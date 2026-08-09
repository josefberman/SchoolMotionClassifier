#!/usr/bin/env python3
"""Generate sims × 6 behaviours × 6 group sizes with train/test split."""

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
from src.sim.render import render_simulation
from src.sim.validate import summarize_metrics, validate_behavior

N_VALUES = [10, 30, 50, 100, 200]
N_SEEDS = 200
TEST_FRAC = 0.2


def _test_seed_start(n_seeds: int) -> int:
    return int(n_seeds * (1.0 - TEST_FRAC))


def _overrides_for(behavior: str, seed: int) -> dict:
    ov: dict = {}
    if behavior == "milling":
        # even seeds: unidirectional, odd seeds: bidirectional
        if seed % 2 == 1:
            ov["bidirectional_frac"] = 0.5
            ov["cross_align_scale"] = 0.05
            ov["w_circ"] = 2.0
        else:
            ov["bidirectional_frac"] = 0.0
            ov["cross_align_scale"] = 1.0
            ov["w_circ"] = 2.5
    return ov


def _event_window(behavior: str) -> tuple[int | None, int | None]:
    return None, None


def generate_one(
    behavior: str,
    n: int,
    seed: int,
    out_root: Path,
    max_retries: int = 4,
    *,
    test_seed_start: int,
    render: bool = False,
    video: bool = False,
) -> dict:
    split = "test" if seed >= test_seed_start else "train"

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
            fps = 30.0
            label_raw = {
                "traveling_polarized": "polarized",
                "milling": "milling",
                "swarming": "swarming",
                "fountain_evasion": "fountain",
                "expansion_burst": "burst",
                "compaction": "compaction",
            }[behavior]
            es, ee = _event_window(behavior)
            if es is not None:
                segments = [
                    {
                        "start": _frame_to_mmss(es, fps),
                        "end": _frame_to_mmss(ee, fps),
                        "label": label_raw,
                    }
                ]
            else:
                segments = [
                    {
                        "start": "00:00",
                        "end": _frame_to_mmss(result.positions.shape[0], fps),
                        "label": label_raw,
                    }
                ]
            save_motion_json(json_path, dataset=stem, fps=fps, segments=segments, source="simulation")
            render_info = None
            if render:
                render_info = render_simulation(
                    result.positions,
                    result.velocities,
                    csv_path.parent / "renders",
                    stem=stem,
                    behavior=behavior,
                    fps=fps,
                    title=behavior.replace("_", " "),
                    video=video,
                    stills=True,
                )
            ev_s, ev_e = _event_window(behavior)
            entry = {
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
            if render_info is not None:
                entry["renders"] = render_info
            return entry
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
    parser.add_argument(
        "--render",
        action="store_true",
        help="Save manuscript stills (PNG) under each clip's renders/",
    )
    parser.add_argument(
        "--video",
        action="store_true",
        help="Also write MP4/GIF (implies --render). Slow for large batches.",
    )
    parser.add_argument(
        "--render-seeds",
        nargs="*",
        type=int,
        default=None,
        help="Only render these seeds (default: all when --render). Example: 0",
    )
    args = parser.parse_args()

    behaviors = args.behaviors
    n_values = args.n_values
    n_seeds = args.seeds
    if args.smoke:
        n_values = [10, 30]
        n_seeds = 2
    do_video = bool(args.video)
    do_render = bool(args.render or args.video)
    render_seeds = set(args.render_seeds) if args.render_seeds is not None else None
    test_seed_start = _test_seed_start(n_seeds)

    jobs = [(b, n, s) for b in behaviors for n in n_values for s in range(n_seeds)]
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(jobs)} simulations → {args.out}  (test seeds >= {test_seed_start})")
    results = Parallel(n_jobs=args.n_jobs, verbose=0)(
        delayed(generate_one)(
            b,
            n,
            s,
            args.out,
            test_seed_start=test_seed_start,
            render=do_render and (render_seeds is None or s in render_seeds),
            video=do_video and (render_seeds is None or s in render_seeds),
        )
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
