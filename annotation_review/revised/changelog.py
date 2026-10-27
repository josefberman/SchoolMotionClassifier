"""Final per-segment change table (changes.csv), loader validation, CHANGELOG.md."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from common import IDS, REVIEW, ROOT, META
from src.labels import canonicalize, load_aliases, ALL_LABELS
from src.sim.io import load_motion_json, mmss_to_frame
from src.features.dataset import load_real_segments
OUT = REVIEW/"revised"
fin = pd.read_csv(OUT/"final_segments.csv", dtype={"dataset": str, "orig": str})
steps = pd.read_csv(OUT/"changes_steps.csv", dtype={"dataset": str, "old_seg": str})
rad = pd.read_csv(OUT/"radial_recheck.csv", dtype={"dataset": str, "seg": str})
rev = pd.read_csv(REVIEW/"segment_review.csv", dtype={"dataset": str})
fin["orig"] = fin.orig.fillna("")
rows = []
for ds in IDS:
    ann = load_motion_json(ROOT/"annotations"/f"{ds}_motion.json"); fps = float(ann["fps"])
    F = fin[fin.dataset == ds]; St = steps[steps.dataset == ds]
    for i, x in enumerate(ann["segments"]):
        oa, ob = mmss_to_frame(x["start"], fps), mmss_to_frame(x["end"], fps); oc = canonicalize(x["label"])
        fs = F[F.orig.apply(lambda o: str(i) in o.split(";") if o else False)]
        st = St[St.old_seg.fillna("").apply(lambda o: str(i) in o.split(";"))]
        reasons = [r for r in st.reason.dropna().unique() if r and "adjacent segments with identical label" not in r]
        rr = rev[(rev.dataset == ds) & (rev.seg == i)].iloc[0]
        rc = rad[(rad.dataset == ds) & (rad.seg == str(i))]
        carved = [x for x in st.reason.dropna() if x.startswith("split around new ")]
        if len(fs) == 0 and carved:   # stable segment replaced by a strict exp/comp event carved out of it
            k, fr_ = carved[0].replace("split around new ", "").split(" ")
            typ = "relabel"; new = dict(new_label=k, new_frames=fr_ + " (remnants < 2 s left unlabelled)")
        elif len(fs) == 0:
            typ = "removed"; new = {}
        else:
            labs = set(fs.canon); merged = any(len(o.split(";")) > 1 for o in fs.orig)
            same_frames = len(fs) == 1 and fs.a.iloc[0] == oa and fs.b.iloc[0] == ob
            if labs != {oc}: typ = "relabel"
            elif len(fs) > 1: typ = "split"
            elif merged: typ = "merged"
            elif not same_frames: typ = "boundary_trim"
            else: typ = "unchanged"
            new = dict(new_seg=";".join(map(str, fs.new_seg)), new_label=" | ".join(fs.label), new_start=" | ".join(fs.start), new_end=" | ".join(fs.end),
                       new_frames=" | ".join(f"{a}-{b}" for a, b in zip(fs.a, fs.b)))
            if merged: new["merged_with_orig"] = ";".join(sorted({o for oo in fs.orig for o in oo.split(";")} - {str(i)}, key=int))
        flag = any(st.change.isin(["unchanged_flagged"]))
        rows.append(dict(dataset=ds, change_type=typ, flagged=flag, old_seg=i, old_label=x["label"], old_start=x["start"], old_end=x["end"],
                         old_frames=f"{oa}-{ob}", **new, reason=" / ".join(reasons),
                         old_P=round(rr.P, 3), old_M=round(rr.M, 3), old_dlogR=round(rr.dlogR, 3), old_verdict_v1=rr.verdict,
                         **({f"strict_{k}": (round(v, 3) if isinstance(v, float) else v) for k, v in rc.iloc[0][["decision", "peak_rate", "thr", "dlogR", "P_mean", "P_min", "frac_P065", "speed_ratio"]].items()} if len(rc) else {})))
    for _, f_ in F[F.orig == ""].iterrows():
        st = St[(St.change.isin(["new_event", "new_from_gap"])) & (St.new_frames == f"{f_.a}-{f_.b}")]
        rows.append(dict(dataset=ds, change_type="new_from_gap" if (len(st) and "inside gap" in st.reason.iloc[0]) or st.change.eq("new_from_gap").any() else "new_event_in_segment",
                         flagged=False, new_seg=str(f_.new_seg), new_label=f_.label, new_start=f_.start, new_end=f_.end, new_frames=f"{f_.a}-{f_.b}",
                         reason=st.reason.iloc[0] if len(st) else "", new_P=f_.P, new_M=f_.M))
ch = pd.DataFrame(rows); ch.to_csv(OUT/"changes.csv", index=False)
print(ch.change_type.value_counts().to_dict())
# ---------------- validation with the repo's own loader ----------------
aliases = load_aliases(); val = []
segs = load_real_segments(annotations_dir=OUT/"annotations", datasets_json=ROOT/"annotations"/"datasets.json")
for ds in IDS:
    j = json.loads((OUT/"annotations"/f"{ds}_motion.json").read_text()); o = json.loads((ROOT/"annotations"/f"{ds}_motion.json").read_text())
    assert list(j) == list(o) and j["fps"] == o["fps"] and j["source"] == o["source"] and j["dataset"] == o["dataset"]
    assert all(list(s) == ["start", "end", "label"] for s in j["segments"])
    canon = [canonicalize(s["label"], aliases) for s in j["segments"]]
    assert all(c in ALL_LABELS for c in canon) and not any("mixed" in s["label"] for s in j["segments"])
    fr = [(mmss_to_frame(s["start"], 29.97), mmss_to_frame(s["end"], 29.97)) for s in j["segments"]]
    assert all(b > a for a, b in fr) and all(fr[k][0] >= fr[k-1][1] for k in range(1, len(fr))), ds
    assert (OUT/"annotations"/f"{ds}_motion.json").read_text() == json.dumps(j, indent=2) + "\n"
    val.append(dict(dataset=ds, segments=len(j["segments"]), loaded_by_load_real_segments=sum(1 for s in segs if s["dataset"] == ds),
                    under_15_frames=sum(1 for a, b in fr if b - a < 15), raw_labels=len(set(s["label"] for s in j["segments"]))))
v = pd.DataFrame(val); v.to_csv(OUT/"validation.csv", index=False); print(v.to_string()); print("labels used:", sorted({s["label"] for s in segs}))
