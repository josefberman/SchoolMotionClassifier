"""Random search to match sim order-parameter stats to real calibration targets."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.labels import BEHAVIOR_SHORT, CANONICAL, canonicalize
from src.sim.config import CONFIG_DIR
from src.tune.calibration import (
    behavior_calibration_loss,
    load_calibration_targets,
    score_from_loss,
    summarize_behavior_sims,
    total_calibration_loss,
)
from src.tune.search_space import SEARCH_SPACE, round_overrides, sample_overrides


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


def _yaml_center(behavior: str) -> dict:
    """Extract search-space keys from the current behavior YAML."""
    short = BEHAVIOR_SHORT[behavior]
    path = CONFIG_DIR / f"{short}.yaml"
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    def _pick(space: dict, cfg_node: dict) -> dict:
        out: dict = {}
        for key, spec in space.items():
            if key not in cfg_node:
                continue
            if isinstance(spec, dict) and isinstance(cfg_node[key], dict):
                sub = _pick(spec, cfg_node[key])
                if sub:
                    out[key] = sub
            else:
                out[key] = cfg_node[key]
        return out

    return _pick(SEARCH_SPACE.get(behavior, {}), cfg)


def tune_behavior(
    behavior: str,
    target_report: dict[str, dict],
    *,
    n_trials: int = 30,
    n_seeds: int = 16,
    n_values: list[int] | None = None,
    n_jobs: int = -1,
    jitter: float = 0.35,
    rng: np.random.Generator | None = None,
    show_progress: bool = True,
) -> dict[str, Any]:
    """Optimize overrides for a single behavior against real feature targets."""
    if behavior not in target_report:
        raise ValueError(f"No target stats for {behavior}")

    n_values = n_values or [20, 40]
    rng = rng or np.random.default_rng()
    target_block = target_report[behavior]

    best_loss = float("inf")
    best_overrides: dict = {}
    center = _yaml_center(behavior)
    trials: list[dict[str, Any]] = []

    for trial_idx in range(n_trials):
        use_jitter = jitter if center else 0.0
        center_dict = {behavior: center} if center else None
        overrides = sample_overrides(
            rng,
            behaviors=[behavior],
            center=center_dict,
            jitter=use_jitter,
        )
        ov = overrides.get(behavior, {})
        sim_report = summarize_behavior_sims(
            behavior,
            ov,
            n_values=n_values,
            n_seeds=n_seeds,
            n_jobs=n_jobs,
        )
        loss = behavior_calibration_loss(sim_report[behavior], target_block)
        score = score_from_loss(loss)
        record = {
            "behavior": behavior,
            "trial": trial_idx + 1,
            "loss": loss,
            "score": score,
            "n_segments": sim_report[behavior]["n_segments"],
            "overrides": round_overrides({behavior: ov})[behavior],
            "sim_features": sim_report[behavior]["features"],
        }
        trials.append(record)

        if show_progress:
            sf = sim_report[behavior]["features"]
            print(
                f"  trial {trial_idx + 1:3d}/{n_trials}  loss={loss:.4f}  "
                f"phi_trans={sf['phi_trans_mean']['mean']:.3f}  "
                f"psi_tan={sf['psi_tan_mean']['mean']:.3f}  "
                f"psi_rad={sf['psi_rad_pm_mean']['mean']:+.3f}"
            )

        if loss < best_loss:
            best_loss = loss
            best_overrides = ov
            center = ov
            if show_progress:
                print(f"    new best (loss={best_loss:.4f})")

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
    n_trials: int = 30,
    n_seeds: int = 16,
    n_values: list[int] | None = None,
    n_jobs: int = -1,
    jitter: float = 0.35,
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
            jitter=jitter,
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
