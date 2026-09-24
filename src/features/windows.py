"""Sliding-window aggregation of order parameters."""

from __future__ import annotations

import numpy as np

from src.features.order_params import (
    AGG_FEATURE_NAMES,
    aggregate_series,
    compute_order_params_series,
)


def segment_feature_vector(
    positions: np.ndarray,
    velocities: np.ndarray,
    fps: float = 30.0,
) -> dict[str, float]:
    series = compute_order_params_series(positions, velocities)
    return aggregate_series(series, fps=fps)


def sliding_window_features(
    positions: np.ndarray,
    velocities: np.ndarray,
    window_sec: float = 2.0,
    hop_sec: float = 1.0,
    fps: float = 30.0,
) -> list[dict[str, float]]:
    w = max(2, int(round(window_sec * fps)))
    h = max(1, int(round(hop_sec * fps)))
    t = positions.shape[0]
    feats = []
    for start in range(0, max(1, t - w + 1), h):
        end = min(t, start + w)
        if end - start < max(2, w // 2):
            continue
        feats.append(
            segment_feature_vector(positions[start:end], velocities[start:end], fps=fps)
        )
    if not feats:
        feats.append(segment_feature_vector(positions, velocities, fps=fps))
    return feats


def feature_dict_to_array(feat: dict[str, float], names: list[str] | None = None) -> np.ndarray:
    names = names or AGG_FEATURE_NAMES
    return np.array([feat.get(n, 0.0) for n in names], dtype=np.float64)


def _rolling_mean_std(x: np.ndarray, left: np.ndarray, right: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    c1 = np.concatenate([[0.0], np.cumsum(x, dtype=np.float64)])
    c2 = np.concatenate([[0.0], np.cumsum(x * x, dtype=np.float64)])
    n = (right - left).astype(np.float64)
    n = np.maximum(n, 1.0)
    mean = (c1[right] - c1[left]) / n
    var = np.maximum((c2[right] - c2[left]) / n - mean * mean, 0.0)
    return mean, np.sqrt(var)


def frame_feature_matrix(
    positions: np.ndarray,
    velocities: np.ndarray,
    *,
    window_sec: float = 2.0,
    fps: float = 30.0,
    names: list[str] | None = None,
) -> np.ndarray:
    """Per-frame classifier inputs: centered rolling mean/std of order parameters."""
    names = names or AGG_FEATURE_NAMES
    series = compute_order_params_series(positions, velocities)
    t = positions.shape[0]
    window = max(1, int(round(window_sec * fps)))
    half = window // 2
    idx = np.arange(t)
    left = np.maximum(0, idx - half)
    right = np.minimum(t, idx + half + 1)
    stats: dict[str, np.ndarray] = {}
    for key, arr in series.items():
        mean, std = _rolling_mean_std(np.asarray(arr, dtype=np.float64), left, right)
        stats[f"{key}_mean"] = mean
        stats[f"{key}_std"] = std
    return np.column_stack([stats.get(name, np.zeros(t)) for name in names])
