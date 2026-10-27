"""Merge transition-crossing check into segment_review.csv and build a human-readable suggestion column."""
import numpy as np, pandas as pd
from common import REVIEW
s = pd.read_csv(REVIEW/"segment_review.csv", dtype={"dataset": str})
s = s.drop(columns=[c for c in ("transition_crossing", "transition_crossing_offset_s", "suggestion", "evidence", "boundary_verdict") if c in s.columns])
t = pd.read_csv(REVIEW/"transition_crossings.csv", dtype={"dataset": str})[["dataset", "seg", "crossing", "offset_s"]]
t = t.rename(columns={"crossing": "transition_crossing", "offset_s": "transition_crossing_offset_s"})
s = s.merge(t, on=["dataset", "seg"], how="left")
SH = {"traveling": "tpol", "milling": "mill", "shoaling": "shoal", "expansion": "exp", "compaction": "comp"}
def short(l): return "→".join(SH.get(x, x) for x in l.split("_to_"))
def evidence(r):
    ev = f"P {r.P:.2f}, M {r.M:.2f}, pol/mill/swarm {r.frac_pol:.0%}/{r.frac_mill:.0%}/{r.frac_swarm:.0%}; dlogR {r.dlogR:+.2f}, hull {r.dlogHull:+.2f}, vrad {r.vrad_norm:+.2f}, Φrad {r.phi_rad_pm:+.2f}; sim≈{SH.get(r.sim_nearest, r.sim_nearest)}"
    if "_to_" in r.label and isinstance(r.transition_crossing, str): ev += f"; crossing {r.transition_crossing}" + (f" {r.transition_crossing_offset_s:+.1f}s" if r.transition_crossing in ("before", "after") else "")
    return ev
def suggestion(r):
    out = []
    if r.verdict != "agree" and "_to_" not in r.label and r.label in SH and r.label not in ("expansion", "compaction"):
        if r.suggested_state == "mixed": out.append("intermediate regime: keep only if you accept weak " + SH[r.label] + ", else mark 'mixed/unclear'")
        elif r.suggested_state != r.label: out.append(f"relabel → {r.suggested_state}")
    if r.label in ("expansion", "compaction") and r.verdict != "agree": out.append("radial evidence weak; check video")
    if isinstance(r.evt_unannotated_inside, str) and r.evt_unannotated_inside: out.append("split out: " + r.evt_unannotated_inside)
    if "_to_" in r.label and r.transition_crossing in ("before", "after"):
        out.append(f"state change happens {abs(r.transition_crossing_offset_s):.1f}s {r.transition_crossing} this transition → move it")
    if "_to_" in r.label and r.transition_crossing == "no_crossing_within_3s": out.append("no state change found within ±3 s")
    for side in ("start", "end"):
        st, off, fr = r[f"{side}_status"], r[f"{side}_offset_s"], r[f"{side}_suggested"]
        if st == "shift_suggested": out.append(f"{side} → {int(fr)} ({off:+.1f}s, 2 methods)")
        elif str(st).startswith("shift_possible") and abs(off) >= 1.0: out.append(f"{side} maybe → {int(fr)} ({off:+.1f}s, 1 method)")
    if r.dur_s < 1.0: out.append("<1 s: ≤6 windows")
    return "; ".join(out)
def bverdict(r):
    sts = [r.start_status, r.end_status]
    if "_to_" in r.label and r.transition_crossing in ("before", "after") and abs(r.transition_crossing_offset_s) > 0.5: return "shift"
    if "shift_suggested" in sts: return "shift"
    if any(str(x).startswith("shift_possible") for x in sts) and max(abs(r.start_offset_s), abs(r.end_offset_s)) >= 1.0: return "possible_shift"
    if all(x == "supported" for x in sts): return "ok"
    if any(x == "supported" for x in sts): return "ok_one_side"
    return "unclear"
s["boundary_verdict"] = s.apply(bverdict, axis=1)
s["evidence"] = s.apply(evidence, axis=1); s["suggestion"] = s.apply(suggestion, axis=1)
lead = ["dataset", "group", "seg", "raw_label", "label", "start_str", "end_str", "start", "end", "n_frames", "dur_s", "verdict", "boundary_verdict", "reason", "evidence", "suggestion"]
s = s[lead + [c for c in s.columns if c not in lead]]
s.to_csv(REVIEW/"segment_review.csv", index=False)
print(s.verdict.value_counts().to_dict(), s.boundary_verdict.value_counts().to_dict())
