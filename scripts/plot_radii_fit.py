#!/usr/bin/env python3
"""Corner plot of pooled window radii, in meters.

Diagonal: histogram of each radius. Lower panels: 2D histogram of each pair.
Writes results/figures/radii_fit.pdf and .png.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import PowerNorm
from matplotlib.ticker import FormatStrFormatter, MultipleLocator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NAMES = ("r_r", "r_o", "r_a")
LABELS = (r"$r_r$ (m)", r"$r_o$ (m)", r"$r_a$ (m)")
# Search box in px. The arena rectangle is 1900 × 1020 px; the tank is 2.1 × 1.2 m.
RANGES_PX = ((5.0, 200.0), (10.0, 500.0), (20.0, 1000.0))
M_PER_PX = float(np.hypot(2.1, 1.2) / np.hypot(1900.0, 1020.0))
RANGES = tuple((lo * M_PER_PX, hi * M_PER_PX) for lo, hi in RANGES_PX)
TICK_STEP = (0.02, 0.05, 0.1)
BINS = 40


def _radius_axis(axis, i: int) -> None:
    axis.set_major_locator(MultipleLocator(TICK_STEP[i]))
    axis.set_major_formatter(FormatStrFormatter("%.2f"))


def main() -> None:
    data = pd.read_csv(ROOT / "annotated_config.csv")[list(NAMES)].to_numpy(dtype=float) * M_PER_PX
    edges = [np.linspace(lo, hi, BINS + 1) for lo, hi in RANGES]

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, axes = plt.subplots(3, 3, figsize=(6.0, 6.0))
    bar = plt.cm.Blues(0.6)

    pairs = {}
    for row in range(1, 3):
        for col in range(row):
            counts, _, _ = np.histogram2d(data[:, col], data[:, row], bins=[edges[col], edges[row]])
            pairs[(row, col)] = counts
    # Square-root scale so the dense r_o–r_a ridge does not wash out the other panels.
    norm = PowerNorm(gamma=0.5, vmin=0.0, vmax=max(float(c.max()) for c in pairs.values()))

    for row in range(3):
        for col in range(3):
            ax = axes[row, col]
            if col > row:
                ax.set_axis_off()
                continue

            if row == col:
                counts, _ = np.histogram(data[:, col], bins=edges[col])
                ax.stairs(counts, edges[col], fill=True, color=bar, linewidth=0)
                ax.set_ylim(0, None)
                ax.set_yticks([])
                for side in ("left", "right", "top"):
                    ax.spines[side].set_visible(False)
            else:
                counts = np.ma.masked_equal(pairs[(row, col)].T, 0.0)
                ax.pcolormesh(edges[col], edges[row], counts, cmap="Blues", norm=norm, rasterized=True)
                ax.set_ylim(*RANGES[row])
                _radius_axis(ax.yaxis, row)
                if col == 0:
                    ax.set_ylabel(LABELS[row])
                else:
                    ax.tick_params(labelleft=False)

            ax.set_xlim(*RANGES[col])
            _radius_axis(ax.xaxis, col)
            if row == 2:
                ax.set_xlabel(LABELS[col])
            else:
                ax.tick_params(labelbottom=False)

    fig.subplots_adjust(left=0.13, right=0.97, bottom=0.10, top=0.97, hspace=0.08, wspace=0.08)
    fig.align_ylabels(axes[:, 0])
    out_dir = ROOT / "results" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = out_dir / "radii_fit.pdf"
    png = out_dir / "radii_fit.png"
    fig.savefig(pdf, dpi=300)
    fig.savefig(png, dpi=200)
    plt.close(fig)
    print(f"Wrote {pdf}")
    print(f"Wrote {png}")


if __name__ == "__main__":
    main()
