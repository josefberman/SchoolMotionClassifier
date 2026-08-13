"""Soft validation of simulated behaviours via order-parameter signatures."""

from __future__ import annotations

import numpy as np

from src.features.order_params import compute_order_params_series


def summarize_metrics(positions: np.ndarray, velocities: np.ndarray) -> dict[str, float]:
    series = compute_order_params_series(positions, velocities)
    out = {}
    for k, arr in series.items():
        out[f"{k}_mean"] = float(np.mean(arr))
        out[f"{k}_std"] = float(np.std(arr))
    out["phi_rad_event"] = float(np.mean(series["phi_rad_pm"]))
    return out


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
        return phi_trans > 0.90 and 0.50 < phi_tan < 0.75
    if behavior == "milling":
        return phi_tan > 0.85 and phi_trans < 0.45
    if behavior == "swarming":
        return phi_trans < 0.45 and 0.55 < phi_tan < 0.72 and abs(phi_rad) < 0.30
    if behavior == "fountain_evasion":
        if positions is None or velocities is None:
            return True
        series = compute_order_params_series(positions, velocities)
        return float(np.std(series["phi_trans"])) > 0.12 or float(np.std(series["phi_tan"])) > 0.15
    if behavior == "expansion_burst":
        return phi_rad > 0.80 and phi_tan < 0.40
    if behavior == "compaction":
        return phi_rad < -0.55 and phi_tan < 0.45
    return True
