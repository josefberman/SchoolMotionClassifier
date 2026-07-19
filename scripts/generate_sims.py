#!/usr/bin/env python3
"""Generate 100 sims × 6 behaviours × 6 group sizes with train/test split."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from joblib import Parallel, delayed
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.labels import BEHAVIOR_SHORT, CANONICAL
from src.sim.io import save_motion_json, save_trajectory_csv
from src.sim.model_fast import run_simulation_fast
from src.sim.validate import summarize_metrics, validate_behavior

N_VALUES = [10, 20, 30, 40, 100, 200]
N_SEEDS = 100
TEST_FRAC = 0.2


def _overrides_for(behavior: str, seed: int) -> dict:
    ov: dict = {}
    if behavior == "milling":
        # ~20% bidirectional mills
        if seed % 5 == 0:
            ov["bidirectional_frac"] = 0.5
            ov["cross_align_scale"] = 0.1
            ov["w_circ"] = 0.9
        else:
            ov["bidirectional_frac"] = 0.0
            ov["cross_align_scale"] = 1.0
            ov["w_circ"] = 1.2
    return ov


def _event_window(behavior: str) -> tuple[int | None, int | None]:
    if behavior == "fountain_evasion":
        return 100, 300
    if behavior == "expansion_burst":
        return 120, 260
    if behavior == "compaction":
        return 120, 320
    return None, None


def generate_one(behavior: str, n: int, seed: int, out_root: Path, max_retries: int = 4) -> dict:
    short = BEHAVIOR_SHORT[behavior]
    split = "test" if seed >= int(N_SEEDS * (1 - TEST_FRAC)) else "train"
    # seeds 80-99 test (20%), 0-79 train
    split = "test" if seed >= 80 else "train"

    last_err = None
    for attempt in range(max_retries):
        use_seed = seed + attempt * 10007
        ov = _overrides_for(behavior, seed)
        try:
            result = run_simulation_fast(behavior, n, use_seed, overrides=ov)
        except Exception as e:
            last_err = str(e)
            continue
        metrics = summarize_metrics(result.positions, result.velocities)
        ok = validate_behavior(behavior, metrics, result.positions, result.velocities)
        if ok or attempt == max_retries - 1:
            rel_dir = Path(behavior) / f"N{n}"
            stem = f"seed{seed:03d}"
            csv_rel = rel_dir / f"{stem}_loc_vel_data.csv"
            json_rel = rel_dir / f"{stem}_motion.json"
            csv_path = out_root / csv_rel
            json_path = out_root / json_rel
            save_trajectory_csv(csv_path, result.positions, result.velocities)
            es, ee = _event_window(behavior)
            fps = 30.0
            if es is not None:
                segments = [
                    {
                        "start": _frame_to_mmss(es, fps),
                        "end": _frame_to_mmss(ee, fps),
                        "label": short if short != "tpol" else "polarized",
                    }
                ]
                # Use canonical-friendly raw labels matching annotations style
                label_raw = {
                    "traveling_polarized": "polarized",
                    "milling": "milling",
                    "swarming": "swarming",
                    "fountain_evasion": "fountain",
                    "expansion_burst": "burst",
                    "compaction": "compaction",
                }[behavior]
                segments[0]["label"] = label_raw
            else:
                label_raw = {
                    "traveling_polarized": "polarized",
                    "milling": "milling",
                    "swarming": "swarming",
                    "fountain_evasion": "fountain",
                    "expansion_burst": "burst",
                    "compaction": "compaction",
                }[behavior]
                segments = [
                    {
                        "start": "00:00",
                        "end": _frame_to_mmss(result.positions.shape[0], fps),
                        "label": label_raw,
                    }
                ]
            save_motion_json(json_path, dataset=stem, fps=fps, segments=segments, source="simulation")
            ev_s, ev_e = _event_window(behavior)
            return {
                "behavior": behavior,
                "n": n,
                "seed": seed,
                "split": split,
                "valid": bool(ok),
                "csv": str(csv_rel).replace("\\", "/"),
                "motion_json": str(json_rel).replace("\\", "/"),
                "fps": fps,
                "event_start": ev_s,
                "event_end": ev_e,
                "metrics": metrics,
                "attempts": attempt + 1,
            }
    return {
        "behavior": behavior,
        "n": n,
        "seed": seed,
        "split": split,
        "valid": False,
        "error": last_err,
    }


def _frame_to_mmss(frame: int, fps: float) -> str:
    total = int(frame / fps)
    m, s = divmod(total, 60)
    return f"{m:02d}:{s:02d}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "sim_datasets")
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--behaviors", nargs="*", default=list(CANONICAL))
    parser.add_argument("--n-values", nargs="*", type=int, default=N_VALUES)
    parser.add_argument("--seeds", type=int, default=N_SEEDS)
    parser.add_argument("--smoke", action="store_true", help="Tiny run: 2 seeds × 2 N × all behaviours")
    args = parser.parse_args()

    behaviors = args.behaviors
    n_values = args.n_values
    n_seeds = args.seeds
    if args.smoke:
        n_values = [10, 30]
        n_seeds = 2

    jobs = [(b, n, s) for b in behaviors for n in n_values for s in range(n_seeds)]
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(jobs)} simulations → {args.out}")
    results = Parallel(n_jobs=args.n_jobs, verbose=0)(
        delayed(generate_one)(b, n, s, args.out)
        for b, n, s in tqdm(jobs, desc="sims")
    )

    manifest_path = args.out / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")

    n_ok = sum(1 for r in results if r.get("valid"))
    print(f"Done. valid={n_ok}/{len(results)}  manifest={manifest_path}")


if __name__ == "__main__":
    main()
