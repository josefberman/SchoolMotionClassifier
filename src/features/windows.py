"""Sliding-window aggregation and per-frame stacking of order parameters."""

from __future__ import annotations

import numpy as np

from src.features.order_params import (
    AGG_FEATURE_NAMES,
    FEATURE_NAMES,
    aggregate_series,
    compute_order_params_series,
)

# Classifier samples are non-overlapping 5-frame windows of instantaneous Φ.
WINDOW_FRAMES = 5
HOP_FRAMES = 5


def segment_feature_vector(
    positions: np.ndarray,
    velocities: np.ndarray,
    fps: float = 30.0,
) -> dict[str, float]:
    series = compute_order_params_series(positions, velocities)
    return aggregate_series(series, fps=fps)


def iter_window_bounds(
    n_frames: int,
    window_frames: int = WINDOW_FRAMES,
    hop_frames: int = HOP_FRAMES,
    fps: float = 30.0,
) -> list[tuple[int, int]]:
    """[start, end) spans of `window_frames` frames, stepped by `hop_frames`."""
    del fps
    w = max(2, int(window_frames))
    h = max(1, int(hop_frames))
    t = int(n_frames)
    if t < w:
        return [(0, t)] if t >= 2 else []
    return [(start, start + w) for start in range(0, t - w + 1, h)]


def _window_feat_from_series(series: dict[str, np.ndarray], start: int, end: int) -> dict[str, float]:
    feat: dict[str, float] = {}
    for key, arr in series.items():
        sl = arr[start:end]
        feat[f"{key}_mean"] = float(np.mean(sl))
        feat[f"{key}_std"] = float(np.std(sl))
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
        return [aggregate_series(series, fps=fps)]
    return [_window_feat_from_series(series, a, b) for a, b in bounds]


def window_feature_matrix(
    positions: np.ndarray,
    velocities: np.ndarray,
    *,
    names: list[str] | None = None,
    window_frames: int = WINDOW_FRAMES,
    hop_frames: int = HOP_FRAMES,
    fps: float = 30.0,
) -> tuple[np.ndarray, list[tuple[int, int]]]:
    """One row per 5-frame window: mean Φ over the window. Also returns [start, end) spans."""
    names = names or list(AGG_FEATURE_NAMES)
    bounds = iter_window_bounds(
        positions.shape[0], window_frames=window_frames, hop_frames=hop_frames, fps=fps
    )
    series = compute_order_params_series(positions, velocities)
    if not bounds:
        feat = aggregate_series(series, fps=fps)
        return feature_dict_to_array(feat, names)[None, :], [(0, int(positions.shape[0]))]
    rows = [feature_dict_to_array(_window_feat_from_series(series, a, b), names) for a, b in bounds]
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
