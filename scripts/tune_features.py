#!/usr/bin/env python3
"""Tune behavior YAML overrides to match real order-parameter means and stds."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml

from src.labels import BEHAVIOR_SHORT, canonicalize
from src.features.order_params import CALIBRATION_FEATURE_NAMES
from src.sim.config import CONFIG_DIR, deep_merge, validate_radii
from src.tune.feature_match import BEST_PATH, tune_all_behaviors

DEFAULT_RADII = {"r_r": 50.0, "r_o": 100.0, "r_a": 150.0}


def radii_overrides(r_r: float, r_o: float, r_a: float) -> dict[str, float]:
    radii = {"r_r": float(r_r), "r_o": float(r_o), "r_a": float(r_a)}
    validate_radii(radii)
    return radii


def write_radii_to_yamls(r_r: float, r_o: float, r_a: float) -> list[str]:
    """Write fixed Couzin radii into every behavior YAML (weights unchanged)."""
    radii = radii_overrides(r_r, r_o, r_a)
    updated = []
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            current = yaml.safe_load(f) or {}
        current.update(radii)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(current, f, sort_keys=False, default_flow_style=False)
        updated.append(str(path))
    return updated


def _print_feature_summary(summary: dict) -> None:
    print("=== feature-match summary ===")
    print(f"total_loss={summary['total_loss']:.4f}")
    for behavior, block in summary["sim_features"].items():
        tgt = summary["target_features"].get(behavior)
        if tgt is None:
            continue
        print(f"\n{behavior}:")
        for feat in CALIBRATION_FEATURE_NAMES:
            if feat not in block or feat not in tgt:
                continue
            sm = block[feat]["mean"]
            ss = block[feat]["std"]
            tm = tgt[feat]["mean"]
            ts = tgt[feat]["std"]
            print(
                f"  {feat:18s}  "
                f"sim={sm:+.4f}±{ss:.4f}  "
                f"target={tm:+.4f}±{ts:.4f}  "
                f"Δmean={sm - tm:+.4f}  Δstd={ss - ts:+.4f}"
            )


def apply_best_to_yaml(
    best_path: Path | None = None,
    *,
    dry_run: bool = False,
    r_r: float = DEFAULT_RADII["r_r"],
    r_o: float = DEFAULT_RADII["r_o"],
    r_a: float = DEFAULT_RADII["r_a"],
) -> list[str]:
    """Merge feature-match best overrides into configs/behaviors/*.yaml."""
    best_path = best_path or BEST_PATH
    radii = radii_overrides(r_r, r_o, r_a)
    with open(best_path, encoding="utf-8") as f:
        best = json.load(f)
    overrides = best.get("behavior_overrides") or {}
    updated = []
    for behavior, ov in overrides.items():
        try:
            behavior = canonicalize(behavior)
        except ValueError:
            continue
        short = BEHAVIOR_SHORT.get(behavior)
        if not short:
            continue
        path = CONFIG_DIR / f"{short}.yaml"
        with open(path, encoding="utf-8") as f:
            current = yaml.safe_load(f) or {}
        ov = {k: v for k, v in ov.items() if k not in ("r_r", "r_o", "r_a")}
        merged = deep_merge(current, ov)
        merged.update(radii)
        updated.append(str(path))
        if not dry_run:
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(merged, f, sort_keys=False, default_flow_style=False)
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        default=ROOT / "results" / "calibration_report_real.json",
        help="Real calibration report (default: results/calibration_report_real.json)",
    )
    parser.add_argument("--trials", type=int, default=100, help="CMA-ES evaluations per behavior")
    parser.add_argument("--n-seeds", type=int, default=30, help="Seeds per group size")
    parser.add_argument(
        "--n-values",
        nargs="*",
        type=int,
        default=[20, 40, 100],
        help="Group sizes to simulate",
    )
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument(
        "--behaviors",
        nargs="*",
        default=None,
        help="Subset of behaviors to tune (default: all in target report)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Quick loop: 12 trials, 8 seeds, N in {20}",
    )
    parser.add_argument(
        "--apply-best",
        action="store_true",
        help="Write results/tuning/feature_match/best.json overrides to configs/behaviors/*.yaml",
    )
    parser.add_argument(
        "--set-radii",
        action="store_true",
        help="Write --r-r/--r-o/--r-a into configs/behaviors/*.yaml and exit",
    )
    parser.add_argument("--r-r", type=float, default=DEFAULT_RADII["r_r"], help="Fixed repulsion radius")
    parser.add_argument("--r-o", type=float, default=DEFAULT_RADII["r_o"], help="Fixed orientation radius")
    parser.add_argument("--r-a", type=float, default=DEFAULT_RADII["r_a"], help="Fixed attraction radius")
    parser.add_argument("--dry-run", action="store_true", help="With --apply-best, print paths only")
    args = parser.parse_args()

    if args.set_radii:
        for p in write_radii_to_yamls(args.r_r, args.r_o, args.r_a):
            print(f"Updated radii: {p}")
        print(f"radii r_r={args.r_r} r_o={args.r_o} r_a={args.r_a}")
        return

    if args.apply_best:
        paths = apply_best_to_yaml(
            dry_run=args.dry_run,
            r_r=args.r_r,
            r_o=args.r_o,
            r_a=args.r_a,
        )
        verb = "Would update" if args.dry_run else "Updated"
        for p in paths:
            print(f"{verb}: {p}")
        return

    n_trials = args.trials
    n_seeds = args.n_seeds
    n_values = list(args.n_values)
    if args.fast:
        n_trials = min(n_trials, 12)
        n_seeds = min(n_seeds, 8)
        n_values = [20]

    summary = tune_all_behaviors(
        args.target,
        behaviors=args.behaviors,
        n_trials=n_trials,
        n_seeds=n_seeds,
        n_values=n_values,
        n_jobs=args.n_jobs,
    )

    _print_feature_summary(summary)

    print(f"\nBest config: {BEST_PATH}")
    print("Apply with: python scripts/tune_features.py --apply-best")


if __name__ == "__main__":
    main()
