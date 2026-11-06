"""CMA-ES search to match sim order-parameter stats to real calibration targets."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cma
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.features.order_params import CALIBRATION_FEATURE_NAMES
from src.labels import CANONICAL, canonicalize
from src.tune.calibration import (
    behavior_calibration_loss,
    load_calibration_targets,
    score_from_loss,
    summarize_behavior_sims,
    total_calibration_loss,
)
from src.tune.search_space import (
    box_center_unit,
    param_bounds,
    round_overrides,
    unit_to_overrides,
)


def _feat_progress(sf: dict) -> str:
    parts = []
    for name in CALIBRATION_FEATURE_NAMES:
        if name not in sf:
            continue
        short = name.removeprefix("phi_")
        m = sf[name]["mean"]
        s = sf[name]["std"]
        if name == "phi_rad_pm" or name.endswith("_rate"):
            parts.append(f"{short}={m:+.3f}±{s:.3f}")
        else:
            parts.append(f"{short}={m:.3f}±{s:.3f}")
    return "  ".join(parts)


def _canonical_behavior_map(d: dict[str, Any] | None) -> dict[str, Any]:
    """Remap keys such as swarming → shoaling; drop unknown labels."""
    out: dict[str, Any] = {}
    for key, val in (d or {}).items():
        try:
            canon = canonicalize(str(key))
        except ValueError:
            continue
        if canon not in CANONICAL:
            continue
        out[canon] = val
    return out


TUNING_DIR = ROOT / "results" / "tuning" / "feature_match"
BEST_PATH = TUNING_DIR / "best.json"
HISTORY_PATH = TUNING_DIR / "history.jsonl"


def tune_behavior(
    behavior: str,
    target_report: dict[str, dict],
    *,
    n_trials: int = 500,
    n_seeds: int = 16,
    n_values: list[int] | None = None,
    n_jobs: int = -1,
    rng: np.random.Generator | None = None,
    show_progress: bool = True,
) -> dict[str, Any]:
    """CMA-ES over SEARCH_SPACE for one behavior against real feature targets."""
    if behavior not in target_report:
        raise ValueError(f"No target stats for {behavior}")
    if n_trials <= 0:
        raise ValueError("n_trials must be positive")

    n_values = n_values or [20, 40]
    rng = rng or np.random.default_rng()
    target_block = target_report[behavior]
    dim = len(param_bounds(behavior))
    seed = int(rng.integers(0, 2**31 - 1))
    x0 = box_center_unit(behavior)
    sigma0 = 0.3
    popsize = max(4, min(4 + int(3 * np.log(max(dim, 2))), n_trials))

    trials: list[dict[str, Any]] = []
    best_loss = float("inf")
    best_overrides: dict[str, float] = {}

    def _evaluate(x) -> float:
        nonlocal best_loss, best_overrides
        ov = unit_to_overrides(behavior, x)
        sim_report = summarize_behavior_sims(
            behavior,
            ov,
            n_values=n_values,
            n_seeds=n_seeds,
            n_jobs=n_jobs,
        )
        block = sim_report[behavior]
        loss = behavior_calibration_loss(block, target_block)
        record = {
            "behavior": behavior,
            "trial": len(trials) + 1,
            "loss": float(loss),
            "score": score_from_loss(loss),
            "n_windows": block.get("n_windows", block.get("n_frames", 0)),
            "overrides": round_overrides({behavior: ov})[behavior],
            "sim_features": block["features"],
        }
        trials.append(record)
        if show_progress:
            print(
                f"  trial {record['trial']:4d}/{n_trials}  loss={loss:.4f}  "
                f"{_feat_progress(block['features'])}"
            )
        if loss < best_loss:
            best_loss = float(loss)
            best_overrides = ov
            if show_progress:
                print(f"    new best (loss={best_loss:.4f})")
        return float(loss) if np.isfinite(loss) else 1e6

    if show_progress:
        tuned = [name for name, _, _ in param_bounds(behavior)]
        print(f"  CMA-ES: {n_trials} evaluations in {dim}D  (σ0={sigma0}, λ={popsize})")
        print(f"  search  {', '.join(tuned)}")
        print(
            f"  matching mean+std of {len(CALIBRATION_FEATURE_NAMES)} 5-frame window features: "
            f"{', '.join(CALIBRATION_FEATURE_NAMES)}"
        )
        print(f"  target  {_feat_progress(target_block['features'])}")

    es = cma.CMAEvolutionStrategy(
        x0,
        sigma0,
        {
            "bounds": [0.0, 1.0],
            "maxfevals": n_trials,
            "popsize": popsize,
            "seed": seed,
            "verbose": -9,
        },
    )
    while not es.stop() and len(trials) < n_trials:
        xs = es.ask()
        remaining = n_trials - len(trials)
        if remaining < len(xs):
            for x in xs[:remaining]:
                _evaluate(x)
            break
        losses = [_evaluate(x) for x in xs]
        es.tell(xs, losses)

    return {
        "behavior": behavior,
        "best_loss": best_loss,
        "best_score": score_from_loss(best_loss),
        "best_overrides": round_overrides({behavior: best_overrides})[behavior],
        "target_features": target_block["features"],
        "trials": trials,
    }


def tune_all_behaviors(
    target_path: Path,
    *,
    behaviors: list[str] | None = None,
    n_trials: int = 500,
    n_seeds: int = 16,
    n_values: list[int] | None = None,
    n_jobs: int = -1,
    show_progress: bool = True,
) -> dict[str, Any]:
    """Tune each behavior independently, then merge best overrides."""
    target_report = load_calibration_targets(target_path)
    behaviors = behaviors or [b for b in CANONICAL if b in target_report]
    rng = np.random.default_rng()

    # Merge with any existing best overrides for behaviors we skip.
    merged_overrides: dict[str, dict] = {}
    if BEST_PATH.exists():
        with open(BEST_PATH, encoding="utf-8") as f:
            prev = json.load(f)
        merged_overrides.update(_canonical_behavior_map(prev.get("behavior_overrides")))

    per_behavior: dict[str, Any] = {}

    print(f"Target report: {target_path}")
    print(f"Behaviors: {behaviors}\n")

    for behavior in behaviors:
        print(f"=== {behavior} ===")
        result = tune_behavior(
            behavior,
            target_report,
            n_trials=n_trials,
            n_seeds=n_seeds,
            n_values=n_values,
            n_jobs=n_jobs,
            rng=rng,
            show_progress=show_progress,
        )
        per_behavior[behavior] = result
        merged_overrides[behavior] = result["best_overrides"]
        append_history(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "behavior": behavior,
                "best_loss": result["best_loss"],
                "best_overrides": result["best_overrides"],
            }
        )
        print()

    sim_report: dict[str, dict] = {}
    for behavior, ov in merged_overrides.items():
        if behavior not in target_report:
            continue
        sim_report.update(
            summarize_behavior_sims(
                behavior,
                ov,
                n_values=n_values or [20, 40],
                n_seeds=n_seeds,
                n_jobs=n_jobs,
            )
        )

    prev_per_behavior: dict[str, Any] = {}
    if BEST_PATH.exists():
        with open(BEST_PATH, encoding="utf-8") as f:
            prev = json.load(f)
        prev_per_behavior = _canonical_behavior_map(prev.get("per_behavior"))

    summary = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "target_path": str(target_path),
        "n_trials_per_behavior": n_trials,
        "n_seeds": n_seeds,
        "n_values": n_values or [20, 40],
        "total_loss": total_calibration_loss(
            sim_report,
            target_report,
            behaviors=[b for b in CANONICAL if b in target_report],
        ),
        "behavior_overrides": round_overrides(merged_overrides),
        "per_behavior": {
            **prev_per_behavior,
            **{
                b: {
                    "best_loss": r["best_loss"],
                    "best_overrides": r["best_overrides"],
                }
                for b, r in per_behavior.items()
            },
        },
        "sim_features": {b: sim_report[b]["features"] for b in sim_report},
        "target_features": {b: target_report[b]["features"] for b in target_report if b in CANONICAL},
    }
    save_best(summary)
    return summary


def append_history(record: dict[str, Any]) -> None:
    TUNING_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def save_best(record: dict[str, Any]) -> None:
    TUNING_DIR.mkdir(parents=True, exist_ok=True)
    with open(BEST_PATH, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
        f.write("\n")
