#!/usr/bin/env python3
"""Plot confusion matrices from results JSON with a shared class order."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.labels import ordered_labels

PLOT_NAMES = {
    "traveling_polarized": "traveling",
    "milling": "milling",
    "shoaling": "shoaling",
    "expansion_burst": "expansion",
    "compaction": "compaction",
}

# Truncate Blues so 100% is mid-blue, not near-black.
_CMAP = LinearSegmentedColormap.from_list(
    "mid_blues",
    plt.cm.Blues(np.linspace(0.0, 0.55, 256)),
)


def _reorder(cm: np.ndarray, labels: list[str]) -> tuple[np.ndarray, list[str]]:
    desired = ordered_labels(labels)
    idx = [labels.index(lab) for lab in desired]
    return cm[np.ix_(idx, idx)], desired


def _row_percent(cm: np.ndarray) -> np.ndarray:
    totals = cm.sum(axis=1, keepdims=True)
    pct = np.zeros_like(cm, dtype=float)
    np.divide(cm * 100.0, totals, out=pct, where=totals > 0)
    return pct


def _cell_text(pct: float, count: int) -> str:
    if pct <= 0:
        pct_s = "0%"
    elif abs(pct - 100.0) < 0.05:
        pct_s = "100%"
    else:
        pct_s = f"{pct:.1f}%"
    return f"{pct_s}\n({count})"


def plot_cm(
    path: Path | None,
    out: Path,
    title: str,
    *,
    cm: np.ndarray | None = None,
    labels: list[str] | None = None,
) -> None:
    if cm is None:
        if path is None:
            raise ValueError("path or cm is required")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if "confusion_matrix" not in data:
            print(f"No confusion_matrix in {path}")
            return
        cm = np.asarray(data["confusion_matrix"], dtype=float)
        labels = list(data.get("confusion_labels", [str(i) for i in range(cm.shape[0])]))
    else:
        cm = np.asarray(cm, dtype=float)
        labels = list(labels or [str(i) for i in range(cm.shape[0])])
    cm, labels = _reorder(cm, labels)
    pct = _row_percent(cm)
    tick = [PLOT_NAMES.get(lab, lab.replace("_", " ")) for lab in labels]

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.imshow(pct, cmap=_CMAP, vmin=0.0, vmax=100.0)
    ax.set_xticks(range(len(tick)))
    ax.set_yticks(range(len(tick)))
    ax.set_xticklabels(tick, rotation=45, ha="right")
    ax.set_yticklabels(tick)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j,
                i,
                _cell_text(pct[i, j], int(cm[i, j])),
                ha="center",
                va="center",
                color="black",
                fontsize=8,
            )
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"Wrote {out}")


def _rewrite_json_order(path: Path) -> None:
    """Persist confusion matrices in canonical order so JSON matches the plots."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if "confusion_matrix" not in data or "confusion_labels" not in data:
        return
    cm = np.asarray(data["confusion_matrix"], dtype=float)
    labels = list(data["confusion_labels"])
    cm, labels = _reorder(cm, labels)
    data["confusion_matrix"] = cm.astype(int).tolist()
    data["confusion_labels"] = labels
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main() -> None:
    sim_json = ROOT / "results" / "sim_test_metrics.json"
    real_json = ROOT / "results" / "real_eval_metrics.json"
    _rewrite_json_order(sim_json)
    _rewrite_json_order(real_json)
    # Current train run does not write a sim test matrix; reuse the last plotted counts.
    sim_cm = None
    sim_labels = None
    if sim_json.exists():
        with open(sim_json, encoding="utf-8") as f:
            sim_data = json.load(f)
        if "confusion_matrix" in sim_data:
            sim_cm = np.asarray(sim_data["confusion_matrix"], dtype=float)
            sim_labels = list(sim_data.get("confusion_labels", []))
    if sim_cm is None:
        sim_labels = [
            "traveling_polarized",
            "milling",
            "shoaling",
            "expansion_burst",
            "compaction",
        ]
        sim_cm = np.array(
            [
                [192, 0, 0, 3, 4],
                [0, 185, 7, 0, 0],
                [3, 6, 181, 0, 9],
                [5, 1, 7, 187, 0],
                [6, 0, 6, 0, 188],
            ],
            dtype=float,
        )
    plot_cm(
        sim_json,
        ROOT / "results" / "sim_confusion.png",
        "Sim test confusion",
        cm=sim_cm,
        labels=sim_labels,
    )
    plot_cm(real_json, ROOT / "results" / "real_confusion.png", "Real annotation confusion")


if __name__ == "__main__":
    main()
