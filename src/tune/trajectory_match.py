"""Tune behavior YAMLs so simulations reproduce configs extracted from real tracks.

1. Extraction: each 15-frame window of an annotation interval becomes one row of
   annotated_config.csv.
   The fit is the simulator's own update: heading and speed changes are a
   clipped normal (Tobit) of the zone torques and of (s_0 - speed). The clip
   levels are omega_max and a_max, so the fitted numbers are YAML parameters.
   r_r, r_o, r_a are the ordered triple inside r_r 10-80, r_o 40-250, r_a 80-500
   with the best heading likelihood. Any value inside those limits is allowed.
2. Tuning: radii stay at the per-behavior mean of the extracted triples. CMA-ES
   searches the other SEARCH_SPACE parameters so simulated estimates match the
   real means and stds (Huber loss) measured at those same radii.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy.optimize import minimize
from scipy.stats import norm

from src.features.dataset import load_real_segments
from src.labels import BEHAVIOR_SHORT, CANONICAL, canonicalize
from src.sim.config import CONFIG_DIR, DEFAULTS, deep_merge, load_behavior_config, validate_radii
from src.sim.io import load_trajectory_csv
from src.sim.model import _wrap
from src.sim.model_fast import FastSchoolSimulator
from src.tune.search_space import SEARCH_PARAM_NAMES, SEARCH_SPACE, round_overrides

ROOT = Path(__file__).resolve().parents[2]
TUNING_DIR = ROOT / "results" / "tuning" / "trajectory_match"
BEST_PATH = TUNING_DIR / "best.json"
HISTORY_PATH = TUNING_DIR / "history.jsonl"
ANNOTATED_CONFIG_PATH = ROOT / "annotated_config.csv"

ID_COLUMNS = ("dataset", "start_frame", "end_frame", "fps", "label")
MIN_STEPS = 10
SPEED_EPS = 1e-3
_FIT_ROWS = 30000
# 15 frames at 29.97 fps is 0.5 s. Non-overlapping; a short tail is dropped.
EXTRACT_WINDOW_FRAMES = 15
_WEIGHTS = ("w_r", "w_o", "w_a", "w_tan", "w_rad")
RADIUS_COLUMNS = ("r_r", "r_o", "r_a")
# Continuous search box. Every ordered triple inside it is a legal zone.
_R_R = (10.0, 80.0)
_R_O = (40.0, 250.0)
_R_A = (80.0, 500.0)
_RADIUS_GAP = 1.0
_RADIUS_SEARCH_FRAMES = 120


def _dataset_id(dataset: str) -> int | str:
    text = str(dataset)
    return int(text) if text.isdigit() else text


def _torque_calculator(radii: dict[str, float]) -> FastSchoolSimulator:
    cfg = load_behavior_config("tpol")
    cfg.update(radii)
    validate_radii(cfg)
    return FastSchoolSimulator(n=2, cfg=cfg, seed=0)


def _design_row(
    sim: FastSchoolSimulator, pos: np.ndarray, theta: np.ndarray, c_mill: float
) -> tuple[np.ndarray, np.ndarray]:
    sim.n = int(pos.shape[0])
    sim.pos = np.ascontiguousarray(pos, dtype=np.float64)
    sim.theta = np.ascontiguousarray(theta, dtype=np.float64)
    sim.c_mill = float(c_mill)
    t_r, t_o, t_a = sim._social()
    t_tan, t_rad = sim._centroid_steering()
    return np.column_stack([t_r, t_o, t_a, t_tan, t_rad]), sim._wall()


def _circulation_sign(pos: np.ndarray, theta: np.ndarray, valid: np.ndarray) -> float:
    acc = 0.0
    for t in range(pos.shape[0]):
        m = valid[t]
        if int(m.sum()) < 2:
            continue
        rel = pos[t, m] - pos[t, m].mean(axis=0)
        th = theta[t, m]
        acc += float(np.sum(rel[:, 0] * np.sin(th) - rel[:, 1] * np.cos(th)))
    if abs(acc) < 1e-8:
        return 1.0
    return 1.0 if acc > 0.0 else -1.0


def _clip_level(values: np.ndarray) -> float:
    """Clip bound. Saturated sims pile up at the bound, so the 99th percentile is that bound."""
    magnitude = np.abs(values)
    if magnitude.size < 20:
        return float(np.max(magnitude)) if magnitude.size else 0.0
    return float(np.percentile(magnitude, 99))


def _subsample(n: int) -> np.ndarray:
    if n <= _FIT_ROWS:
        return np.arange(n)
    return np.random.default_rng(0).choice(n, _FIT_ROWS, replace=False)


def _tobit_nll(y: np.ndarray, mu: np.ndarray, sigma: float, bound: float) -> float:
    """Negative log-likelihood of y = clip(mu + sigma * ε, ±bound)."""
    sigma = max(float(sigma), 1e-6)
    interior = np.abs(y) < bound
    upper = y >= bound
    lower = ~interior & ~upper
    val = np.empty(y.shape[0])
    if np.any(interior):
        z = (y[interior] - mu[interior]) / sigma
        val[interior] = 0.5 * z * z + np.log(sigma)
    if np.any(upper):
        z = np.clip((bound - mu[upper]) / sigma, -30.0, 30.0)
        val[upper] = -norm.logsf(z)
    if np.any(lower):
        z = np.clip((-bound - mu[lower]) / sigma, -30.0, 30.0)
        val[lower] = -norm.logcdf(z)
    out = float(np.mean(val))
    return out if np.isfinite(out) else 1e6


def _fit_heading(design: np.ndarray, wall: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Tobit fit of Δθ = clip(X w + wall + σ ε, ±omega_max). Returns w, sigma, omega_max."""
    omega = max(_clip_level(observed), 1e-4)
    idx = _subsample(observed.size)
    design, wall, observed = design[idx], wall[idx], observed[idx]
    w0, *_ = np.linalg.lstsq(design, observed - wall, rcond=None)
    w0[:4] = np.maximum(w0[:4], 0.0)
    start = np.concatenate([w0, [np.log(0.05)]])

    def nll(p: np.ndarray) -> float:
        return _tobit_nll(observed, design @ p[:5] + wall, np.exp(p[5]), omega)

    bounds = [(0.0, None)] * 4 + [(None, None), (np.log(1e-4), np.log(5.0))]
    fit = minimize(nll, start, method="L-BFGS-B", bounds=bounds)
    w = fit.x[:5] if fit.success else w0
    sigma = float(np.exp(fit.x[5]) if fit.success else 0.05)
    return w, sigma, omega


def _fit_speed(speed: np.ndarray, delta: np.ndarray) -> tuple[float, float, float]:
    """Tobit fit of Δs = clip(s_0 - speed + σ ε, ±a_max). Returns s_0, sigma, a_max."""
    a_max = max(_clip_level(delta), 1e-4)
    idx = _subsample(speed.size)
    speed, delta = speed[idx], delta[idx]
    s0_0 = float(np.median(speed + delta))

    def nll(p: np.ndarray) -> float:
        return _tobit_nll(delta, p[0] - speed, np.exp(p[1]), a_max)

    fit = minimize(nll, [s0_0, np.log(0.05)], method="L-BFGS-B", bounds=[(0.0, None), (np.log(1e-4), np.log(5.0))])
    if not fit.success:
        return s0_0, 0.05, a_max
    return float(fit.x[0]), float(np.exp(fit.x[1])), a_max


def _step_frames(
    pos: np.ndarray,
    vel: np.ndarray,
    *,
    max_frames: int | None = None,
) -> tuple[list[tuple[np.ndarray, np.ndarray, np.ndarray]], float] | None:
    """Per-step (positions, headings, Δθ) for fish that move at both ends of the step."""
    if pos.shape[0] < 2 or pos.shape[1] < 2:
        return None
    speed = np.linalg.norm(vel, axis=-1)
    theta = np.arctan2(vel[..., 1], vel[..., 0])
    valid = np.isfinite(pos).all(axis=-1) & np.isfinite(vel).all(axis=-1) & (speed > SPEED_EPS)
    c_mill = _circulation_sign(pos, theta, valid)
    n_steps = pos.shape[0] - 1
    stride = 1 if max_frames is None else max(1, int(np.ceil(n_steps / max_frames)))
    frames: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    for t in range(0, n_steps, stride):
        m = valid[t] & valid[t + 1]
        if int(m.sum()) < 2:
            continue
        frames.append((pos[t, m], theta[t, m], np.asarray(_wrap(theta[t + 1, m] - theta[t, m]), dtype=np.float64)))
    if not frames:
        return None
    return frames, c_mill


def _zone_mean(err: np.ndarray, mask: np.ndarray) -> np.ndarray:
    count = mask.sum(axis=1)
    out = np.zeros(err.shape[0], dtype=np.float64)
    np.divide(np.where(mask, err, 0.0).sum(axis=1), count, out=out, where=count > 0)
    return out


def _radii_from_unit(unit: np.ndarray) -> tuple[float, float, float]:
    """Map [0, 1]^3 onto r_r < r_o < r_a inside the box."""
    u = np.clip(np.asarray(unit, dtype=np.float64), 0.0, 1.0)
    r_r = _R_R[0] + u[0] * (_R_R[1] - _R_R[0])
    r_o_lo = max(r_r + _RADIUS_GAP, _R_O[0])
    r_o_hi = _R_O[1]
    r_o = r_o_lo if r_o_lo >= r_o_hi else r_o_lo + u[1] * (r_o_hi - r_o_lo)
    r_a_lo = max(r_o + _RADIUS_GAP, _R_A[0])
    r_a_hi = _R_A[1]
    r_a = r_a_lo if r_a_lo >= r_a_hi else r_a_lo + u[2] * (r_a_hi - r_a_lo)
    return float(r_r), float(r_o), float(r_a)


def _frame_geometry(
    sim: FastSchoolSimulator,
    frames: list[tuple[np.ndarray, np.ndarray, np.ndarray]],
    c_mill: float,
) -> list[tuple]:
    """Neighbor geometry and the radius-independent torques, once per step."""
    geoms = []
    for pos_t, theta_t, delta_t in frames:
        sim.n = int(pos_t.shape[0])
        sim.pos = np.ascontiguousarray(pos_t, dtype=np.float64)
        sim.theta = np.ascontiguousarray(theta_t, dtype=np.float64)
        sim.c_mill = float(c_mill)
        dvec = sim.pos[None, :, :] - sim.pos[:, None, :]
        dist = np.hypot(dvec[:, :, 0], dvec[:, :, 1])
        np.fill_diagonal(dist, np.inf)
        theta = sim.theta
        err_r = np.asarray(_wrap(np.arctan2(-dvec[:, :, 1], -dvec[:, :, 0]) - theta[:, None]), dtype=np.float64)
        err_o = np.asarray(_wrap(theta[None, :] - theta[:, None]), dtype=np.float64)
        err_a = np.asarray(_wrap(np.arctan2(dvec[:, :, 1], dvec[:, :, 0]) - theta[:, None]), dtype=np.float64)
        t_tan, t_rad = sim._centroid_steering()
        geoms.append((dist, err_r, err_o, err_a, t_tan, t_rad, sim._wall(), delta_t))
    return geoms


def _heading_nll_radii(geoms: list[tuple], radii: tuple[float, float, float], omega: float) -> float:
    """Tobit loss at the nonnegative least-squares weights for this zone triple.

    The stored weights are the full Tobit fit at the chosen radii. This score only
    ranks triples, and on real windows the clip barely binds, so the two agree.
    """
    r_r, r_o, r_a = radii
    blocks_x: list[np.ndarray] = []
    blocks_wall: list[np.ndarray] = []
    blocks_y: list[np.ndarray] = []
    for dist, err_r, err_o, err_a, t_tan, t_rad, wall, delta in geoms:
        mask_r = dist < r_r
        mask_o = (dist >= r_r) & (dist < r_o)
        mask_a = (dist >= r_o) & (dist < r_a)
        blocks_x.append(
            np.column_stack(
                [_zone_mean(err_r, mask_r), _zone_mean(err_o, mask_o), _zone_mean(err_a, mask_a), t_tan, t_rad]
            )
        )
        blocks_wall.append(wall)
        blocks_y.append(delta)
    design = np.vstack(blocks_x)
    wall = np.concatenate(blocks_wall)
    observed = np.concatenate(blocks_y)
    if observed.size < MIN_STEPS or not np.isfinite(design).all() or not np.isfinite(wall).all():
        return 1e6
    weights, *_ = np.linalg.lstsq(design, observed - wall, rcond=None)
    weights = np.asarray(weights, dtype=np.float64).copy()
    weights[:4] = np.maximum(weights[:4], 0.0)
    mu = design @ weights + wall
    sigma = max(float(np.std(observed - mu)), 1e-4)
    return _tobit_nll(observed, mu, sigma, omega)


def fit_radii(pos: np.ndarray, vel: np.ndarray) -> dict[str, float] | None:
    """Zone radii inside the box with the best heading likelihood.

    Any ordered triple with r_r in [10, 80], r_o in [40, 250], r_a in [80, 500]
    is allowed. Differential evolution searches that box.
    """
    from scipy.optimize import differential_evolution

    packed = _step_frames(pos, vel, max_frames=_RADIUS_SEARCH_FRAMES)
    if packed is None:
        return None
    frames, c_mill = packed
    sim = _torque_calculator({"r_r": 50.0, "r_o": 100.0, "r_a": 150.0})
    geoms = _frame_geometry(sim, frames, c_mill)
    if not geoms:
        return None
    observed = np.concatenate([g[-1] for g in geoms])
    omega = max(_clip_level(observed), 1e-4)

    def objective(unit: np.ndarray) -> float:
        return _heading_nll_radii(geoms, _radii_from_unit(unit), omega)

    fit = differential_evolution(
        objective,
        bounds=[(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)],
        seed=0,
        popsize=4,
        maxiter=12,
        mutation=0.5,
        recombination=0.7,
        atol=0.0,
        tol=1e-3,
        polish=False,
        workers=1,
        updating="immediate",
    )
    radii = _radii_from_unit(fit.x)
    if not np.isfinite(fit.fun) or fit.fun >= 1e6:
        return None
    return {"r_r": radii[0], "r_o": radii[1], "r_a": radii[2]}


def estimate_interval(
    pos: np.ndarray,
    vel: np.ndarray,
    behavior: str,
    *,
    sim: FastSchoolSimulator,
) -> dict[str, float] | None:
    """Clipped-update config for one (T, N, 2) trajectory slice. Values match the YAML."""
    if behavior not in SEARCH_SPACE or pos.shape[0] < 2 or pos.shape[1] < 2:
        return None

    speed = np.linalg.norm(vel, axis=-1)
    theta = np.arctan2(vel[..., 1], vel[..., 0])
    finite = np.isfinite(pos).all(axis=-1) & np.isfinite(vel).all(axis=-1)
    moving = speed > SPEED_EPS
    valid = finite & moving
    c_mill = _circulation_sign(pos, theta, valid)

    blocks_x: list[np.ndarray] = []
    blocks_wall: list[np.ndarray] = []
    blocks_y: list[np.ndarray] = []
    speed_now: list[np.ndarray] = []
    speed_step: list[np.ndarray] = []
    for t in range(pos.shape[0] - 1):
        m = valid[t] & valid[t + 1]
        if int(m.sum()) < 2:
            continue
        design_t, wall_t = _design_row(sim, pos[t, m], theta[t, m], c_mill)
        blocks_x.append(design_t)
        blocks_wall.append(wall_t)
        blocks_y.append(np.asarray(_wrap(theta[t + 1, m] - theta[t, m]), dtype=np.float64))
        speed_now.append(speed[t, m])
        speed_step.append(speed[t + 1, m] - speed[t, m])
    if not blocks_y:
        return None
    design = np.vstack(blocks_x)
    wall = np.concatenate(blocks_wall)
    observed = np.concatenate(blocks_y)
    if observed.size < MIN_STEPS or not np.isfinite(design).all() or not np.isfinite(wall).all():
        return None

    weights_v, sigma_theta, omega_max = _fit_heading(design, wall, observed)
    if not np.isfinite(weights_v).all():
        return None
    s_0, sigma_s, a_max = _fit_speed(np.concatenate(speed_now), np.concatenate(speed_step))
    return {
        **{name: float(val) for name, val in zip(_WEIGHTS, weights_v)},
        "sigma_theta": sigma_theta,
        "s_0": s_0,
        "sigma_s": sigma_s,
        "omega_max": omega_max,
        "a_max": a_max,
    }


def build_annotated_config(
    *,
    radii: dict[str, float] | None = None,
    behaviors: list[str] | None = None,
) -> pd.DataFrame:
    """One row per non-overlapping 15-frame window inside each canonical interval."""
    del radii
    allowed = set(behaviors or CANONICAL)
    sim = _torque_calculator({"r_r": 50.0, "r_o": 100.0, "r_a": 150.0})
    segments = [s for s in load_real_segments() if s["label"] in allowed]

    by_csv: dict[str, list[dict]] = {}
    for seg in segments:
        by_csv.setdefault(seg["csv"], []).append(seg)

    rows: list[dict[str, Any]] = []
    for csv_rel, group in by_csv.items():
        pos, vel = load_trajectory_csv(ROOT / csv_rel)
        dataset = group[0]["dataset"]
        print(f"{dataset}: {len(group)} intervals, {pos.shape[1]} fish")
        n_windows = 0
        for seg in group:
            a = int(seg["start"])
            b = min(int(seg["end"]), pos.shape[0])
            for start in range(a, b - EXTRACT_WINDOW_FRAMES + 1, EXTRACT_WINDOW_FRAMES):
                end = start + EXTRACT_WINDOW_FRAMES
                fitted = fit_radii(pos[start:end], vel[start:end])
                if fitted is None:
                    continue
                sim.cfg["r_r"], sim.cfg["r_o"], sim.cfg["r_a"] = fitted["r_r"], fitted["r_o"], fitted["r_a"]
                estimate = estimate_interval(pos[start:end], vel[start:end], seg["label"], sim=sim)
                if estimate is None:
                    continue
                estimate.update(fitted)
                n_windows += 1
                rows.append(
                    {
                        "dataset": _dataset_id(dataset),
                        "start_frame": start,
                        "end_frame": end,
                        "fps": float(seg["fps"]),
                        "label": seg["label"],
                        **estimate,
                    }
                )
        print(f"  {n_windows} windows of {EXTRACT_WINDOW_FRAMES} frames")
    columns = list(ID_COLUMNS) + list(SEARCH_PARAM_NAMES) + list(RADIUS_COLUMNS)
    frame = pd.DataFrame(rows, columns=columns)
    if not frame.empty:
        frame = frame.sort_values(["dataset", "start_frame", "end_frame"]).reset_index(drop=True)
    return frame


def save_annotated_config(frame: pd.DataFrame, path: Path | None = None) -> Path:
    path = path or ANNOTATED_CONFIG_PATH
    frame.to_csv(path, index=False)
    return path


def load_annotated_config(path: Path | None = None) -> pd.DataFrame:
    path = path or ANNOTATED_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run: python scripts/tune_trajectories.py --extract")
    return pd.read_csv(path, dtype={"dataset": str})


def load_behavior_clips(behavior: str, max_clips: int | None = None) -> list[tuple[np.ndarray, np.ndarray]]:
    """Position and velocity slices for one behavior."""
    segments = [s for s in load_real_segments() if s["label"] == behavior]
    if max_clips is not None and len(segments) > max_clips:
        pick = np.linspace(0, len(segments) - 1, max_clips).astype(int)
        segments = [segments[i] for i in pick]
    by_csv: dict[str, list[dict]] = {}
    for seg in segments:
        by_csv.setdefault(seg["csv"], []).append(seg)
    clips: list[tuple[np.ndarray, np.ndarray]] = []
    for csv_rel, group in by_csv.items():
        pos, vel = load_trajectory_csv(ROOT / csv_rel)
        for seg in group:
            a = int(seg["start"])
            b = min(int(seg["end"]), pos.shape[0])
            if b - a >= 2:
                clips.append((pos[a:b], vel[a:b]))
    return clips


def real_target_stats(
    clips: list[tuple[np.ndarray, np.ndarray]],
    behavior: str,
    radii: dict[str, float],
) -> dict[str, dict[str, float]] | None:
    """Mean and std of the extractor on real clips, using this trial's radii."""
    sim = _torque_calculator(radii)
    rows = []
    for pos, vel in clips:
        est = estimate_interval(pos, vel, behavior, sim=sim)
        if est is not None:
            rows.append(est)
    if not rows:
        return None
    stats: dict[str, dict[str, float]] = {}
    for name in SEARCH_PARAM_NAMES:
        col = np.array([row[name] for row in rows], dtype=np.float64)
        stats[name] = {"mean": float(np.mean(col)), "std": float(max(np.std(col), 1e-6))}
    return stats


def behavior_radii(frame: pd.DataFrame) -> dict[str, dict[str, float]]:
    """One zone triple per behavior: the mean of the triples chosen at extraction."""
    missing = [name for name in RADIUS_COLUMNS if name not in frame.columns]
    if missing:
        raise ValueError(
            "annotated_config.csv has no extracted radii. Run: python scripts/tune_trajectories.py --extract"
        )
    out: dict[str, dict[str, float]] = {}
    for label, block in frame.groupby("label"):
        try:
            behavior = canonicalize(str(label))
        except ValueError:
            continue
        if behavior not in SEARCH_SPACE:
            continue
        radii = {name: float(block[name].mean()) for name in RADIUS_COLUMNS}
        validate_radii(radii)
        out[behavior] = radii
    return out


def target_stats(frame: pd.DataFrame) -> dict[str, dict[str, dict[str, float]]]:
    """Per-behavior mean and std across intervals of every extracted parameter."""
    out: dict[str, dict[str, dict[str, float]]] = {}
    for label, block in frame.groupby("label"):
        try:
            behavior = canonicalize(str(label))
        except ValueError:
            continue
        if behavior not in SEARCH_SPACE:
            continue
        stats: dict[str, dict[str, float]] = {}
        for name in SEARCH_PARAM_NAMES:
            col = block[name].to_numpy(dtype=np.float64)
            stats[name] = {"mean": float(np.mean(col)), "std": float(max(np.std(col), 1e-6))}
        out[behavior] = stats
    return out


def _estimate_sim(behavior: str, n: int, seed: int, overrides: dict, radii: dict[str, float]) -> dict[str, float] | None:
    """Run the extraction estimator on one simulated clip of a candidate config."""
    from src.sim.model_fast import run_simulation_fast

    try:
        result = run_simulation_fast(behavior, n, seed + n * 10007, overrides=overrides)
        sim = _torque_calculator(radii)
        return estimate_interval(result.positions, result.velocities, behavior, sim=sim)
    except Exception:
        return None


def simulated_estimates(
    behavior: str,
    overrides: dict[str, float],
    *,
    n_values: list[int],
    n_seeds: int,
    radii: dict[str, float],
    n_jobs: int = -1,
) -> dict[str, dict[str, float]] | None:
    """Mean and std of the extracted parameters over simulated clips."""
    from joblib import Parallel, delayed

    tasks = [(n, s) for n in n_values for s in range(n_seeds)]
    rows = Parallel(n_jobs=n_jobs)(delayed(_estimate_sim)(behavior, n, s, overrides, radii) for n, s in tasks)
    rows = [r for r in rows if r is not None]
    if not rows:
        return None
    return {
        "mean": {name: float(np.mean([r[name] for r in rows])) for name in SEARCH_PARAM_NAMES},
        "std": {name: float(np.std([r[name] for r in rows])) for name in SEARCH_PARAM_NAMES},
    }


HUBER_DELTA = 3.0


def _huber(z: np.ndarray) -> np.ndarray:
    z = np.abs(z)
    return np.where(z <= HUBER_DELTA, z**2, 2.0 * HUBER_DELTA * z - HUBER_DELTA**2)


def trajectory_loss(
    sim: dict[str, dict[str, float]] | None,
    target: dict[str, dict[str, float]],
) -> float:
    """Mean Huber loss over mean and std of every parameter.

    Mean term: (sim mean - real mean) / real std.
    Std term:  (sim std - real std) / real std, a relative error.
    Quadratic within HUBER_DELTA, linear beyond, so a parameter that is far from its
    target keeps a gradient instead of saturating.
    """
    if sim is None:
        return float("inf")
    z_mean = [(sim["mean"][n] - target[n]["mean"]) / target[n]["std"] for n in SEARCH_PARAM_NAMES]
    z_std = [(sim["std"][n] - target[n]["std"]) / target[n]["std"] for n in SEARCH_PARAM_NAMES]
    return float(np.mean(_huber(np.array(z_mean + z_std))))


def tune_behavior(
    behavior: str,
    target: dict[str, dict[str, float]],
    *,
    radii: dict[str, float],
    n_trials: int,
    n_seeds: int,
    n_values: list[int],
    n_jobs: int = -1,
    rng: np.random.Generator | None = None,
) -> dict[str, Any]:
    """CMA-ES over SEARCH_SPACE at radii already chosen during extraction."""
    import cma

    from src.tune.search_space import box_center_unit, param_bounds, unit_to_overrides

    rng = rng or np.random.default_rng()
    dim = len(param_bounds(behavior))
    popsize = max(4, min(4 + int(3 * np.log(max(dim, 2))), n_trials))
    best: dict[str, Any] = {"loss": float("inf"), "overrides": {}, "estimate": None}
    count = 0

    def _evaluate(x) -> float:
        nonlocal count
        count += 1
        ov = unit_to_overrides(behavior, x)
        ov.update(radii)
        est = simulated_estimates(behavior, ov, n_values=n_values, n_seeds=n_seeds, radii=radii, n_jobs=n_jobs)
        loss = trajectory_loss(est, target)
        flag = ""
        if loss < best["loss"]:
            best.update(loss=loss, overrides=ov, estimate=est)
            flag = "  *"
        print(f"  trial {count:4d}/{n_trials}  loss={loss:.4f}{flag}", flush=True)
        return loss if np.isfinite(loss) else 1e6

    es = cma.CMAEvolutionStrategy(
        box_center_unit(behavior),
        0.3,
        {
            "bounds": [0.0, 1.0],
            "maxfevals": n_trials,
            "popsize": popsize,
            "seed": int(rng.integers(0, 2**31 - 1)),
            "verbose": -9,
        },
    )
    while not es.stop() and count < n_trials:
        xs = es.ask()
        remaining = n_trials - count
        if remaining < len(xs):
            for x in xs[:remaining]:
                _evaluate(x)
            break
        es.tell(xs, [_evaluate(x) for x in xs])

    return {
        "behavior": behavior,
        "best_loss": best["loss"],
        "best_overrides": round_overrides({behavior: best["overrides"]})[behavior],
        "sim_estimate": best["estimate"],
    }


def tune_all_behaviors(
    frame: pd.DataFrame,
    *,
    behaviors: list[str] | None = None,
    n_trials: int = 100,
    n_seeds: int = 6,
    n_values: list[int] | None = None,
    n_jobs: int = -1,
) -> dict[str, Any]:
    """Tune every behavior at the mean extracted radii. Radii are not search variables."""
    n_values = n_values or [10, 30, 70]
    locked = behavior_radii(frame)
    behaviors = behaviors or [b for b in CANONICAL if b in locked]
    rng = np.random.default_rng()

    overrides: dict[str, dict[str, float]] = {}
    per_behavior: dict[str, Any] = {}
    if BEST_PATH.exists():
        with open(BEST_PATH, encoding="utf-8") as f:
            prev = json.load(f)
        overrides.update(prev.get("behavior_overrides") or {})
        per_behavior.update(prev.get("per_behavior") or {})

    for behavior in behaviors:
        radii = locked[behavior]
        clips = load_behavior_clips(behavior)
        print(f"=== {behavior} ===")
        print(
            f"  radii fixed from extraction: "
            f"r_r={radii['r_r']:.1f} r_o={radii['r_o']:.1f} r_a={radii['r_a']:.1f} "
            f"({len(clips)} intervals)"
        )
        target = real_target_stats(clips, behavior, radii)
        if target is None:
            raise RuntimeError(f"No real estimates for {behavior} at the extracted radii")
        res = tune_behavior(
            behavior,
            target,
            radii=radii,
            n_trials=n_trials,
            n_seeds=n_seeds,
            n_values=n_values,
            n_jobs=n_jobs,
            rng=rng,
        )
        overrides[behavior] = res["best_overrides"]
        per_behavior[behavior] = {
            "best_loss": res["best_loss"],
            "sim_estimate": round_overrides({behavior: res["sim_estimate"] or {}})[behavior],
            "target_mean": {n: round(v["mean"], 6) for n, v in target.items()},
            "target_std": {n: round(v["std"], 6) for n, v in target.items()},
        }

    summary = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "source": "annotated_config.csv",
        "n_trials_per_behavior": n_trials,
        "n_seeds": n_seeds,
        "n_values": n_values,
        "behavior_overrides": round_overrides(overrides),
        "per_behavior": per_behavior,
    }
    save_best(summary)
    return summary


def save_best(record: dict[str, Any]) -> Path:
    TUNING_DIR.mkdir(parents=True, exist_ok=True)
    with open(BEST_PATH, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
        f.write("\n")
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({k: record[k] for k in ("started_at", "behavior_overrides")}) + "\n")
    return BEST_PATH


def apply_best_to_yaml(
    best_path: Path | None = None,
    *,
    dry_run: bool = False,
    r_r: float = float(DEFAULTS["r_r"]),
    r_o: float = float(DEFAULTS["r_o"]),
    r_a: float = float(DEFAULTS["r_a"]),
) -> list[str]:
    """Merge tuned overrides into configs/behaviors/*.yaml.

    r_r, r_o, r_a come from the best record (the extraction means). The function
    arguments fill radii only when that record does not contain them.
    """
    best_path = best_path or BEST_PATH
    fallback = {"r_r": float(r_r), "r_o": float(r_o), "r_a": float(r_a)}
    with open(best_path, encoding="utf-8") as f:
        best = json.load(f)
    updated = []
    for behavior, ov in (best.get("behavior_overrides") or {}).items():
        try:
            behavior = canonicalize(behavior)
        except ValueError:
            continue
        short = BEHAVIOR_SHORT.get(behavior)
        if not short:
            continue
        path = CONFIG_DIR / f"{short}.yaml"
        with open(path, encoding="utf-8") as f:
            current = yaml.safe_load(f) or {}
        radii = {k: float(ov[k]) if k in ov else fallback[k] for k in ("r_r", "r_o", "r_a")}
        validate_radii(radii)
        merged = deep_merge(current, ov)
        merged.update(radii)
        updated.append(str(path))
        if not dry_run:
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(merged, f, sort_keys=False, default_flow_style=False)
    return updated
