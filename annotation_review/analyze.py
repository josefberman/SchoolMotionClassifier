"""Segment-by-segment review of real annotations. Writes segment_review.csv, boundary_review.csv,
gaps_review.csv, sensitivity tables and summary json. Figures are made by plots.py."""
import json, joblib, warnings
import numpy as np, pandas as pd
import ruptures as rpt
from scipy.ndimage import uniform_filter1d
from scipy.cluster.hierarchy import fcluster, linkage
from common import IDS, REVIEW, ROOT, load_cache, load_ds
from src.labels import is_transition
from src.features.windows import window_feature_matrix
warnings.filterwarnings("ignore")

TH = dict(hi=0.65, lo=0.35)                 # Tunstrom et al. 2013 state thresholds
SPREAD = 0.10                               # |dlog R| over segment for expansion/compaction "agree"
SMOOTH = 15                                 # frames (0.5 s) for state classification
TH_SETS = {"tunstrom_0.65/0.35": (0.65, 0.35, 0.10), "lenient_0.60/0.40": (0.60, 0.40, 0.05),
           "strict_0.70/0.30": (0.70, 0.30, 0.20), "loose_0.55/0.45": (0.55, 0.45, 0.05)}
inv = pd.read_csv(REVIEW/"segments_inventory.csv", dtype={"dataset": str})
qda = joblib.load(REVIEW/"sim_qda.joblib")

def sm(x, w=SMOOTH):
    x = np.nan_to_num(np.asarray(x, float), nan=np.nanmean(x))
    return uniform_filter1d(x, size=max(1, w), mode="nearest")

def series(ds, w=SMOOTH):
    c = load_cache(ds); fps = float(c["fps"])
    s = {k: sm(c[k], w) for k in ["phi_trans", "M_tun", "phi_tan", "phi_rad_pm",
                               "vrad_norm", "R", "hull", "nnd", "speed"]}
    logR = np.log(sm(c["R"], 5)); s["rate"] = sm(np.gradient(logR) * fps, w)        # dlogR/dt  [1/s]
    s["hull_rate"] = sm(np.gradient(np.log(np.maximum(sm(c["hull"], 5), 1))) * fps, SMOOTH)
    s["nnd_rate"] = sm(np.gradient(np.log(sm(c["nnd"], 5))) * fps, SMOOTH)
    s["raw"] = c; s["fps"] = fps; s["T"] = len(c["phi_trans"])
    return s

def states(P, M, hi, lo):
    pol = (P > hi) & (M < lo); mil = (M > hi) & (P < lo); swa = (P < lo) & (M < lo)
    return pol, mil, swa

def stable_score(lab, s, sl):
    if lab == "traveling": return s["phi_trans"][sl].mean()
    if lab == "milling": return s["M_tun"][sl].mean()
    if lab == "shoaling": return 1 - np.maximum(s["phi_trans"][sl], s["M_tun"][sl]).mean()
    if lab == "expansion": return s["rate"][sl].mean()
    if lab == "compaction": return -s["rate"][sl].mean()

def dlog(x, a, b, k=5):
    k = max(1, min(k, (b - a) // 3))
    return float(np.log(np.mean(x[b-k:b]) / np.mean(x[a:a+k])))

def judge(lab, m, hi, lo, spread):
    """Return verdict, reason for one label given metric dict m."""
    if is_transition(lab):
        return m["trans_verdict"], m["trans_reason"]
    if lab in ("traveling", "milling", "shoaling"):
        own = {"traveling": "frac_pol", "milling": "frac_mill", "shoaling": "frac_swarm"}[lab]
        f = m[own]
        others = {k: m[v] for k, v in {"traveling": "frac_pol", "milling": "frac_mill", "shoaling": "frac_swarm"}.items() if k != lab}
        oth = max(others, key=others.get)
        ev = f"P={m['P']:.2f}, M={m['M']:.2f}; frames pol/mill/swarm={m['frac_pol']:.0%}/{m['frac_mill']:.0%}/{m['frac_swarm']:.0%}"
        if f >= 0.5: return "agree", ev
        if others[oth] >= 0.5: return "disagree", ev + f" -> mostly {oth}"
        return "questionable", ev + " (intermediate regime)"
    sgn = 1 if lab == "expansion" else -1
    d, v, h = sgn*m["dlogR"], sgn*m["vrad_norm"], sgn*m["dlogHull"]
    if d >= spread and v > 0: return "agree", f"dlogR={m['dlogR']:+.2f}, hull {m['dlogHull']:+.2f}, vrad={m['vrad_norm']:+.3f}"
    if d > 0 or v > 0 or h >= spread: return "questionable", f"weak/mixed: dlogR={m['dlogR']:+.2f}, hull {m['dlogHull']:+.2f}, vrad={m['vrad_norm']:+.3f}"
    return "disagree", f"opposite: dlogR={m['dlogR']:+.2f}, hull {m['dlogHull']:+.2f}, vrad={m['vrad_norm']:+.3f}"

def suggest(m, hi, lo, spread, dur_s):
    """Data-driven label (stable state + radial overlay)."""
    shares = {"traveling": m["frac_pol"], "milling": m["frac_mill"], "shoaling": m["frac_swarm"]}
    best = max(shares, key=shares.get)
    base = best if shares[best] >= 0.5 else "mixed"
    rad = ""
    if m["dlogR"] >= max(spread, 0.15) and m["vrad_norm"] > 0: rad = "expansion"
    if m["dlogR"] <= -max(spread, 0.15) and m["vrad_norm"] < 0: rad = "compaction"
    return base, rad

# ------------------------------------------------------------------ change points
def cp_signal(s, smooth):
    X = np.column_stack([s["phi_trans"], s["M_tun"], s["phi_rad_pm"], np.clip(s["rate"], -2, 2)])
    X = uniform_filter1d(X, size=max(1, smooth), axis=0, mode="nearest")
    T = len(X); nw = T // 5
    W = X[:nw*5].reshape(nw, 5, -1).mean(1)                    # repo-style 5-frame windows
    W = (W - np.median(W, 0)) / (np.quantile(W, 0.75, 0) - np.quantile(W, 0.25, 0) + 1e-9)
    return W

def detect(s, smooth, k_target):
    """KernelCPD (linear kernel = l2 on window means); penalty bisected so that the number of
    change points ~= k_target (a multiple of the number of annotated boundaries)."""
    W = cp_signal(s, smooth)
    algo = rpt.KernelCPD(kernel="linear", min_size=3).fit(W)
    lo, hi = -6.0, 6.0
    for _ in range(18):
        mid = (lo + hi) / 2
        n = len(algo.predict(pen=np.exp(mid))) - 1
        if n > k_target: lo = mid
        else: hi = mid
    bk = algo.predict(pen=np.exp(hi))
    return np.array(bk[:-1]) * 5                                # back to frames

SMOOTHS, BETAS = [5, 15, 31], [0.5, 1.0, 2.0]                   # BETAS = CP count / annotated boundary count
BASE = (15, 1.0)

def match(boundary, cps, tol):
    if len(cps) == 0: return None
    d = cps - boundary; i = np.argmin(np.abs(d))
    return int(d[i]) if abs(d[i]) <= tol else None

def onset(lab_after, s, b, fps, side):
    """Label-specific criterion crossing nearest to boundary b (within ±3 s)."""
    if lab_after is None or is_transition(lab_after): return None
    w = int(3*fps); a0, a1 = max(0, b-w), min(s["T"]-1, b+w)
    # midpoint (0.5) crossing: the boundary between states, not the Tunstrom state-membership threshold
    if lab_after == "traveling": z = s["phi_trans"] - 0.5
    elif lab_after == "milling": z = s["M_tun"] - 0.5
    elif lab_after == "shoaling": z = 0.5 - np.maximum(s["phi_trans"], s["M_tun"])
    elif lab_after == "expansion": z = s["rate"]
    else: z = -s["rate"]
    z = z[a0:a1+1]
    want = 1 if side == "start" else -1                         # start: z goes - -> + ; end: + -> -
    cr = np.where(np.diff(np.sign(z)) == 2*want)[0]
    if len(cr) == 0: return None
    cr = cr + a0 + 1
    return int(cr[np.argmin(np.abs(cr - b))] - b)

# ------------------------------------------------------------------ main loop
seg_rows, bnd_rows, gap_rows, sens_rows, null_rows, event_rows = [], [], [], [], [], []
cp_store = {}
for ds in IDS:
    s = series(ds); fps, T, raw = s["fps"], s["T"], s["raw"]
    tele = np.load(REVIEW/"cache"/f"{ds}_teleport.npy")
    pos, vel, _ = load_ds(ds)
    segs = inv[inv.dataset == ds].sort_values(["start", "end"]).reset_index(drop=True)
    nb = len(set(segs.start) | set(segs.end))
    cps = {(sw, b): detect(s, sw, int(b*nb)) for sw in SMOOTHS for b in BETAS}
    rng = np.random.default_rng(0); rb = rng.integers(0, T, 2000); bc = cps[BASE]
    null_rows.append(dict(dataset=ds, n_boundaries=nb, n_cp_base=len(bc), null_within_0p5s=float(np.mean([match(x, bc, int(0.5*fps)) is not None for x in rb])),
                          null_within_3s=float(np.mean([match(x, bc, int(3*fps)) is not None for x in rb]))))
    cp_store[ds] = {f"{k[0]}_{k[1]}": v.tolist() for k, v in cps.items()}
    # fission check: number of clusters (single-linkage, cut at 6x median NND) every 5th frame
    nnd_med = float(np.median(raw["nnd"]))
    ncl = np.ones(T)
    for t in range(0, T, 5):
        Z = linkage(pos[t], "single"); ncl[t:t+5] = fcluster(Z, 6*nnd_med, "distance").max()
    s["nclust"] = ncl
    # ---- boundaries (every segment start and end)
    # Two independent methods: (1) multivariate change points (9 configs: 3 smoothings x 3 CP densities),
    # (2) label-specific criterion crossing (P / M / swarm / dlogR/dt sign), at 3 smoothings.
    # Transition segments have no own criterion: they borrow it from the stable neighbour sharing the frame.
    tol = int(3*fps); half = int(0.5*fps)
    s_alt = {w: (s if w == SMOOTH else series(ds, w)) for w in (5, 15, 31)}
    crit = {}                                   # (frame, side) -> (label used, side used)
    for i, r in segs.iterrows():
        if not is_transition(r.label):
            crit[(r.start, "start")] = (r.label, "start"); crit[(r.end, "end")] = (r.label, "end")
    for i, r in segs.iterrows():
        for side, bf in (("start", r.start), ("end", r.end)):
            offs = {k: match(bf, v, tol) for k, v in cps.items()}
            base = offs[BASE]
            found = [o for o in offs.values() if o is not None]
            if not is_transition(r.label): lab_ref, side_ref = r.label, side
            else:   # neighbour: a transition's start is the end of the previous stable seg, and vice versa
                lab_ref, side_ref = crit.get((bf, "end" if side == "start" else "start"), (None, None))
            ons = {w: onset(lab_ref, s_alt[w], bf, fps, side_ref) if lab_ref else None for w in s_alt}
            on = ons[15]; on_all = [o for o in ons.values() if o is not None]
            cp_cons = len(found) >= 5 and (max(found) - min(found)) <= int(1.5*fps)
            cpm = int(np.median(found)) if found else None
            if (base is not None and abs(base) <= half) or (on is not None and abs(on) <= half):
                st, sugg = "supported", 0
            elif on is not None and cpm is not None and cp_cons and abs(cpm - on) <= half:
                st, sugg = "shift_suggested", int(round((on + cpm) / 2))
            elif on is not None and len(on_all) == 3 and (max(on_all) - min(on_all)) <= half:
                st, sugg = "shift_possible(criterion)", on
            elif cp_cons and abs(cpm) > half:
                st, sugg = "shift_possible(changepoint)", cpm
            else:
                st, sugg = "unclear", 0
            bnd_rows.append(dict(dataset=ds, seg=r.seg, label=r.label, side=side, frame=bf, status=st,
                                 criterion_label=lab_ref, cp_offset_base=base, cp_offset_median=cpm,
                                 cp_offset_min=(min(found) if found else None), cp_offset_max=(max(found) if found else None),
                                 n_configs_with_cp=len(found), onset_offset=on,
                                 onset_offset_s5=ons[5], onset_offset_s31=ons[31],
                                 onset_range=(max(on_all) - min(on_all) if on_all else None),
                                 suggested_frame=bf + sugg, suggested_offset_frames=sugg, suggested_offset_s=round(sugg/fps, 2)))
    # ---- gaps / overlaps / unannotated stretches
    prev_end = 0; prev = None
    for i, r in segs.iterrows():
        if r.start > prev_end:
            gap_rows.append(dict(dataset=ds, kind="gap", start=prev_end, end=int(r.start), after_seg=None if prev is None else int(prev.seg), before_seg=int(r.seg)))
        elif prev is not None and r.start < prev_end:
            gap_rows.append(dict(dataset=ds, kind="overlap", start=int(r.start), end=int(prev_end), after_seg=int(prev.seg), before_seg=int(r.seg)))
        prev_end = max(prev_end, r.end); prev = r
    if prev_end < T: gap_rows.append(dict(dataset=ds, kind="gap_tail", start=int(prev_end), end=T, after_seg=int(prev.seg), before_seg=None))
    if segs.end.max() > T: gap_rows.append(dict(dataset=ds, kind="beyond_data", start=T, end=int(segs.end.max()), after_seg=None, before_seg=None))
    for g in gap_rows:
        if g["dataset"] != ds or g["kind"] not in ("gap", "gap_tail"): continue
        a, b = g["start"], min(g["end"], T)
        if b - a < 2: continue
        pol, mil, swa = states(s["phi_trans"][a:b], s["M_tun"][a:b], TH["hi"], TH["lo"])
        g.update(dur_s=round((b-a)/fps, 2), frac_pol=pol.mean(), frac_mill=mil.mean(), frac_swarm=swa.mean(),
                 dlogR=dlog(s["R"], a, b), P=s["phi_trans"][a:b].mean(), M=s["M_tun"][a:b].mean())
        dom = max([("traveling", pol.mean()), ("milling", mil.mean()), ("shoaling", swa.mean())], key=lambda x: x[1])
        g["dominant"] = dom[0] if dom[1] >= 0.6 else "mixed"
        g["clear_behavior"] = bool((b - a) >= fps and (dom[1] >= 0.6 or abs(g["dlogR"]) >= 0.2))
    # ---- per-segment metrics
    for i, r in segs.iterrows():
        a, b = int(r.start), int(min(r.end, T)); n = b - a; dur = n / fps
        if n < 2:
            seg_rows.append(dict(dataset=ds, seg=r.seg, raw_label=r.raw_label, label=r.label, start=a, end=int(r.end), n_frames=n, verdict="unevaluable", reason="segment outside data or <2 frames")); continue
        sl = slice(a, b)
        P, M = s["phi_trans"][sl], s["M_tun"][sl]
        pol, mil, swa = states(P, M, TH["hi"], TH["lo"])
        m = dict(P=P.mean(), M=M.mean(), frac_pol=pol.mean(), frac_mill=mil.mean(), frac_swarm=swa.mean(),
                 phi_trans=raw["phi_trans"][sl].mean(), phi_tan=raw["phi_tan"][sl].mean(), phi_rad_pm=raw["phi_rad_pm"][sl].mean(),
                 vrad_norm=np.nanmean(raw["vrad_norm"][sl]), rate=s["rate"][sl].mean(),
                 dlogR=dlog(s["R"], a, b), dlogHull=dlog(s["hull"], a, b), dlogNND=dlog(s["nnd"], a, b),
                 R=raw["R"][sl].mean(), nnd=raw["nnd"][sl].mean(), speed=np.nanmean(raw["speed"][sl]),
                 nnd_rel=raw["nnd"][sl].mean()/nnd_med, max_clusters=int(ncl[sl].max()), frac_split=float((ncl[sl] > 1).mean()))
        # independent radial lines of evidence: do R, hull, NND, vrad agree in sign?
        signs = np.sign([m["dlogR"], m["dlogHull"], m["dlogNND"], m["vrad_norm"]])
        m["radial_sign_agreement"] = float(abs(signs.sum()) / 4)
        # transitions: compare before-part vs after-part
        if is_transition(r.label):
            A, B = r.label.split("_to_")
            k = max(3, int(0.3*n)); ctx = int(1.0*fps)
            pre = slice(max(0, a-ctx), a+k); post = slice(b-k, min(T, b+ctx))
            dA = stable_score(A, s, pre) - stable_score(A, s, post); dB = stable_score(B, s, post) - stable_score(B, s, pre)
            radial = {"expansion", "compaction"}
            m["trans_dA"], m["trans_dB"] = dA, dB
            if A not in radial and B not in radial:          # state -> state: both must move
                okA, okB = dA > 0.05, dB > 0.05
                m["trans_verdict"] = "agree" if okA and okB else ("questionable" if (okA or okB or min(dA, dB) > -0.05) else "disagree")
                m["trans_reason"] = f"{A} score {-dA:+.2f}, {B} score {dB:+.2f} (pre->post)"
            else:                                             # radial component decides; units 1/s
                d = dA if A in radial else dB
                if A in radial and B in radial:
                    rp, rq = s["rate"][pre].mean(), s["rate"][post].mean()
                    good = (A == "expansion" and rp > 0 > rq) or (A == "compaction" and rp < 0 < rq)
                else: good = True
                m["trans_verdict"] = "agree" if (d > 0.02 and good) else ("questionable" if d > -0.02 else "disagree")
                m["trans_reason"] = f"radial change pre->post {d:+.3f}/s (rate pre {s['rate'][pre].mean():+.3f}, post {s['rate'][post].mean():+.3f})"
                st = B if A in radial else A                  # the stable side, if any
                if st not in radial:
                    side = post if st == B else pre
                    sc = stable_score(st, s, side)
                    m["trans_reason"] += f"; {st} score on its side {sc:.2f}"
                    if m["trans_verdict"] == "agree" and sc < 0.5: m["trans_verdict"] = "questionable"; m["trans_reason"] += " (<0.5)"
        v, why = judge(r.label, m, TH["hi"], TH["lo"], SPREAD)
        base, rad = suggest(m, TH["hi"], TH["lo"], SPREAD, dur)
        # sensitivity across threshold sets
        sens = {}
        for name, (hi, lo, sp) in TH_SETS.items():
            p2, m2, w2 = states(P, M, hi, lo)
            mm = dict(m, frac_pol=p2.mean(), frac_mill=m2.mean(), frac_swarm=w2.mean())
            sens[name] = judge(r.label, mm, hi, lo, sp)[0]
        # tracking quality inside segment
        q = dict(q_teleports=int(tele[sl].sum()), q_fast_moves=int(raw["n_jump"][sl].sum() - tele[sl].sum()),
                 q_jumps=int(raw["n_jump"][sl].sum()), q_swaps=int(raw["n_swap"][sl].sum()),
                 q_frozen=int(raw["n_frozen"][sl].sum()), q_linear_frac=float(raw["n_linear"][sl].sum()/(n*int(raw["n_fish"]))),
                 q_closepair_frames=int((raw["close_pairs"][sl] > 0).sum()), q_zero_vel=int(raw["n_zero_vel"][sl].sum()))
        q["quality_flag"] = bool(q["q_teleports"] > 0 or q["q_linear_frac"] > 0.10 or q["q_frozen"] > n)
        # simulated-class resemblance (QDA on repo 5-frame window features)
        if n >= 5:
            Xw, _ = window_feature_matrix(pos[a:b], vel[a:b], fps=fps, names=qda["names"])
            pr = qda["clf"].predict(Xw); vc = pd.Series(pr).value_counts(normalize=True)
            sim_cls, sim_share = vc.index[0], float(vc.iloc[0])
        else: sim_cls, sim_share = "too_short", np.nan
        bs = [x for x in bnd_rows if x["dataset"] == ds and x["seg"] == r.seg]
        st_s = next(x for x in bs if x["side"] == "start"); st_e = next(x for x in bs if x["side"] == "end")
        notes = []
        if dur < 1.0: notes.append("short<1s")
        if n < 15: notes.append("<15 frames: dropped by build_real_xy(min_frames=15)")
        if n < int(0.5*fps): notes.append("<0.5 s: silently dropped by load_real_segments")
        if q["quality_flag"]: notes.append("tracking-quality flag")
        if m["frac_split"] > 0.3: notes.append(f"group split into subgroups {m['frac_split']:.0%} of frames")
        if r.label in ("expansion", "compaction") and m["radial_sign_agreement"] < 0.5: notes.append("radial evidence lines disagree")
        if v == "agree" and q["quality_flag"] and r.label in ("expansion", "compaction"): v = "questionable"; notes.append("downgraded: radial change coincides with tracking artefacts")
        seg_rows.append(dict(dataset=ds, group=r.group, seg=r.seg, raw_label=r.raw_label, label=r.label,
                             start_str=r.start_str, end_str=r.end_str, start=a, end=int(r.end), n_frames=n, dur_s=round(dur, 2),
                             verdict=v, reason=why, **{f"sens_{k}": x for k, x in sens.items()},
                             suggested_state=base, suggested_radial=rad, sim_nearest=sim_cls, sim_share=sim_share,
                             start_status=st_s["status"], start_suggested=st_s["suggested_frame"], start_offset_s=st_s["suggested_offset_s"],
                             end_status=st_e["status"], end_suggested=st_e["suggested_frame"], end_offset_s=st_e["suggested_offset_s"],
                             start_onset_offset=st_s["onset_offset"], end_onset_offset=st_e["onset_offset"],
                             **{k: (round(x, 4) if isinstance(x, float) else x) for k, x in m.items() if k not in ("trans_verdict", "trans_reason")},
                             **q, notes="; ".join(notes)))
    # ---- radial events (data-driven): |dlogR/dt| > RATE_THR for >= 1 s, |dlogR| >= 0.10, vrad sign agrees
    RATE_THR = 0.06
    for sign, name in ((1, "expansion"), (-1, "compaction")):
        on_ = (sign * s["rate"]) > RATE_THR
        d = np.diff(np.r_[0, on_.astype(int), 0]); st_, en_ = np.where(d == 1)[0], np.where(d == -1)[0]
        for a, b in zip(st_, en_):
            if b - a < fps: continue
            dl = dlog(s["R"], a, b); vr = float(np.nanmean(raw["vrad_norm"][a:b]))
            if sign*dl < 0.10 or sign*vr <= 0: continue
            ov = segs[(segs.start < b) & (segs.end > a)]
            radlab = ov[ov.label.str.contains(name)]
            cover = 0
            for _, rr in radlab.iterrows(): cover += min(b, rr.end) - max(a, rr.start)
            q_ = pos[a:b] - pos[a:b].mean(1, keepdims=True); u_ = vel[a:b] - np.nanmean(vel[a:b], 1, keepdims=True)
            ur = np.nanmean((u_ * q_).sum(-1) / np.maximum(np.linalg.norm(q_, axis=-1), 1e-9), 0)
            med_d = np.median(np.linalg.norm(q_, axis=-1), 1)
            ax_ = np.array([np.linalg.eigvalsh(np.cov(x.T)) for x in q_])        # PCA variances (minor, major)
            event_rows.append(dict(dataset=ds, kind=name, start=int(a), end=int(b), dur_s=round((b-a)/fps, 2), dlogR=round(dl, 3),
                                   dlogHull=round(dlog(s["hull"], a, b), 3), dlogNND=round(dlog(s["nnd"], a, b), 3),
                                   dlog_median_dist=round(float(np.log(med_d[-5:].mean()/med_d[:5].mean())), 3),
                                   frac_fish_moving_with_event=round(float(np.mean(sign*ur > 0)), 2),
                                   vrad_norm=round(vr, 3), peak_rate=round(float((sign*s["rate"][a:b]).max()), 3),
                                   overlapping_labels="|".join(f"{rr.seg}:{rr.label}" for _, rr in ov.iterrows()) or "UNANNOTATED",
                                   frac_covered_by_matching_label=round(cover/(b-a), 2),
                                   jumps_in_event=int(tele[a:b].sum()), fast_moves_in_event=int(raw["n_jump"][a:b].sum() - tele[a:b].sum()),
                                   dlog_major=round(float(np.log(ax_[-5:, 1].mean()/ax_[:5, 1].mean())/2), 3), dlog_minor=round(float(np.log(ax_[-5:, 0].mean()/ax_[:5, 0].mean())/2), 3)))
    np.save(REVIEW/"cache"/f"{ds}_nclust.npy", ncl)
    print(ds, "done", flush=True)

seg = pd.DataFrame(seg_rows); seg.to_csv(REVIEW/"segment_review.csv", index=False)
pd.DataFrame(bnd_rows).to_csv(REVIEW/"boundary_review.csv", index=False)
pd.DataFrame(gap_rows).to_csv(REVIEW/"gaps_review.csv", index=False)
pd.DataFrame(event_rows).to_csv(REVIEW/"radial_events.csv", index=False)
pd.DataFrame(null_rows).to_csv(REVIEW/"cp_null_rates.csv", index=False)
json.dump(cp_store, open(REVIEW/"cache"/"changepoints.json", "w"))
print(seg.verdict.value_counts().to_dict())
