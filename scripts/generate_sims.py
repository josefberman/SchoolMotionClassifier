#!/usr/bin/env python3
"""Generate sims × 5 behaviours × group sizes with train/test split."""

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
from src.sim.config import deep_merge
from src.sim.io import save_motion_json, save_trajectory_csv
from src.sim.model_fast import run_simulation_fast, run_transition_fast
from src.sim.render import render_simulation
from src.sim.validate import metrics_for_validation, validate_behavior

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


def _event_window(behavior: str, n_frames: int = 150) -> tuple[int | None, int | None]:
    """Frame slice [start, end) for threat-event features within a recorded clip."""
    if behavior == "expansion_burst":
        return int(0.20 * n_frames), min(n_frames, int(0.93 * n_frames))
    if behavior == "compaction":
        return int(0.20 * n_frames), min(n_frames, int(0.95 * n_frames))
    return None, None


_LABEL_RAW = {
    "traveling_polarized": "polarized",
    "milling": "milling",
    "swarming": "swarming",
    "expansion_burst": "e+",
    "compaction": "e-",
}


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
    behavior_overrides: dict[str, dict] | None = None,
) -> dict:
    split = "test" if seed >= test_seed_start else "train"

    last_err = None
    for attempt in range(max_retries):
        use_seed = seed + attempt * 10007
        ov = _overrides_for(behavior, seed)
        if behavior_overrides and behavior in behavior_overrides:
            ov = deep_merge(ov, behavior_overrides[behavior])
        try:
            result = run_simulation_fast(behavior, n, use_seed, overrides=ov)
        except Exception as e:
            last_err = str(e)
            continue
        fps = 30.0
        n_frames = int(result.positions.shape[0])
        es, ee = _event_window(behavior, n_frames)
        metrics = metrics_for_validation(
            behavior,
            result.positions,
            result.velocities,
            event_start=es,
            event_end=ee,
        )
        ok = validate_behavior(behavior, metrics, result.positions, result.velocities)
        if ok or attempt == max_retries - 1:
            rel_dir = Path(behavior) / f"N{n}"
            stem = f"seed{seed:03d}"
            csv_rel = rel_dir / f"{stem}_loc_vel_data.csv"
            json_rel = rel_dir / f"{stem}_motion.json"
            csv_path = out_root / csv_rel
            json_path = out_root / json_rel
            save_trajectory_csv(csv_path, result.positions, result.velocities)
            label_raw = _LABEL_RAW[behavior]
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
                        "end": _frame_to_mmss(n_frames, fps),
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
            entry = {
                "behavior": behavior,
                "n": n,
                "seed": seed,
                "split": split,
                "valid": bool(ok),
                "csv": str(csv_rel).replace("\\", "/"),
                "motion_json": str(json_rel).replace("\\", "/"),
                "fps": fps,
                "event_start": es,
                "event_end": ee,
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


def generate_one_transition(
    behavior_from: str,
    behavior_to: str,
    n: int,
    seed: int,
    out_root: Path,
    *,
    test_seed_start: int,
    total_frames: int = 300,
    render: bool = False,
    video: bool = False,
) -> dict:
    label = f"{behavior_from}_to_{behavior_to}"
    split = "test" if seed >= test_seed_start else "train"
    try:
        result = run_transition_fast(
            behavior_from, behavior_to, n, seed,
            total_frames=total_frames,
        )
    except Exception as e:
        return {
            "behavior": label,
            "n": n,
            "seed": seed,
            "split": split,
            "valid": False,
            "error": str(e),
        }

    fps = 30.0
    rel_dir = Path(label) / f"N{n}"
    stem = f"seed{seed:03d}"
    csv_rel = rel_dir / f"{stem}_loc_vel_data.csv"
    json_rel = rel_dir / f"{stem}_motion.json"
    csv_path = out_root / csv_rel
    json_path = out_root / json_rel
    save_trajectory_csv(csv_path, result.positions, result.velocities)

    morph_start = result.meta.get("morph_start", int(total_frames * 0.3))
    morph_end = result.meta.get("morph_end", int(total_frames * 0.7))
    segments = [
        {
            "start": _frame_to_mmss(0, fps),
            "end": _frame_to_mmss(morph_start, fps),
            "label": _LABEL_RAW.get(behavior_from, behavior_from),
        },
        {
            "start": _frame_to_mmss(morph_start, fps),
            "end": _frame_to_mmss(morph_end, fps),
            "label": label,
        },
        {
            "start": _frame_to_mmss(morph_end, fps),
            "end": _frame_to_mmss(total_frames, fps),
            "label": _LABEL_RAW.get(behavior_to, behavior_to),
        },
    ]
    save_motion_json(json_path, dataset=stem, fps=fps, segments=segments, source="simulation")

    render_info = None
    if render:
        render_info = render_simulation(
            result.positions,
            result.velocities,
            csv_path.parent / "renders",
            stem=stem,
            behavior=label,
            fps=fps,
            title=label.replace("_", " "),
            video=video,
            stills=True,
        )

    entry = {
        "behavior": label,
        "behavior_from": behavior_from,
        "behavior_to": behavior_to,
        "n": n,
        "seed": seed,
        "split": split,
        "valid": True,
        "csv": str(csv_rel).replace("\\", "/"),
        "motion_json": str(json_rel).replace("\\", "/"),
        "fps": fps,
        "morph_start": morph_start,
        "morph_end": morph_end,
        "event_start": None,
        "event_end": None,
        "attempts": 1,
    }
    if render_info is not None:
        entry["renders"] = render_info
    return entry


def _frame_to_mmss(frame: int, fps: float) -> str:
    total = int(frame / fps)
    m, s = divmod(total, 60)
    return f"{m:02d}:{s:02d}"


def generate_batch(
    out_root: Path,
    *,
    behaviors: list[str] | None = None,
    n_values: list[int] | None = None,
    n_seeds: int = N_SEEDS,
    n_jobs: int = -1,
    behavior_overrides: dict[str, dict] | None = None,
    render: bool = False,
    video: bool = False,
    render_seeds: set[int] | None = None,
    show_progress: bool = True,
    include_transitions: bool = False,
    transition_seeds: int | None = None,
    transition_n_values: list[int] | None = None,
) -> list[dict]:
    """Generate simulations and write manifest.json under out_root."""
    behaviors = behaviors or list(CANONICAL)
    n_values = n_values or list(N_VALUES)
    test_seed_start = _test_seed_start(n_seeds)
    jobs = [(b, n, s) for b in behaviors for n in n_values for s in range(n_seeds)]
    out_root.mkdir(parents=True, exist_ok=True)

    iterator = tqdm(jobs, desc="sims") if show_progress else jobs
    results = Parallel(n_jobs=n_jobs, verbose=0)(
        delayed(generate_one)(
            b,
            n,
            s,
            out_root,
            test_seed_start=test_seed_start,
            render=render and (render_seeds is None or s in render_seeds),
            video=video and (render_seeds is None or s in render_seeds),
            behavior_overrides=behavior_overrides,
        )
        for b, n, s in iterator
    )

    if include_transitions:
        t_seeds = transition_seeds if transition_seeds is not None else n_seeds
        t_nvals = transition_n_values or n_values
        t_test_start = _test_seed_start(t_seeds)
        base_behaviors = [b for b in behaviors if b in CANONICAL]
        t_jobs = [
            (a, b, n, s)
            for a in base_behaviors
            for b in base_behaviors
            if a != b
            for n in t_nvals
            for s in range(t_seeds)
        ]
        t_iter = tqdm(t_jobs, desc="transitions") if show_progress else t_jobs
        t_results = Parallel(n_jobs=n_jobs, verbose=0)(
            delayed(generate_one_transition)(
                a, b, n, s, out_root,
                test_seed_start=t_test_start,
                render=render and (render_seeds is None or s in render_seeds),
                video=video and (render_seeds is None or s in render_seeds),
            )
            for a, b, n, s in t_iter
        )
        results.extend(t_results)

    manifest_path = out_root / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")
    return results


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
    parser.add_argument(
        "--transitions",
        action="store_true",
        help="Also generate X→Y transition clips for every ordered pair of base behaviors "
        "(5 baselines → 20 transition types, including stable↔expansion/compaction)",
    )
    parser.add_argument(
        "--transition-seeds",
        type=int,
        default=None,
        help="Number of seeds for transition clips (default: same as --seeds)",
    )
    parser.add_argument(
        "--transition-n-values",
        nargs="*",
        type=int,
        default=None,
        help="Group sizes for transition clips (default: same as --n-values)",
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

    args.out.mkdir(parents=True, exist_ok=True)

    results = generate_batch(
        args.out,
        behaviors=behaviors,
        n_values=n_values,
        n_seeds=n_seeds,
        n_jobs=args.n_jobs,
        render=do_render,
        video=do_video,
        render_seeds=render_seeds,
        include_transitions=args.transitions,
        transition_seeds=args.transition_seeds,
        transition_n_values=args.transition_n_values,
    )

    manifest_path = args.out / "manifest.json"
    n_ok = sum(1 for r in results if r.get("valid"))
    n_trans = sum(1 for r in results if "_to_" in r.get("behavior", ""))
    print(f"Done. valid={n_ok}/{len(results)}  transitions={n_trans}  manifest={manifest_path}")


if __name__ == "__main__":
    main()
