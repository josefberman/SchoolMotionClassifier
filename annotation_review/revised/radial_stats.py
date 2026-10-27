"""Event-level kinematics for annotated exp/comp segments and earlier 'missed' events."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from scipy.ndimage import uniform_filter1d
from common import IDS, REVIEW, load_cache
OUT = REVIEW/"revised"
def sm(x, w=15): return uniform_filter1d(np.nan_to_num(x, nan=np.nanmedian(x)), w, mode="nearest")
seg = pd.read_csv(REVIEW/"segment_review.csv", dtype={"dataset": str})
ev = pd.read_csv(REVIEW/"radial_events.csv", dtype={"dataset": str})
rows, tails = [], []
for ds in IDS:
    c = load_cache(ds); fps = float(c["fps"]); T = len(c["phi_trans"])
    P = sm(c["phi_trans"]); rate = sm(np.gradient(np.log(sm(c["R"], 5))) * fps)
    spd = sm(c["speed"], 5); vr = sm(c["vrad_norm"])
    base_spd = pd.Series(spd).rolling(int(5*fps), min_periods=1).median().to_numpy()   # trailing 5 s median speed
    tails.append(dict(dataset=ds, n_fish=int(c["n_fish"]), **{f"absrate_p{q}": float(np.quantile(np.abs(rate), q/100)) for q in (90, 95, 97.5, 99)},
                      P_median=float(np.median(P))))
    items = [("annot", r.label, r.seg, r.start, r.end) for _, r in seg[(seg.dataset == ds) & seg.label.isin(["expansion", "compaction"])].iterrows()]
    items += [("event", r.kind, i, r.start, r.end) for i, r in ev[(ev.dataset == ds) & ev.robust & ev.strong & ev.unannotated].iterrows()]
    for src, lab, sid, a, b in items:
        a, b = int(a), int(min(b, T)); sg = 1 if lab == "expansion" else -1
        pre = slice(max(0, a - int(fps)), a)
        rows.append(dict(dataset=ds, n_fish=int(c["n_fish"]), source=src, label=lab, id=sid, start=a, end=b, dur_s=(b-a)/fps,
                         peak_rate=float((sg*rate[a:b]).max()), mean_rate=float((sg*rate[a:b]).mean()),
                         dlogR=float(np.log(sm(c["R"],5)[b-1]/sm(c["R"],5)[a])),
                         P_mean=float(P[a:b].mean()), P_min=float(P[a:b].min()), P_pre=float(P[pre].mean()) if a > 0 else np.nan,
                         frac_P_ge_065=float((P[a:b] >= 0.65).mean()),
                         speed_ratio=float(spd[a:b].max() / max(base_spd[max(a-1, 0)], 1e-9)),
                         vrad_peak=float((sg*vr[a:b]).max())))
d = pd.DataFrame(rows); d.to_csv(OUT/"radial_event_kinematics.csv", index=False)
t = pd.DataFrame(tails); t.to_csv(OUT/"rate_tails.csv", index=False); print(t.round(3).to_string())
q = lambda x: x.quantile([.1, .25, .5, .75, .9]).round(2).tolist()
for (src, lab), g in d.groupby(["source", "label"]):
    print(src, lab, len(g), "peak_rate", q(g.peak_rate), "P_mean", q(g.P_mean), "P_min", q(g.P_min), "frac_P>=.65", q(g.frac_P_ge_065), "speed_ratio", q(g.speed_ratio), "dur", q(g.dur_s))
