#!/usr/bin/env python3
"""Tune behavior YAML overrides to maximize real eval accuracy / macro F1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml

from src.labels import BEHAVIOR_SHORT
from src.sim.config import CONFIG_DIR, deep_merge
from src.tune.pipeline import BEST_PATH, run_trial, tune_loop


def apply_best_to_yaml(best_path: Path | None = None, *, dry_run: bool = False) -> list[str]:
    """Merge best trial overrides into configs/behaviors/*.yaml."""
    best_path = best_path or BEST_PATH
    with open(best_path, encoding="utf-8") as f:
        best = json.load(f)
    overrides = best.get("behavior_overrides") or {}
    updated = []
    for behavior, ov in overrides.items():
        short = BEHAVIOR_SHORT[behavior]
        path = CONFIG_DIR / f"{short}.yaml"
        with open(path, encoding="utf-8") as f:
            current = yaml.safe_load(f) or {}
        merged = deep_merge(current, ov)
        updated.append(str(path))
        if not dry_run:
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(merged, f, sort_keys=False, default_flow_style=False)
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=10, help="Number of random-search trials")
    parser.add_argument("--n-seeds", type=int, default=40, help="Seeds per behavior (train+test split)")
    parser.add_argument(
        "--n-values",
        nargs="*",
        type=int,
        default=[10, 30, 50],
        help="Group sizes to simulate",
    )
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument(
        "--objective",
        choices=["real_macro_f1", "real_accuracy", "combined"],
        default="real_macro_f1",
    )
    parser.add_argument("--jitter", type=float, default=0.35, help="Local search radius around current best")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Quick loop: 3 trials, 16 seeds, N in {10,30}",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full loop: 200 seeds, N in {10,30,50,100,200}",
    )
    parser.add_argument(
        "--single-trial",
        action="store_true",
        help="Run one trial using configs/behaviors/*.yaml as overrides (baseline eval)",
    )
    parser.add_argument(
        "--apply-best",
        action="store_true",
        help="Write results/tuning/best.json overrides back to configs/behaviors/*.yaml",
    )
    parser.add_argument("--dry-run", action="store_true", help="With --apply-best, print paths only")
    args = parser.parse_args()

    if args.apply_best:
        paths = apply_best_to_yaml(dry_run=args.dry_run)
        verb = "Would update" if args.dry_run else "Updated"
        for p in paths:
            print(f"{verb}: {p}")
        return

    n_trials = args.trials
    n_seeds = args.n_seeds
    n_values = list(args.n_values)
    if args.fast:
        n_trials = min(n_trials, 3)
        n_seeds = min(n_seeds, 16)
        n_values = [10, 30]
    if args.full:
        n_seeds = 200
        n_values = [10, 30, 50, 100, 200]

    if args.single_trial:
        trial_dir = ROOT / "results" / "tuning" / "baseline"
        metrics = run_trial(
            trial_dir,
            {},
            n_seeds=n_seeds,
            n_values=n_values,
            n_jobs=args.n_jobs,
        )
        print(json.dumps(metrics, indent=2))
        return

    summary = tune_loop(
        n_trials=n_trials,
        n_seeds=n_seeds,
        n_values=n_values,
        n_jobs=args.n_jobs,
        objective=args.objective,
        jitter=args.jitter,
        show_progress=True,
    )
    print("\n=== tuning summary ===")
    print(json.dumps(summary, indent=2))
    if BEST_PATH.exists():
        print(f"\nBest config: {BEST_PATH}")
        print("Apply with: python scripts/tune_configs.py --apply-best")


if __name__ == "__main__":
    main()
