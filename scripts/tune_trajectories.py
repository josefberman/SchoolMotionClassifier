#!/usr/bin/env python3
"""Tune behavior YAMLs to match configs extracted from real trajectories.

  --extract      fit one config per 15-frame window -> annotated_config.csv,
                 including r_r, r_o, r_a (any ordered triple inside the radius bounds)
  (default)      CMA-ES over SEARCH_SPACE at the mean extracted radii. Radii are
                 not searched again. Matches mean and std (Huber loss).
  --apply-best   write results/tuning/trajectory_match/best.json into the YAMLs,
                 including those radii.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse

from src.sim.config import DEFAULTS
from src.tune.search_space import SEARCH_PARAM_NAMES
from src.tune.trajectory_match import (
    BEST_PATH,
    apply_best_to_yaml,
    build_annotated_config,
    load_annotated_config,
    save_annotated_config,
    target_stats,
    tune_all_behaviors,
)


def _print_extraction(frame) -> None:
    print("=== extracted from real trajectories (mean ± std per behavior) ===")
    for behavior, stats in target_stats(frame).items():
        n = int((frame["label"] == behavior).sum())
        print(f"\n{behavior} (n={n})")
        names = list(SEARCH_PARAM_NAMES) + [c for c in ("r_r", "r_o", "r_a") if c in frame.columns]
        for k in names:
            if k in stats:
                mean, std = stats[k]["mean"], stats[k]["std"]
            else:
                col = frame.loc[frame["label"] == behavior, k].to_numpy(dtype=float)
                mean, std = float(col.mean()), float(col.std())
            print(f"  {k:12s} {mean:+.4f} ± {std:.4f}")


def _print_tuned(summary: dict) -> None:
    print("=== tuned: simulated estimate vs real extracted (mean ± std) ===")
    for behavior, block in summary["per_behavior"].items():
        zones = summary.get("behavior_overrides", {}).get(behavior, {})
        print(
            f"\n{behavior}  loss={block['best_loss']:.4f}"
            f"  r_r={zones.get('r_r', float('nan')):.1f}"
            f" r_o={zones.get('r_o', float('nan')):.1f}"
            f" r_a={zones.get('r_a', float('nan')):.1f}"
        )
        sim = block["sim_estimate"]
        for name in SEARCH_PARAM_NAMES:
            print(
                f"  {name:12s} "
                f"sim={sim['mean'][name]:+.4f}±{sim['std'][name]:.4f}  "
                f"real={block['target_mean'][name]:+.4f}±{block['target_std'][name]:.4f}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--extract", action="store_true", help="Build annotated_config.csv and exit")
    parser.add_argument("--csv", type=Path, default=ROOT / "annotated_config.csv")
    parser.add_argument("--behaviors", nargs="*", default=None, help="Subset to tune/extract")
    parser.add_argument("--trials", type=int, default=100, help="CMA-ES evaluations per behavior")
    parser.add_argument("--n-seeds", type=int, default=6, help="Sim seeds per group size")
    parser.add_argument("--n-values", nargs="*", type=int, default=[10, 30, 70], help="Sim group sizes")
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--fast", action="store_true", help="Quick loop: 12 trials, 3 seeds, N in {10,30}")
    parser.add_argument("--r-r", type=float, default=float(DEFAULTS["r_r"]))
    parser.add_argument("--r-o", type=float, default=float(DEFAULTS["r_o"]))
    parser.add_argument("--r-a", type=float, default=float(DEFAULTS["r_a"]))
    parser.add_argument("--apply-best", action="store_true", help="Write best.json into configs/behaviors/*.yaml")
    parser.add_argument("--dry-run", action="store_true", help="With --apply-best, print paths only")
    args = parser.parse_args()
    radii = {"r_r": args.r_r, "r_o": args.r_o, "r_a": args.r_a}

    if args.apply_best:
        verb = "Would update" if args.dry_run else "Updated"
        for path in apply_best_to_yaml(dry_run=args.dry_run, **radii):
            print(f"{verb}: {path}")
        return

    if args.extract:
        frame = build_annotated_config(radii=radii, behaviors=args.behaviors)
        csv_path = save_annotated_config(frame, args.csv)
        _print_extraction(frame)
        print(f"\nAnnotated configs: {csv_path}")
        return

    frame = load_annotated_config(args.csv)
    n_trials, n_seeds, n_values = args.trials, args.n_seeds, list(args.n_values)
    if args.fast:
        n_trials, n_seeds, n_values = min(n_trials, 12), min(n_seeds, 3), [10, 30]

    _print_extraction(frame)
    print()
    summary = tune_all_behaviors(
        frame,
        behaviors=args.behaviors,
        n_trials=n_trials,
        n_seeds=n_seeds,
        n_values=n_values,
        n_jobs=args.n_jobs,
    )
    _print_tuned(summary)
    print(f"\nBest config: {BEST_PATH}")
    print("Apply with: python scripts/tune_trajectories.py --apply-best")


if __name__ == "__main__":
    main()
