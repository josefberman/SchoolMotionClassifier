"""Soft validation of simulated behaviours via order-parameter signatures."""

from __future__ import annotations

import numpy as np

from src.features.order_params import compute_order_params_series


def summarize_metrics(positions: np.ndarray, velocities: np.ndarray) -> dict[str, float]:
    series = compute_order_params_series(positions, velocities)
    t0, t1 = 0, len(series["phi_dir"])
    out = {}
    for k, arr in series.items():
        out[f"{k}_mean"] = float(np.mean(arr[t0:t1]))
        out[f"{k}_std"] = float(np.std(arr[t0:t1]))
    out["sigma_d_delta"] = float(series["sigma_d"][t1 - 1] - series["sigma_d"][t0])
    out["v_r_event"] = float(np.mean(series["v_r_bar"][t0:t1]))
    return out


def validate_behavior(
    behavior: str,
    metrics: dict[str, float],
    positions: np.ndarray | None = None,
    velocities: np.ndarray | None = None,
) -> bool:
    phi = metrics["phi_dir_mean"]
    l_abs = abs(metrics["l_bar_mean"])
    prot = metrics["phi_rot_mean"]
    ptan = metrics["phi_tan_mean"]

    if behavior == "traveling_polarized":
        return phi > 0.48 and l_abs < 0.50
    if behavior == "milling":
        return ptan > 0.30 and phi < 0.80 and (l_abs > 0.08 or (prot < 0.55 and ptan > 0.40))
    if behavior == "swarming":
        return phi < 0.60 and l_abs < 0.45
    if behavior == "fountain_evasion":
        if positions is None or velocities is None:
            return True
        series = compute_order_params_series(positions, velocities)
        sig_std = float(np.std(series["sigma_d"]))
        sig_range = float(np.max(series["sigma_d"]) - np.min(series["sigma_d"]))
        return sig_std > 0.35 or sig_range > 1.0
    if behavior == "expansion_burst":
        if positions is None or velocities is None:
            return True
        series = compute_order_params_series(positions, velocities)
        sig_mean = float(np.mean(series["sigma_d"]))
        vr_mean = float(np.mean(series["v_r_bar"]))
        return sig_mean > 4.0 or vr_mean > 0.06
    if behavior == "compaction":
        if positions is None or velocities is None:
            return True
        series = compute_order_params_series(positions, velocities)
        d_sig = metrics["sigma_d_delta"]
        w = min(30, max(10, positions.shape[0] // 4))
        r0 = float(np.mean(np.linalg.norm(positions[:w] - positions[:w].mean(axis=1, keepdims=True), axis=-1)))
        r1 = float(np.mean(np.linalg.norm(positions[-w:] - positions[-w:].mean(axis=1, keepdims=True), axis=-1)))
        return d_sig < -0.5 or (r1 - r0) < -2.0
    return True
