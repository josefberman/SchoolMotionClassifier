#!/usr/bin/env python3
"""Plot confusion matrices from results JSON with a shared class order."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.ticker import LogFormatterSciNotation

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

# Truncate Greens so the max cell is mid-green, not near-black.
_CMAP = LinearSegmentedColormap.from_list(
    "mid_greens",
    plt.cm.Greens(np.linspace(0.0, 0.55, 256)),
)
# Zero counts fall outside the log scale and are drawn as empty cells.
_CMAP.set_bad("white")


def _reorder(cm: np.ndarray, labels: list[str]) -> tuple[np.ndarray, list[str]]:
    desired = ordered_labels(labels)
    idx = [labels.index(lab) for lab in desired]
    return cm[np.ix_(idx, idx)], desired


def plot_cm(path: Path, out: Path, title: str) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if "confusion_matrix" not in data:
        print(f"No confusion_matrix in {path}")
        return
    cm = np.asarray(data["confusion_matrix"], dtype=float)
    labels = list(data.get("confusion_labels", [str(i) for i in range(cm.shape[0])]))
    cm, labels = _reorder(cm, labels)
    tick = [PLOT_NAMES.get(lab, lab.replace("_", " ")) for lab in labels]

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(
        np.ma.masked_less(cm, 1.0),
        cmap=_CMAP,
        norm=LogNorm(vmin=1.0, vmax=max(cm.max(), 2.0)),
    )
    ax.set_xticks(range(len(tick)))
    ax.set_yticks(range(len(tick)))
    ax.set_xticklabels(tick, rotation=45, ha="right")
    ax.set_yticklabels(tick)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center", color="black", fontsize=8)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046)
    cbar.ax.yaxis.set_major_formatter(LogFormatterSciNotation(labelOnlyBase=False))
    cbar.set_label("count (log scale)")
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
    plot_cm(sim_json, ROOT / "results" / "sim_confusion.png", "Sim test confusion")
    plot_cm(real_json, ROOT / "results" / "real_confusion.png", "Real annotation confusion")


if __name__ == "__main__":
    main()
