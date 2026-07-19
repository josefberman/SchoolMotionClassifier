#!/usr/bin/env python3
"""Quick calibration smoke: run a few sims and print order-parameter signatures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.labels import CANONICAL
from src.sim.model_fast import run_simulation_fast
from src.sim.validate import summarize_metrics, validate_behavior


def main() -> None:
    report = {}
    for behavior in CANONICAL:
        rows = []
        for n in (20, 40):
            for seed in (0, 1, 2):
                ov = {}
                if behavior == "milling" and seed == 2:
                    ov = {"bidirectional_frac": 0.45, "cross_align_scale": 0.15, "w_circ": 0.35}
                res = run_simulation_fast(behavior, n, seed, overrides=ov)
                m = summarize_metrics(res.positions, res.velocities)
                ok = validate_behavior(behavior, m, res.positions, res.velocities)
                rows.append({"n": n, "seed": seed, "valid": ok, **{k: m[k] for k in m if k.endswith("_mean") or k in ("sigma_d_delta", "v_r_event")}})
        report[behavior] = rows
        n_ok = sum(1 for r in rows if r["valid"])
        print(f"{behavior}: {n_ok}/{len(rows)} valid")
        for r in rows:
            print(
                f"  N={r['n']} seed={r['seed']} valid={r['valid']} "
                f"φdir={r['phi_dir_mean']:.2f} |L|={abs(r['l_bar_mean']):.2f} "
                f"φrot={r['phi_rot_mean']:.2f} φtan={r['phi_tan_mean']:.2f} "
                f"vr={r['v_r_bar_mean']:.2f} σd={r['sigma_d_mean']:.1f}"
            )

    out = ROOT / "results" / "calibration_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
