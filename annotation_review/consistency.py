"""Cross-dataset consistency, annotation-scheme statistics, boundary bias, data-quality summary."""
import json
import numpy as np, pandas as pd
from common import IDS, REVIEW, ROOT, load_cache
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
s = pd.read_csv(REVIEW/"segment_review.csv", dtype={"dataset": str})
b = pd.read_csv(REVIEW/"boundary_review.csv", dtype={"dataset": str})
e = pd.read_csv(REVIEW/"radial_events.csv", dtype={"dataset": str})
g = pd.read_csv(REVIEW/"gaps_review.csv", dtype={"dataset": str})
inv = pd.read_csv(REVIEW/"segments_inventory.csv", dtype={"dataset": str})
out = {}
STAB = ["traveling", "milling", "shoaling", "expansion", "compaction"]
st = s[s.label.isin(STAB)].copy(); st["n_fish"] = st.group.str.split("_").str[0].astype(int)
# 1 per label x group-size signature
sig = st.groupby(["label", "n_fish"]).agg(n=("seg", "size"), P=("P", "median"), M=("M", "median"), dlogR=("dlogR", "median"),
                                           rate=("rate", "median"), phi_rad=("phi_rad_pm", "median"), dur=("dur_s", "median")).round(3)
sig.to_csv(REVIEW/"tables_label_by_groupsize.csv"); print(sig)
perds = st.groupby(["label", "dataset"]).agg(n=("seg", "size"), P=("P", "median"), M=("M", "median"), rate=("rate", "median"),
                                             agree=("verdict", lambda v: (v == "agree").mean())).round(2)
perds.to_csv(REVIEW/"tables_label_by_dataset.csv")
# 2 kNN label consistency across datasets (z-space P, M, phi_rad, rate)
F = st[["P", "M", "phi_rad_pm", "rate"]].to_numpy(); Z = (F - F.mean(0)) / F.std(0)
cons = []
for i in range(len(st)):
    other = np.where(st.dataset.values != st.dataset.values[i])[0]
    d = np.linalg.norm(Z[other] - Z[i], axis=1); nn = other[np.argsort(d)[:7]]
    cons.append((st.label.values[nn] == st.label.values[i]).mean())
st["knn_same_label_other_datasets"] = cons
knn = st.groupby("label").knn_same_label_other_datasets.mean().round(2); print("kNN consistency\n", knn)
# nearest-centroid confusion
cent = {l: Z[st.label.values == l].mean(0) for l in STAB}
st["nearest_centroid"] = [min(cent, key=lambda l: np.linalg.norm(z - cent[l])) for z in Z]
conf = pd.crosstab(st.label, st.nearest_centroid); print(conf); conf.to_csv(REVIEW/"tables_nearest_centroid_confusion.csv")
# exp/comp annotation density vs detected events
rows = []
for ds in IDS:
    c = load_cache(ds); T = len(c["phi_trans"]); fps = float(c["fps"]); mins = T/fps/60
    ann = s[(s.dataset == ds) & s.label.isin(["expansion", "compaction"])]
    ev = e[(e.dataset == ds) & e.robust & e.strong]
    rows.append(dict(dataset=ds, n_fish=int(c["n_fish"]), minutes=round(mins, 1), annotated_exp_comp=len(ann),
                     robust_strong_events=len(ev), of_which_unannotated=int(ev.unannotated.sum()),
                     frac_events_annotated=round(1 - ev.unannotated.mean(), 2) if len(ev) else np.nan,
                     annotated_per_min=round(len(ann)/mins, 2), events_per_min=round(len(ev)/mins, 2)))
dens = pd.DataFrame(rows); dens.to_csv(REVIEW/"tables_radial_event_density.csv", index=False); print(dens)
# 3 scheme statistics
s["family"] = np.where(s.label.str.contains("_to_"), "transition", s.label)
fam = s.groupby("family").agg(n=("seg", "size"), total_s=("dur_s", "sum"), median_s=("dur_s", "median"),
                              min_s=("dur_s", "min"), n_lt_1s=("dur_s", lambda d: (d < 1).sum()),
                              n_windows_median=("n_frames", lambda f: np.median(f // 5))).round(2)
fam["share_time"] = (fam.total_s / fam.total_s.sum()).round(3); print(fam); fam.to_csv(REVIEW/"tables_scheme_classes.csv")
tr = s[s.family == "transition"]; print("transition dur median", tr.dur_s.median(), "share <=1s", (tr.dur_s <= 1.0).mean().round(2))
pairs = tr.label.value_counts(); print("transition types used", len(pairs), "of 20")
# time stamps resolution
ts = pd.concat([inv.start_str, inv.end_str]); sec = ts.str.split(":").str[-1].astype(float)
print("timestamps on 0.5 s grid:", np.mean(np.isclose((sec*2) % 1, 0)).round(3))
# intermediate regime share of annotated stable time & unannotated time
tot = {}
for ds in IDS:
    c = load_cache(ds); T = len(c["phi_trans"])
    from scipy.ndimage import uniform_filter1d
    P = uniform_filter1d(c["phi_trans"], 15); M = uniform_filter1d(np.nan_to_num(c["M_tun"]), 15)
    inter = ~(((P > .65) & (M < .35)) | ((M > .65) & (P < .35)) | ((P < .35) & (M < .35)))
    cov = np.zeros(T, bool)
    for _, r in inv[inv.dataset == ds].iterrows(): cov[r.start:min(r.end, T)] = True
    sp = c["speed"]; slow = np.nan_to_num(sp, nan=np.nanmedian(sp)) < 0.25*np.nanmedian(sp)
    ncl = np.load(REVIEW/"cache"/f"{ds}_nclust.npy")
    tot[ds] = dict(frac_unannotated=round(1 - cov.mean(), 3), frac_intermediate_all=round(inter.mean(), 3),
                   frac_intermediate_in_annotated=round(inter[cov].mean(), 3), frac_intermediate_in_unannotated=round(inter[~cov].mean(), 3) if (~cov).any() else np.nan,
                   frac_slow=round(slow.mean(), 3), frac_split=round((ncl > 1).mean(), 3))
cover = pd.DataFrame(tot).T; print(cover); cover.to_csv(REVIEW/"tables_coverage_regimes.csv")
# 4 boundary bias (criterion onset, signed: negative = data change happens BEFORE annotated boundary)
bb = b.dropna(subset=["onset_offset"]).copy(); bb["onset_s"] = bb.onset_offset / 29.97
bias = bb.groupby(["criterion_label", "side"]).onset_s.describe()[["count", "25%", "50%", "75%"]].round(2)
print(bias); bias.to_csv(REVIEW/"tables_boundary_bias.csv")
print("boundary status (segment sides):", b.status.value_counts().to_dict())
ub = b.drop_duplicates(["dataset", "frame"]); print("unique boundaries:", len(ub), ub.status.value_counts().to_dict())
print("onset range across smoothings (frames) median/90%:", bb.onset_range.median(), bb.onset_range.quantile(.9))
cpr = (b.cp_offset_max - b.cp_offset_min).dropna(); print("CP offset range across 9 configs (frames) median/90%:", cpr.median(), cpr.quantile(.9))
# transition segments that are already in the target radial state
tc = s[s.label.str.endswith("_to_compaction")]; te = s[s.label.str.endswith("_to_expansion")]
print("rate in X_to_compaction segs median", round(tc.rate.median(),3), "share<0:", round((tc.rate < 0).mean(),2), "| compaction segs", round(s[s.label=="compaction"].rate.median(),3))
print("rate in X_to_expansion segs median", round(te.rate.median(),3), "share>0:", round((te.rate > 0).mean(),2))
fc = s[s.label.str.startswith("compaction_to_")]; print("rate in compaction_to_X median", round(fc.rate.median(),3), "share<0:", round((fc.rate < 0).mean(),2))
# 5 quality
q = s.groupby("dataset").agg(segs=("seg", "size"), flagged=("quality_flag", "sum"), jumps=("q_jumps", "sum"), swaps=("q_swaps", "sum"),
                             linear_frac=("q_linear_frac", "mean"), closepair_frames=("q_closepair_frames", "sum")).round(3)
print(q); q.to_csv(REVIEW/"tables_quality.csv")
fl = s[s.quality_flag & s.label.isin(["expansion", "compaction"])]; print("flagged exp/comp segs:", len(fl), fl.verdict.value_counts().to_dict())
# 6 stale annotated_features.csv
af = pd.read_csv(ROOT/"annotated_features.csv", dtype={"dataset": str})
mg = af.merge(inv, left_on=["dataset", "start_frame", "end_frame"], right_on=["dataset", "start", "end"], how="left")
print("annotated_features.csv rows:", len(af), "matching current annotation spans:", int(mg.start.notna().sum()))
out.update(af_rows=len(af), af_match=int(mg.start.notna().sum()))
json.dump(out, open(REVIEW/"cache"/"consistency.json", "w"))
