"""Post-process: attach data-detected radial events to segments, final verdict, write segment_review.csv."""
import numpy as np, pandas as pd
from common import REVIEW
s = pd.read_csv(REVIEW/"segment_review.csv", dtype={"dataset": str})
if "verdict_metrics_only" in s.columns:   # idempotent re-run
    s["verdict"] = s["verdict_metrics_only"]; s = s.drop(columns=[c for c in s.columns if c.startswith("evt_")] + ["verdict_metrics_only"])
e = pd.read_csv(REVIEW/"radial_events.csv", dtype={"dataset": str})
e["robust"] = ((e.frac_fish_moving_with_event >= 0.6) & (np.sign(e.dlogNND) == np.sign(e.dlogR))
               & (np.sign(e.dlog_median_dist) == np.sign(e.dlogR)) & (e.jumps_in_event == 0))
e["strong"] = e.dlogR.abs() >= 0.29          # = median |dlogR| of annotated compaction segments
e["unannotated"] = e.frac_covered_by_matching_label < 0.2
# isotropic = both principal axes change in the event direction (vs. elongation/reshaping along one axis)
sg = np.sign(e.dlogR)
e["shape_change"] = np.where((np.sign(e.dlog_major) == sg) & (np.sign(e.dlog_minor) == sg), "isotropic", "anisotropic(reshaping)")
e.to_csv(REVIEW/"radial_events.csv", index=False)
miss = e[e.robust & e.strong & e.unannotated]
# Re-check exp/comp segments downgraded for tracking artefacts with outlier-robust measures
from common import load_ds
cache = {}
s["robust_dlog_median_dist"] = np.nan; s["robust_frac_fish_with_label"] = np.nan
for i, r in s[s.notes.fillna("").str.contains("downgraded: radial")].iterrows():
    if r.dataset not in cache: cache[r.dataset] = load_ds(r.dataset)
    pos, vel, _ = cache[r.dataset]; a, b = r.start, r.end
    q_ = pos[a:b] - pos[a:b].mean(1, keepdims=True); u_ = vel[a:b] - np.nanmean(vel[a:b], 1, keepdims=True)
    md = np.median(np.linalg.norm(q_, axis=-1), 1); dl = float(np.log(md[-5:].mean()/md[:5].mean()))
    ur = np.nanmean((u_*q_).sum(-1)/np.maximum(np.linalg.norm(q_, axis=-1), 1e-9), 0)
    sg = 1 if r.label == "expansion" else -1; fr = float(np.mean(sg*ur > 0))
    s.at[i, "robust_dlog_median_dist"] = round(dl, 3); s.at[i, "robust_frac_fish_with_label"] = round(fr, 2)
    if sg*dl >= 0.05 and fr >= 0.6:
        s.at[i, "verdict"] = "agree"
        s.at[i, "notes"] = r.notes.replace("downgraded: radial change coincides with tracking artefacts",
                                           f"tracking teleports present but radial change robust (median-dist dlog {dl:+.2f}, {fr:.0%} fish)")
    else:
        s.at[i, "notes"] = r.notes + f" (robust check failed: median-dist dlog {dl:+.2f}, {fr:.0%} fish)"
s["verdict_metrics_only"] = s.verdict
s["evt_unannotated_inside"] = ""; s["evt_n"] = 0
for i, r in s.iterrows():
    if r.label not in ("traveling", "shoaling", "milling") and "_to_" not in r.label: continue
    m = miss[(miss.dataset == r.dataset) & (miss.start < r.end) & (miss.end > r.start)]
    m = m[[min(r.end, x.end) - max(r.start, x.start) >= 0.5*(x.end - x.start) for _, x in m.iterrows()]] if len(m) else m
    if len(m) == 0: continue
    s.at[i, "evt_n"] = len(m)
    s.at[i, "evt_unannotated_inside"] = "; ".join(f"{x.kind} {x.start}-{x.end} (dlogR {x.dlogR:+.2f}, {x.dur_s}s, {x.shape_change})" for _, x in m.iterrows())
    if s.at[i, "verdict"] == "agree" and "_to_" not in r.label:
        s.at[i, "verdict"] = "questionable"
        s.at[i, "notes"] = (str(r.notes) + "; " if isinstance(r.notes, str) and r.notes else "") + "contains unannotated expansion/compaction event(s)"
s.to_csv(REVIEW/"segment_review.csv", index=False)
print(s.verdict.value_counts().to_dict(), "segments with missed events:", (s.evt_n > 0).sum(), "missed events:", len(miss))
