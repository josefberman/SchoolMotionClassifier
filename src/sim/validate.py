"""Soft validation of simulated behaviours via order-parameter signatures."""

from __future__ import annotations

import numpy as np

from src.features.order_params import compute_order_params_series


def summarize_metrics(positions: np.ndarray, velocities: np.ndarray) -> dict[str, float]:
    series = compute_order_params_series(positions, velocities)
    t0, t1 = len(series["phi_dir"]) // 4, 3 * len(series["phi_dir"]) // 4
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
        pre = slice(0, 100)
        mid = slice(110, 280)
        d_sig = float(np.max(series["sigma_d"][mid]) - np.mean(series["sigma_d"][pre]))
        d_phi = float(np.mean(series["phi_dir"][pre]) - np.min(series["phi_dir"][mid]))
        return d_sig > 1.0 or d_phi > 0.05
    if behavior == "expansion_burst":
        if positions is None or velocities is None:
            return True
        series = compute_order_params_series(positions, velocities)
        pre = slice(0, 120)
        event = slice(130, 250)
        d_sig = float(np.max(series["sigma_d"][event]) - np.mean(series["sigma_d"][pre]))
        vr_max = float(np.max(series["v_r_bar"][event]))
        return d_sig > 1.5 or vr_max > 0.08
    if behavior == "compaction":
        if positions is None or velocities is None:
            return True
        series = compute_order_params_series(positions, velocities)
        pre = slice(0, 120)
        event = slice(160, 320)
        r_pre = float(np.mean(np.linalg.norm(positions[pre] - positions[pre].mean(axis=1, keepdims=True), axis=-1)))
        r_ev = float(np.mean(np.linalg.norm(positions[event][-40:] - positions[event][-40:].mean(axis=1, keepdims=True), axis=-1)))
        d_sig = float(np.mean(series["sigma_d"][event][-40:]) - np.mean(series["sigma_d"][pre]))
        return (r_ev - r_pre) < -2.0 or d_sig < -0.8
    return True
