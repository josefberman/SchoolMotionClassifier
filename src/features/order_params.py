"""Three collective order parameters for five-class motion classification."""

from __future__ import annotations

import numpy as np

# Φ_trans, Φ_tan, Φ_rad^± — mean/std over a segment → 6 classifier inputs.
FEATURE_NAMES = (
    "phi_trans",
    "phi_tan",
    "phi_rad_pm",
)


def _unit_vectors(vel: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    speeds = np.linalg.norm(vel, axis=-1)
    hat_v = np.zeros_like(vel)
    moving = speeds > 1e-9
    hat_v[moving] = vel[moving] / speeds[moving, None]
    return hat_v, moving


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

    hat_v, _ = _unit_vectors(vel)

    # Translational order: |⟨v̂_i⟩|
    phi_trans = np.linalg.norm(hat_v.mean(axis=1), axis=-1)

    centroid = pos.mean(axis=1, keepdims=True)
    r = pos - centroid
    r_norm = np.linalg.norm(r, axis=-1)
    safe = r_norm > 1e-9
    r_hat = np.zeros_like(r)
    r_hat[..., 0] = np.where(safe, r[..., 0] / np.maximum(r_norm, 1e-12), 0.0)
    r_hat[..., 1] = np.where(safe, r[..., 1] / np.maximum(r_norm, 1e-12), 0.0)

    # Tangential order: ⟨|(r̂_i × v̂_i)_z|⟩
    cross_z = r_hat[..., 0] * hat_v[..., 1] - r_hat[..., 1] * hat_v[..., 0]
    phi_tan = np.mean(np.abs(cross_z), axis=1)

    # Signed radial order: ⟨r̂_i · v̂_i⟩
    phi_rad_pm = np.mean(np.sum(r_hat * hat_v, axis=-1), axis=1)

    return {
        "phi_trans": phi_trans,
        "phi_tan": phi_tan,
        "phi_rad_pm": phi_rad_pm,
    }


def aggregate_series(
    series: dict[str, np.ndarray],
    fps: float = 30.0,
) -> dict[str, float]:
    del fps  # reserved for future temporal derivatives
    feat: dict[str, float] = {}
    for k, arr in series.items():
        feat[f"{k}_mean"] = float(np.mean(arr))
        feat[f"{k}_std"] = float(np.std(arr))
    return feat


AGG_FEATURE_NAMES = [f"{k}_{s}" for k in FEATURE_NAMES for s in ("mean", "std")]
