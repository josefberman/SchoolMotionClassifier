#!/usr/bin/env python3
"""Render publication-style stills/videos from simulated (or real) trajectories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.labels import CANONICAL
from src.sim.io import load_trajectory_csv
from src.sim.render import render_simulation


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim-root", type=Path, default=ROOT / "sim_datasets")
    p.add_argument("--manifest", type=Path, default=None)
    p.add_argument("--behaviors", nargs="*", default=None)
    p.add_argument("--n-values", nargs="*", type=int, default=[30])
    p.add_argument("--seeds", nargs="*", type=int, default=[0])
    p.add_argument("--video", action="store_true", help="Also write MP4/GIF")
    p.add_argument("--no-stills", action="store_true")
    p.add_argument("--stride", type=int, default=1, help="Video frame stride")
    p.add_argument(
        "--manuscript",
        action="store_true",
        help="One representative clip per behaviour (N=30, seed=0) into results/figures/",
    )
    args = p.parse_args()

    if args.manuscript:
        out_root = ROOT / "results" / "figures"
        jobs = []
        for b in CANONICAL:
            csv = args.sim_root / b / "N30" / "seed000_loc_vel_data.csv"
            if csv.exists():
                jobs.append((b, csv, out_root / b))
            else:
                # fall back to any available N
                matches = sorted((args.sim_root / b).glob("N*/seed000_loc_vel_data.csv"))
                if matches:
                    jobs.append((b, matches[0], out_root / b))
        if not jobs:
            print("No simulations found. Run scripts/generate_sims.py first.")
            sys.exit(1)
        for b, csv, out_dir in tqdm(jobs, desc="manuscript figures"):
            pos, vel = load_trajectory_csv(csv)
            # No on-figure title: label in the paper caption instead
            info = render_simulation(
                pos,
                vel,
                out_dir,
                stem="fig",
                behavior=b,
                title=None,
                video=args.video,
                stills=not args.no_stills,
                video_stride=args.stride,
            )
            print(b, info)
        return

    manifest_path = args.manifest or (args.sim_root / "manifest.json")
    if not manifest_path.exists():
        print(f"Missing manifest: {manifest_path}")
        sys.exit(1)
    entries = json.loads(manifest_path.read_text())
    behaviors = set(args.behaviors) if args.behaviors else None
    n_set = set(args.n_values)
    seed_set = set(args.seeds)

    selected = [
        e
        for e in entries
        if e.get("valid", True)
        and e.get("n") in n_set
        and e.get("seed") in seed_set
        and (behaviors is None or e.get("behavior") in behaviors)
    ]
    print(f"Rendering {len(selected)} clips")
    for e in tqdm(selected, desc="render"):
        csv = args.sim_root / e["csv"]
        if not csv.exists():
            continue
        pos, vel = load_trajectory_csv(csv)
        out_dir = csv.parent / "renders"
        render_simulation(
            pos,
            vel,
            out_dir,
            stem=Path(e["csv"]).stem.replace("_loc_vel_data", ""),
            behavior=e["behavior"],
            title=e["behavior"].replace("_", " "),
            fps=float(e.get("fps", 30.0)),
            video=args.video,
            stills=not args.no_stills,
            video_stride=args.stride,
        )


if __name__ == "__main__":
    main()
