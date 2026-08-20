"""Three collective order parameters for five-class motion classification."""

from __future__ import annotations

import numpy as np

# Φ_trans, Ψ_tan, Ψ_rad^± — segment means are the classifier inputs.
FEATURE_NAMES = (
    "phi_trans",
    "psi_tan",
    "psi_rad_pm",
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
    """Vectorized over time. positions, velocities: (T, N, 2).

    Φ_trans = ||⟨v̂_i⟩||

    Center unit headings and radial vectors:
        v'_i = v̂_i − v̄ ,  r'_i = r̂_i − r̄
        D = sqrt( (∑_i ||v'_i||²) (∑_i ||r'_i||²) )

    Ψ_rad^± = (∑_i v'_i · r'_i) / D
    Ψ_tan   = |∑_i (r'_i × v'_i)_z| / D
    """
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

    v_p = hat_v - hat_v.mean(axis=1, keepdims=True)
    r_p = r_hat - r_hat.mean(axis=1, keepdims=True)
    sum_v2 = np.sum(v_p[..., 0] ** 2 + v_p[..., 1] ** 2, axis=1)
    sum_r2 = np.sum(r_p[..., 0] ** 2 + r_p[..., 1] ** 2, axis=1)
    denom = np.sqrt(sum_v2 * sum_r2)

    psi_rad_pm = np.zeros(t)
    np.divide(np.sum(v_p * r_p, axis=(1, 2)), denom, out=psi_rad_pm, where=denom > 1e-12)

    cross_z = r_p[..., 0] * v_p[..., 1] - r_p[..., 1] * v_p[..., 0]
    psi_tan = np.zeros(t)
    np.divide(np.abs(np.sum(cross_z, axis=1)), denom, out=psi_tan, where=denom > 1e-12)

    return {
        "phi_trans": phi_trans,
        "psi_tan": psi_tan,
        "psi_rad_pm": psi_rad_pm,
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


AGG_FEATURE_NAMES = [f"{k}_mean" for k in FEATURE_NAMES]
