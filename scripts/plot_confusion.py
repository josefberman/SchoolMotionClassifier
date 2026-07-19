#!/usr/bin/env python3
"""Plot confusion matrices from results JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def plot_cm(path: Path, out: Path, title: str) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if "confusion_matrix" not in data:
        print(f"No confusion_matrix in {path}")
        return
    cm = np.asarray(data["confusion_matrix"], dtype=float)
    labels = data.get("confusion_labels", [str(i) for i in range(cm.shape[0])])
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center", color="black", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"Wrote {out}")


def main() -> None:
    plot_cm(
        ROOT / "results" / "sim_test_metrics.json",
        ROOT / "results" / "sim_confusion.png",
        "Sim test confusion",
    )
    plot_cm(
        ROOT / "results" / "real_eval_metrics.json",
        ROOT / "results" / "real_confusion.png",
        "Real annotation confusion",
    )


if __name__ == "__main__":
    main()
