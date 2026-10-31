"""Sliding-window aggregation and per-frame stacking of order parameters."""

from __future__ import annotations

import numpy as np

from src.features.order_params import (
    AGG_FEATURE_NAMES,
    FEATURE_NAMES,
    compute_order_params_series,
    fifteen_point_derivative,
)

# Classifier samples are non-overlapping 15-frame windows (0.5 s).
WINDOW_FRAMES = 15
HOP_FRAMES = 15


def segment_feature_vector(
    positions: np.ndarray,
    velocities: np.ndarray,
    fps: float = 30.0,
) -> dict[str, float]:
    """Mean of the 15-frame window features that fit in the segment."""
    feats = sliding_window_features(positions, velocities, fps=fps)
    if not feats:
        return {name: 0.0 for name in AGG_FEATURE_NAMES}
    return {name: float(np.mean([feat[name] for feat in feats])) for name in AGG_FEATURE_NAMES}


def iter_window_bounds(
    n_frames: int,
    window_frames: int = WINDOW_FRAMES,
    hop_frames: int = HOP_FRAMES,
    fps: float = 30.0,
) -> list[tuple[int, int]]:
    """Non-overlapping [start, end) spans of exactly 15 frames."""
    del fps
    w = int(window_frames)
    hop = int(hop_frames)
    if w != WINDOW_FRAMES or hop != HOP_FRAMES:
        raise ValueError(
            f"Windows are {WINDOW_FRAMES} frames stepped by {HOP_FRAMES}, got {w} / {hop}"
        )
    t = int(n_frames)
    if t < w:
        return []
    return [(start, start + w) for start in range(0, t - w + 1, hop)]


def _window_feat_from_series(
    series: dict[str, np.ndarray],
    start: int,
    end: int,
    fps: float,
) -> dict[str, float]:
    feat: dict[str, float] = {}
    for key, arr in series.items():
        sl = arr[start:end]
        feat[f"{key}_mean"] = float(np.mean(sl))
        feat[f"{key}_std"] = float(np.std(sl))
        feat[f"{key}_rate"] = fifteen_point_derivative(sl, fps)
    return feat


def sliding_window_features(
    positions: np.ndarray,
    velocities: np.ndarray,
    window_frames: int = WINDOW_FRAMES,
    hop_frames: int = HOP_FRAMES,
    fps: float = 30.0,
) -> list[dict[str, float]]:
    bounds = iter_window_bounds(
        positions.shape[0], window_frames=window_frames, hop_frames=hop_frames, fps=fps
    )
    series = compute_order_params_series(positions, velocities)
    if not bounds:
        return []
    return [_window_feat_from_series(series, a, b, fps) for a, b in bounds]


def window_feature_matrix(
    positions: np.ndarray,
    velocities: np.ndarray,
    *,
    names: list[str] | None = None,
    window_frames: int = WINDOW_FRAMES,
    hop_frames: int = HOP_FRAMES,
    fps: float = 30.0,
) -> tuple[np.ndarray, list[tuple[int, int]]]:
    """One row per 15-frame window: mean Φ and its 15-point dΦ/dt. Also returns [start, end) spans."""
    names = names or list(AGG_FEATURE_NAMES)
    bounds = iter_window_bounds(
        positions.shape[0], window_frames=window_frames, hop_frames=hop_frames, fps=fps
    )
    series = compute_order_params_series(positions, velocities)
    if not bounds:
        return np.zeros((0, len(names))), []
    rows = [feature_dict_to_array(_window_feat_from_series(series, a, b, fps), names) for a, b in bounds]
    return np.vstack(rows), bounds


def feature_dict_to_array(feat: dict[str, float], names: list[str] | None = None) -> np.ndarray:
    names = names or AGG_FEATURE_NAMES
    return np.array([feat.get(n, 0.0) for n in names], dtype=np.float64)


def frame_feature_matrix(
    positions: np.ndarray,
    velocities: np.ndarray,
    *,
    names: list[str] | None = None,
    fps: float = 30.0,
) -> np.ndarray:
    """Per-frame classifier inputs: instantaneous order parameters."""
    del fps
    names = names or list(FEATURE_NAMES)
    series = compute_order_params_series(positions, velocities)
    t = next(iter(series.values())).shape[0] if series else positions.shape[0]
    return np.column_stack([np.asarray(series.get(name, np.zeros(t)), dtype=np.float64) for name in names])
