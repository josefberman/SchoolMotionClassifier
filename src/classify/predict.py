"""Per-window behavior predictions from a trained classifier."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.features.order_params import AGG_FEATURE_NAMES
from src.features.windows import WINDOW_FRAMES, window_feature_matrix
from src.sim.io import load_trajectory_table, pos_vel_from_table, save_trajectory_table

ROOT = Path(__file__).resolve().parents[2]


def predict_trajectory(
    trajectory_path: Path,
    model_path: Path | None = None,
    out_path: Path | None = None,
    *,
    fps: float = 30.0,
    column: str = "predicted_behavior",
) -> pd.DataFrame:
    """Label 5-frame windows and write those labels onto the corresponding frames."""
    trajectory_path = Path(trajectory_path)
    model_path = Path(model_path or (ROOT / "results" / "classifier.joblib"))
    out_path = Path(out_path) if out_path is not None else None

    df = load_trajectory_table(trajectory_path)
    pos, vel = pos_vel_from_table(df, fps=fps)
    if pos.shape[0] == 0:
        raise ValueError(f"No frames in {trajectory_path}")

    bundle = joblib.load(model_path)
    model = bundle["model"]
    le = bundle["label_encoder"]
    names = list(bundle.get("feature_names") or AGG_FEATURE_NAMES)

    X, bounds = window_feature_matrix(pos, vel, fps=fps, names=names)
    if X.shape[0] == 0:
        raise ValueError(f"Need at least {WINDOW_FRAMES} frames for a window, got {pos.shape[0]}")
    window_pred = le.inverse_transform(np.asarray(model.predict(X)))
    labels = np.empty(pos.shape[0], dtype=object)
    labels[:] = window_pred[-1] if len(window_pred) else ""
    for (a, b), lab in zip(bounds, window_pred):
        labels[a:b] = lab

    out = df.copy()
    out[column] = labels
    if out_path is not None:
        if out_path.suffix == "":
            out_path = out_path.with_suffix(trajectory_path.suffix)
        save_trajectory_table(out_path, out)
    return out
