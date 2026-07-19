"""CSV / JSON IO matching real schooling-datasets schema."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def trajectory_to_dataframe(
    positions: np.ndarray,
    velocities: np.ndarray,
) -> pd.DataFrame:
    """positions, velocities: (T, N, 2)."""
    t, n, _ = positions.shape
    cols: dict[str, np.ndarray] = {"frame": np.arange(t, dtype=np.int32)}
    for i in range(n):
        cols[f"fish{i}_x"] = positions[:, i, 0]
        cols[f"fish{i}_y"] = positions[:, i, 1]
        cols[f"fish{i}_vx"] = velocities[:, i, 0]
        cols[f"fish{i}_vy"] = velocities[:, i, 1]
    return pd.DataFrame(cols)


def save_trajectory_csv(
    path: Path,
    positions: np.ndarray,
    velocities: np.ndarray,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    trajectory_to_dataframe(positions, velocities).to_csv(path, index=False)


def load_trajectory_csv(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return positions, velocities as (T, N, 2)."""
    df = pd.read_csv(path)
    fish_ids = sorted(
        {int(c[4:].split("_")[0]) for c in df.columns if c.startswith("fish") and c.endswith("_x")}
    )
    t = len(df)
    n = len(fish_ids)
    pos = np.zeros((t, n, 2), dtype=np.float64)
    vel = np.zeros((t, n, 2), dtype=np.float64)
    for i, fid in enumerate(fish_ids):
        pos[:, i, 0] = df[f"fish{fid}_x"].to_numpy()
        pos[:, i, 1] = df[f"fish{fid}_y"].to_numpy()
        vel[:, i, 0] = df[f"fish{fid}_vx"].to_numpy()
        vel[:, i, 1] = df[f"fish{fid}_vy"].to_numpy()
    return pos, vel


def mmss_to_frame(mmss: str, fps: float) -> int:
    parts = mmss.strip().split(":")
    if len(parts) == 2:
        m, s = int(parts[0]), int(parts[1])
        total = m * 60 + s
    elif len(parts) == 3:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        total = h * 3600 + m * 60 + s
    else:
        raise ValueError(f"Bad timestamp: {mmss!r}")
    return int(round(total * fps))


def save_motion_json(
    path: Path,
    dataset: str,
    fps: float,
    segments: list[dict],
    source: str = "simulation",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"dataset": dataset, "fps": fps, "source": source, "segments": segments},
            f,
            indent=2,
        )
        f.write("\n")


def load_motion_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
