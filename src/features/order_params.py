"""Six school order parameters used for validation and classification."""

from __future__ import annotations

import numpy as np

FEATURE_NAMES = (
    "phi_dir",
    "l_bar",
    "phi_rot",
    "phi_tan",
    "v_r_bar",
    "sigma_d",
)


def compute_order_params(
    positions: np.ndarray,
    velocities: np.ndarray,
) -> dict[str, float]:
    """positions, velocities: (N, 2)"""
    series = compute_order_params_series(positions[None, ...], velocities[None, ...])
    return {k: float(v[0]) for k, v in series.items()}


def compute_order_params_series(
    positions: np.ndarray,
    velocities: np.ndarray,
) -> dict[str, np.ndarray]:
    """Vectorized over time. positions, velocities: (T, N, 2)."""
    pos = np.asarray(positions, dtype=np.float64)
    vel = np.asarray(velocities, dtype=np.float64)
    if pos.ndim == 2:
        pos = pos[None, ...]
        vel = vel[None, ...]
    t, n, _ = pos.shape
    if n == 0:
        z = np.zeros(t)
        return {k: z.copy() for k in FEATURE_NAMES}

    speeds = np.linalg.norm(vel, axis=-1)
    hat_v = np.zeros_like(vel)
    moving = speeds > 1e-9
    hat_v[moving] = vel[moving] / speeds[moving, None]

    mean_dir = hat_v.mean(axis=1)
    phi_dir = np.linalg.norm(mean_dir, axis=-1)

    centroid = pos.mean(axis=1, keepdims=True)
    r = pos - centroid
    r_norm = np.linalg.norm(r, axis=-1)
    mean_r = np.mean(r_norm, axis=1) + 1e-12
    L = r[..., 0] * vel[..., 1] - r[..., 1] * vel[..., 0]
    l_bar = np.mean(L, axis=1) / mean_r

    sum_abs_L = np.sum(np.abs(L), axis=1) + 1e-12
    phi_rot = np.abs(np.sum(L, axis=1)) / sum_abs_L

    safe = r_norm > 1e-9
    t_hat = np.zeros_like(r)
    r_hat = np.zeros_like(r)
    t_hat[..., 0] = np.where(safe, -r[..., 1] / np.maximum(r_norm, 1e-12), 0.0)
    t_hat[..., 1] = np.where(safe, r[..., 0] / np.maximum(r_norm, 1e-12), 0.0)
    r_hat[..., 0] = np.where(safe, r[..., 0] / np.maximum(r_norm, 1e-12), 0.0)
    r_hat[..., 1] = np.where(safe, r[..., 1] / np.maximum(r_norm, 1e-12), 0.0)

    cos_phi = np.sum(hat_v * t_hat, axis=-1)
    phi_tan = np.mean(np.abs(cos_phi), axis=1)

    cos_psi = np.sum(hat_v * r_hat, axis=-1)
    v_r_bar = np.mean(cos_psi, axis=1)

    sigma_d = np.std(r_norm, axis=1) if n > 1 else np.zeros(t)

    return {
        "phi_dir": phi_dir,
        "l_bar": l_bar,
        "phi_rot": phi_rot,
        "phi_tan": phi_tan,
        "v_r_bar": v_r_bar,
        "sigma_d": sigma_d,
    }


def aggregate_series(
    series: dict[str, np.ndarray],
    fps: float = 30.0,
) -> dict[str, float]:
    feat: dict[str, float] = {}
    for k, arr in series.items():
        feat[f"{k}_mean"] = float(np.mean(arr))
        feat[f"{k}_std"] = float(np.std(arr))
    if len(series["sigma_d"]) >= 2:
        t = np.arange(len(series["sigma_d"]), dtype=np.float64) / fps
        feat["sigma_d_slope"] = float(np.polyfit(t, series["sigma_d"], 1)[0])
        feat["v_r_bar_slope"] = float(np.polyfit(t, series["v_r_bar"], 1)[0])
    else:
        feat["sigma_d_slope"] = 0.0
        feat["v_r_bar_slope"] = 0.0
    feat["l_bar_abs_mean"] = float(np.mean(np.abs(series["l_bar"])))
    return feat


AGG_FEATURE_NAMES = [
    f"{k}_{s}" for k in FEATURE_NAMES for s in ("mean", "std")
] + ["sigma_d_slope", "v_r_bar_slope", "l_bar_abs_mean"]
