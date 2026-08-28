"""Bayesian optimization to match sim order-parameter stats to real calibration targets."""

from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from scipy.optimize import differential_evolution
from scipy.stats import norm
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

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
from src.tune.search_space import SEARCH_SPACE, round_overrides


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


def _param_bounds(behavior: str) -> tuple[list[str], np.ndarray]:
    space = SEARCH_SPACE[behavior]
    keys = list(space.keys())
    bounds = np.array([space[k] for k in keys], dtype=float)
    return keys, bounds


def _clip_to_bounds(x: np.ndarray, bounds: np.ndarray) -> np.ndarray:
    return np.clip(x, bounds[:, 0], bounds[:, 1])


def _center_vector(keys: list[str], bounds: np.ndarray, center: dict) -> np.ndarray:
    x = np.empty(len(keys), dtype=float)
    for i, key in enumerate(keys):
        lo, hi = bounds[i]
        if key in center and isinstance(center[key], (int, float)):
            x[i] = float(center[key])
        else:
            x[i] = 0.5 * (lo + hi)
    return _clip_to_bounds(x, bounds)


def _finite_loss(loss: float) -> float:
    if not np.isfinite(loss):
        return 1e6
    return float(loss)


def _suggest_bayes(Xs: np.ndarray, ys: np.ndarray, bounds: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Next point by maximizing expected improvement on the unit cube."""
    lo, hi = bounds[:, 0], bounds[:, 1]
    span = np.maximum(hi - lo, 1e-12)
    Xu = (Xs - lo) / span
    y_best = float(np.min(ys))
    n_dim = Xs.shape[1]
    kernel = ConstantKernel(1.0, (1e-3, 1e3)) * Matern(
        length_scale=np.ones(n_dim),
        length_scale_bounds=(1e-2, 1e2),
        nu=2.5,
    ) + WhiteKernel(noise_level=0.05, noise_level_bounds=(1e-5, 1.0))
    gp = GaussianProcessRegressor(
        kernel=kernel,
        normalize_y=True,
        optimizer=None if Xs.shape[0] < 3 else "fmin_l_bfgs_b",
        n_restarts_optimizer=0 if Xs.shape[0] < 3 else 2,
        random_state=int(rng.integers(0, 2**31 - 1)),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        try:
            gp.fit(Xu, ys)
        except Exception:
            return rng.uniform(lo, hi)

        unit_bounds = [(0.0, 1.0)] * n_dim
        xi = 0.01

        def neg_ei(u: np.ndarray) -> float:
            mu, sigma = gp.predict(np.asarray(u, dtype=float).reshape(1, -1), return_std=True)
            sigma = max(float(sigma[0]), 1e-9)
            z = (y_best - float(mu[0]) - xi) / sigma
            ei = (y_best - float(mu[0]) - xi) * norm.cdf(z) + sigma * norm.pdf(z)
            return -float(ei)

        seed = int(rng.integers(0, 2**31 - 1))
        try:
            result = differential_evolution(
                neg_ei,
                unit_bounds,
                seed=seed,
                maxiter=40,
                polish=True,
                updating="immediate",
            )
            u = np.clip(result.x, 0.0, 1.0)
            return lo + u * span
        except Exception:
            return rng.uniform(lo, hi)


def tune_behavior(
    behavior: str,
    target_report: dict[str, dict],
    *,
    n_trials: int = 30,
    n_seeds: int = 16,
    n_values: list[int] | None = None,
    n_jobs: int = -1,
    n_initial: int = 10,
    rng: np.random.Generator | None = None,
    show_progress: bool = True,
) -> dict[str, Any]:
    """Optimize overrides for a single behavior against real feature targets."""
    if behavior not in target_report:
        raise ValueError(f"No target stats for {behavior}")

    n_values = n_values or [20, 40]
    rng = rng or np.random.default_rng()
    target_block = target_report[behavior]
    keys, bounds = _param_bounds(behavior)
    n_initial = int(max(0, min(n_initial, max(n_trials - 1, 0))))

    best_loss = float("inf")
    best_overrides: dict = {}
    center = _yaml_center(behavior)
    trials: list[dict[str, Any]] = []
    Xs: list[np.ndarray] = []
    ys: list[float] = []

    for trial_idx in range(n_trials):
        if trial_idx == 0 and center:
            x = _center_vector(keys, bounds, center)
            stage = "init-yaml"
        elif trial_idx <= n_initial:
            x = rng.uniform(bounds[:, 0], bounds[:, 1])
            stage = "init-random"
        else:
            x = _suggest_bayes(np.vstack(Xs), np.asarray(ys), bounds, rng)
            x = _clip_to_bounds(x, bounds)
            stage = "bayes"
        ov = {key: float(val) for key, val in zip(keys, x)}
        sim_report = summarize_behavior_sims(
            behavior,
            ov,
            n_values=n_values,
            n_seeds=n_seeds,
            n_jobs=n_jobs,
        )
        loss = behavior_calibration_loss(sim_report[behavior], target_block)
        score = score_from_loss(loss)
        Xs.append(x)
        ys.append(_finite_loss(loss))
        record = {
            "behavior": behavior,
            "trial": trial_idx + 1,
            "stage": stage,
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
                f"  trial {trial_idx + 1:3d}/{n_trials}  {stage:11s}  loss={loss:.4f}  "
                f"phi_trans={sf['phi_trans_mean']['mean']:.3f}  "
                f"psi_tan={sf['psi_tan_mean']['mean']:.3f}  "
                f"psi_rad={sf['psi_rad_pm_mean']['mean']:+.3f}"
            )

        if loss < best_loss:
            best_loss = loss
            best_overrides = ov
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
    n_initial: int = 10,
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
            n_initial=n_initial,
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
        "n_initial": n_initial,
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
