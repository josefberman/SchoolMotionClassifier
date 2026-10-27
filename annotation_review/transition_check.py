"""Where does the actual crossing happen relative to each annotated transition segment?"""
import numpy as np, pandas as pd
from scipy.ndimage import uniform_filter1d
from common import IDS, REVIEW, load_cache
s = pd.read_csv(REVIEW/"segment_review.csv", dtype={"dataset": str})
RAD = {"expansion", "compaction"}
rows = []
for ds in IDS:
    c = load_cache(ds); fps = float(c["fps"]); T = len(c["phi_trans"])
    P = uniform_filter1d(c["phi_trans"], 15); M = uniform_filter1d(np.nan_to_num(c["M_tun"]), 15)
    rate = uniform_filter1d(np.gradient(np.log(uniform_filter1d(c["R"], 5))) * fps, 15)
    score = {"traveling": P - 0.5, "milling": M - 0.5, "shoaling": 0.5 - np.maximum(P, M), "expansion": rate, "compaction": -rate}
    for _, r in s[(s.dataset == ds) & s.label.str.contains("_to_")].iterrows():
        A, B = r.label.split("_to_")
        # the variable that should cross: B's score going up (if B is radial or both are states), else A's going down
        z, want = (score[B], 1) if (B in RAD or A not in RAD) else (score[A], -1)
        w = int(3*fps); a0, a1 = max(0, r.start - w), min(T - 1, r.end + w)
        zz = z[a0:a1+1]; cr = np.where(np.diff(np.sign(zz)) == 2*want)[0] + a0 + 1
        if len(cr) == 0: pos, off = "no_crossing_within_3s", np.nan
        else:
            mid = (r.start + r.end)/2; x = cr[np.argmin(np.abs(cr - mid))]
            if r.start - 7 <= x <= r.end + 7: pos, off = "inside", 0       # ±0.25 s = annotation time resolution
            elif x < r.start: pos, off = "before", (x - r.start)/fps
            else: pos, off = "after", (x - r.end)/fps
        rows.append(dict(dataset=ds, seg=r.seg, label=r.label, start=r.start, end=r.end, dur_s=r.dur_s, crossing=pos, offset_s=round(off, 2) if off == off else np.nan))
d = pd.DataFrame(rows); d.to_csv(REVIEW/"transition_crossings.csv", index=False)
print(d.crossing.value_counts().to_dict())
print(d.groupby("crossing").offset_s.median())
print(pd.crosstab(d.label, d.crossing))
