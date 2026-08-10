"""Build feature matrices from simulated and real annotated trajectories."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.features.order_params import AGG_FEATURE_NAMES
from src.features.windows import feature_dict_to_array, segment_feature_vector, sliding_window_features
from src.labels import canonicalize, load_aliases
from src.sim.io import load_motion_json, load_trajectory_csv, mmss_to_frame

ROOT = Path(__file__).resolve().parents[2]


def load_manifest(path: Path | None = None) -> list[dict]:
    path = path or (ROOT / "sim_datasets" / "manifest.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def features_from_sim_entry(
    entry: dict,
    mode: str = "segment",
    window_sec: float = 2.0,
    sim_root: Path | None = None,
) -> list[tuple[np.ndarray, str]]:
    """Return list of (x, label)."""
    sim_root = sim_root or (ROOT / "sim_datasets")
    csv_path = Path(entry["csv"])
    if not csv_path.is_absolute():
        csv_path = sim_root / csv_path
    pos, vel = load_trajectory_csv(csv_path)
    fps = float(entry.get("fps", 30.0))
    label = entry["behavior"]
    if mode == "windows":
        feats = sliding_window_features(pos, vel, window_sec=window_sec, fps=fps)
    else:
        # For threat behaviours, focus on event window if provided
        if entry.get("event_start") is not None:
            a = int(entry["event_start"])
            b = int(entry.get("event_end", min(pos.shape[0], a + 200)))
            a = max(0, min(a, pos.shape[0] - 2))
            b = max(a + 2, min(b, pos.shape[0]))
            feats = [segment_feature_vector(pos[a:b], vel[a:b], fps=fps)]
        else:
            feats = [segment_feature_vector(pos, vel, fps=fps)]
    return [(feature_dict_to_array(f), label) for f in feats]


def build_sim_xy(
    split: str = "train",
    manifest_path: Path | None = None,
    sim_root: Path | None = None,
    mode: str = "segment",
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    manifest_path = manifest_path or (ROOT / "sim_datasets" / "manifest.json")
    sim_root = sim_root or manifest_path.parent
    entries = [e for e in load_manifest(manifest_path) if e.get("split") == split and e.get("valid", True)]
    xs, ys = [], []
    for e in entries:
        for x, y in features_from_sim_entry(e, mode=mode, sim_root=sim_root):
            xs.append(x)
            ys.append(y)
    if not xs:
        return np.zeros((0, len(AGG_FEATURE_NAMES))), np.array([], dtype=object), list(AGG_FEATURE_NAMES)
    return np.vstack(xs), np.array(ys, dtype=object), list(AGG_FEATURE_NAMES)


def load_real_segments(
    annotations_dir: Path | None = None,
    datasets_json: Path | None = None,
) -> list[dict]:
    annotations_dir = annotations_dir or (ROOT / "annotations")
    datasets_json = datasets_json or (annotations_dir / "datasets.json")
    with open(datasets_json, encoding="utf-8") as f:
        meta = json.load(f)
    aliases = load_aliases()
    out = []
    for path in sorted(annotations_dir.glob("*_motion.json")):
        if path.name.startswith("_"):
            continue
        ann = load_motion_json(path)
        ds = ann["dataset"]
        if ds not in meta:
            continue
        fps = float(ann.get("fps", meta[ds]["fps"]))
        group = meta[ds]["fish_group"]
        csv = ROOT / "schooling-datasets" / group / ds / f"{ds}_loc_vel_data.csv"
        if not csv.exists():
            continue
        for seg in ann["segments"]:
            try:
                label = canonicalize(seg["label"], aliases)
            except ValueError:
                continue
            start = mmss_to_frame(seg["start"], fps)
            end = mmss_to_frame(seg["end"], fps)
            if end - start < int(0.5 * fps):
                continue
            out.append(
                {
                    "dataset": ds,
                    "csv": str(csv.relative_to(ROOT)),
                    "start": start,
                    "end": end,
                    "label": label,
                    "fps": fps,
                }
            )
    return out


def build_real_xy(
    min_frames: int = 15,
) -> tuple[np.ndarray, np.ndarray, list[str], list[dict]]:
    segs = load_real_segments()
    xs, ys, kept = [], [], []
    for s in segs:
        pos, vel = load_trajectory_csv(ROOT / s["csv"])
        a, b = s["start"], min(s["end"], pos.shape[0])
        if b - a < min_frames:
            continue
        feat = segment_feature_vector(pos[a:b], vel[a:b], fps=s["fps"])
        xs.append(feature_dict_to_array(feat))
        ys.append(s["label"])
        kept.append(s)
    if not xs:
        return np.zeros((0, len(AGG_FEATURE_NAMES))), np.array([], dtype=object), list(AGG_FEATURE_NAMES), []
    return np.vstack(xs), np.array(ys, dtype=object), list(AGG_FEATURE_NAMES), kept
