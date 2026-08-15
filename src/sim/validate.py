"""Soft validation of simulated behaviours via order-parameter signatures."""

from __future__ import annotations

import numpy as np

from src.features.order_params import compute_order_params_series

# CouzinLab calibration bands (results/calibration_report_real.json): mean ± 2.5 σ.
_BOUNDS: dict[str, dict[str, float]] = {
    "traveling_polarized": {
        "phi_trans_min": 0.65,
        "phi_tan_min": 0.44,
        "phi_tan_max": 0.73,
    },
    "milling": {
        "phi_tan_min": 0.65,
        "phi_trans_max": 0.61,
    },
    "swarming": {
        "phi_trans_max": 0.72,
        "phi_tan_min": 0.58,
        "phi_tan_max": 0.74,
        "phi_rad_abs_max": 0.31,
    },
    "expansion_burst": {
        "phi_rad_min": 0.0,
        "phi_tan_max": 0.78,
    },
    "compaction": {
        "phi_rad_max": 0.0,
        "phi_tan_max": 0.85,
    },
}


def summarize_metrics(positions: np.ndarray, velocities: np.ndarray) -> dict[str, float]:
    series = compute_order_params_series(positions, velocities)
    out = {}
    for k, arr in series.items():
        out[f"{k}_mean"] = float(np.mean(arr))
        out[f"{k}_std"] = float(np.std(arr))
    out["phi_rad_event"] = float(np.mean(series["phi_rad_pm"]))
    return out


def metrics_for_validation(
    behavior: str,
    positions: np.ndarray,
    velocities: np.ndarray,
    *,
    event_start: int | None = None,
    event_end: int | None = None,
) -> dict[str, float]:
    """Compute validation metrics on the same frame range used for training features."""
    pos, vel = positions, velocities
    if behavior in ("expansion_burst", "compaction") and event_start is not None and event_end is not None:
        a = max(0, int(event_start))
        b = min(int(event_end), pos.shape[0])
        if b > a:
            pos, vel = pos[a:b], vel[a:b]
    return summarize_metrics(pos, vel)


def validate_behavior(
    behavior: str,
    metrics: dict[str, float],
    positions: np.ndarray | None = None,
    velocities: np.ndarray | None = None,
) -> bool:
    phi_trans = metrics["phi_trans_mean"]
    phi_tan = metrics["phi_tan_mean"]
    phi_rad = metrics["phi_rad_pm_mean"]

    if behavior == "traveling_polarized":
        b = _BOUNDS[behavior]
        return phi_trans > b["phi_trans_min"] and b["phi_tan_min"] < phi_tan < b["phi_tan_max"]
    if behavior == "milling":
        b = _BOUNDS[behavior]
        return phi_tan > b["phi_tan_min"] and phi_trans < b["phi_trans_max"]
    if behavior == "swarming":
        b = _BOUNDS[behavior]
        return (
            phi_trans < b["phi_trans_max"]
            and b["phi_tan_min"] < phi_tan < b["phi_tan_max"]
            and abs(phi_rad) < b["phi_rad_abs_max"]
        )
    if behavior == "fountain_evasion":
        if positions is None or velocities is None:
            return True
        series = compute_order_params_series(positions, velocities)
        return float(np.std(series["phi_trans"])) > 0.12 or float(np.std(series["phi_tan"])) > 0.15
    if behavior == "expansion_burst":
        b = _BOUNDS[behavior]
        return phi_rad > b["phi_rad_min"] and phi_tan < b["phi_tan_max"]
    if behavior == "compaction":
        b = _BOUNDS[behavior]
        return phi_rad < b["phi_rad_max"] and phi_tan < b["phi_tan_max"]
    return True
