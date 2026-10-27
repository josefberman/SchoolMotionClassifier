"""Second pass: draft corrected annotations under Josef's domain rules.
Rules (from Josef):
 1 expansion/compaction = RAPID startle-like events with little traveling; if clear traveling -> traveling.
 2 trim stable segments inward to their steady part (never extend).
 3 leave transitions as they are (only fix their state names when a neighbour is relabelled).
 4 new segments in gaps only for clear behaviour (steady state, strict exp/comp, or clear transition).
 5 weak long segments: trim / split / relabel to dominant clear state / leave unlabelled.
 6 no 'mixed'; keep vocabulary and JSON schema.
"""
import sys, json, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from scipy.ndimage import uniform_filter1d, binary_closing
from common import IDS, REVIEW, ROOT, load_cache
from src.labels import canonicalize, load_aliases
from src.sim.io import load_motion_json, mmss_to_frame

OUT = REVIEW/"revised"; ALIAS = load_aliases()
WORD = {"traveling": "traveling", "milling": "milling", "shoaling": "shoaling", "expansion": "expansion", "compaction": "compaction"}
STABLE = ("traveling", "milling", "shoaling"); RAD = ("expansion", "compaction")
# ---------------- thresholds (documented in CHANGELOG / REPORT_v2) ----------------
STEADY = {  # steady-state criteria on 0.5 s smoothed P (polarization) and M (Tunstrom rotation)
    "traveling": lambda P, M: P >= 0.65,
    "milling": lambda P, M: (M >= 0.50) & (P <= 0.50),
    "shoaling": lambda P, M: (P < 0.40) & (M < 0.40),
}
STEADY_TXT = {"traveling": "P>=0.65", "milling": "M>=0.50 & P<=0.50", "shoaling": "P<0.40 & M<0.40"}
FAST_Q = 0.95          # peak |dlogR/dt| must reach the dataset's 95th percentile of |dlogR/dt|  (top 5% tail)
MIN_DLOGR = 0.15       # >= ~16% change in mean distance to centroid during the event
MAX_DUR = 6.0          # s; rapid event
TRAVEL_FRAC = 0.80     # 'clear traveling' if >=80% of event frames P>=0.65 ...
TRAVEL_PMIN = 0.50     # ... and P never drops below 0.5
BROKEN = dict(P_mean=0.65, P_min=0.50, P_drop=0.20)   # polarization low or broken (any one)
BURST = 1.30           # peak mean speed / trailing-5 s median speed (required for NEW events only)
MIN_STEADY_RUN = 2.0   # s, minimum clear run to keep / add a stable segment
EDGE_HOLD = 1.0        # s, criterion must hold this long at a trimmed edge
MIN_NEW_GAP = 3.0     # s, minimum steady run to add a NEW stable segment in a gap
WEAK_FRAC = 0.60       # below this steady fraction a stable segment is handled as 'weak'

def sm(x, w=15): return uniform_filter1d(np.nan_to_num(np.asarray(x, float), nan=np.nanmedian(x)), w, mode="nearest")
def t2s(t):  # seconds -> his 'MM:SS' / 'MM:SS.5' style
    t = round(t * 2) / 2; m = int(t // 60); s = t - 60*m
    return f"{m:02d}:{int(s):02d}" if s == int(s) else f"{m:02d}:{s:04.1f}"
def snap_in(a, b, fps):     # frames -> grid-aligned strings strictly inside [a, b)
    ta, tb = math.ceil(a / fps * 2) / 2, math.floor(b / fps * 2) / 2
    return ta, tb
def raw_of(canon):
    if "_to_" in canon: A, B = canon.split("_to_"); return f"{WORD[A]} to {WORD[B]}"
    return WORD[canon]

class Seg:
    def __init__(self, start_s, end_s, raw, fps, orig=None, strs=None):
        self.start_s, self.end_s, self.raw = start_s, end_s, raw
        self.fps = fps; self.orig = orig if orig is not None else []
        self.strs = strs                     # keep original strings when untouched
        self.canon = canonicalize(raw, ALIAS); self.notes = []
    @property
    def a(self): return mmss_to_frame(self.strs[0], self.fps) if self.strs else int(round(self.start_s * self.fps))
    @property
    def b(self): return mmss_to_frame(self.strs[1], self.fps) if self.strs else int(round(self.end_s * self.fps))
    def set_label(self, canon): self.canon = canon; self.raw = raw_of(canon)
    def set_bounds(self, ts, te): self.start_s, self.end_s, self.strs = ts, te, None
    def out(self):
        s, e = self.strs if self.strs else (t2s(self.start_s), t2s(self.end_s))
        return {"start": s, "end": e, "label": self.raw}

def metrics(S, a, b):
    P, M, rate = S["P"][a:b], S["M"][a:b], S["rate"][a:b]
    return dict(P=float(P.mean()), M=float(M.mean()), rate=float(rate.mean()))

def radial_eval(S, lab, a, b, fps):
    sg = 1 if lab == "expansion" else -1
    P = S["P"]; pre = slice(max(0, a - int(fps)), max(a, 1))
    d = dict(peak_rate=float((sg*S["rate"][a:b]).max()), dlogR=float(np.log(S["Rs"][b-1]/S["Rs"][a])),
             P_mean=float(P[a:b].mean()), P_min=float(P[a:b].min()), P_pre=float(P[pre].mean()),
             frac_P065=float((P[a:b] >= 0.65).mean()), dur=(b-a)/fps,
             speed_ratio=float(S["spd"][a:b].max() / max(S["base_spd"][max(a-1, 0)], 1e-9)), thr=S["fast_thr"])
    d["P_drop"] = d["P_pre"] - d["P_min"]
    d["fast"] = bool(d["peak_rate"] >= S["fast_thr"] and sg*d["dlogR"] >= MIN_DLOGR and d["dur"] <= MAX_DUR)
    d["clear_travel"] = bool(d["frac_P065"] >= TRAVEL_FRAC and d["P_min"] >= TRAVEL_PMIN)
    d["broken"] = bool(d["P_mean"] < BROKEN["P_mean"] or d["P_min"] < BROKEN["P_min"] or d["P_drop"] >= BROKEN["P_drop"])
    d["burst"] = bool(d["speed_ratio"] >= BURST)
    return d

def fmt_rad(d):
    return (f"peak dlogR/dt {d['peak_rate']:.2f}/s (thr {d['thr']:.2f}), dlogR {d['dlogR']:+.2f}, dur {d['dur']:.1f}s, "
            f"P mean {d['P_mean']:.2f} min {d['P_min']:.2f} (pre {d['P_pre']:.2f}), {d['frac_P065']:.0%} frames P>=0.65, speed x{d['speed_ratio']:.2f}")

def runs(mask, min_len):
    d = np.diff(np.r_[0, mask.astype(int), 0]); st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    return [(s, e) for s, e in zip(st, en) if e - s >= min_len]

changes = []; radial_rows = []; final_rows = []
def log(ds, typ, old, new, reason, **m):
    changes.append(dict(dataset=ds, change=typ,
        old_seg=";".join(str(o) for o in old.get("ids", [])), old_label=old.get("label", ""), old_start=old.get("start", ""), old_end=old.get("end", ""),
        old_frames=old.get("frames", ""), new_label=new.get("label", ""), new_start=new.get("start", ""), new_end=new.get("end", ""),
        new_frames=new.get("frames", ""), reason=reason, **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()}))
def od(sg): o = sg.out(); return dict(ids=sg.orig, label=sg.raw, start=o["start"], end=o["end"], frames=f"{sg.a}-{sg.b}")

ev_all = pd.read_csv(REVIEW/"radial_events.csv", dtype={"dataset": str})
for ds in IDS:
    c = load_cache(ds); fps = float(c["fps"]); T = len(c["phi_trans"])
    S = dict(P=sm(c["phi_trans"]), M=sm(c["M_tun"]), Rs=sm(c["R"], 5))
    S["rate"] = sm(np.gradient(np.log(S["Rs"])) * fps); S["spd"] = sm(c["speed"], 5)
    S["base_spd"] = pd.Series(S["spd"]).rolling(int(5*fps), min_periods=1).median().to_numpy()
    S["fast_thr"] = float(np.quantile(np.abs(S["rate"]), FAST_Q))
    steady = {k: f(S["P"], S["M"]) for k, f in STEADY.items()}
    ann = load_motion_json(ROOT/"annotations"/f"{ds}_motion.json")
    segs = [Seg(None, None, x["label"], fps, [i], (x["start"], x["end"])) for i, x in enumerate(ann["segments"])]
    for sg in segs: sg.start_s, sg.end_s = sg.a / fps, sg.b / fps
    orig_cov = np.zeros(T, bool)
    for sg in segs: orig_cov[sg.a:min(sg.b, T)] = True
    # ---------- 1. strict re-check of annotated expansion / compaction ----------
    for sg in segs:
        if sg.canon not in RAD: continue
        a, b = sg.a, min(sg.b, T); d = radial_eval(S, sg.canon, a, b, fps)
        if d["clear_travel"]:
            dec = "-> traveling (clear traveling)"; new = "traveling"
        elif d["fast"] and d["broken"]:
            dec = "kept (rapid, polarization broken" + (", speed burst)" if d["burst"] else ", no speed burst)"); new = sg.canon
        elif d["fast"]:
            dec = "kept, borderline (rapid but polarization not clearly broken)"; new = sg.canon
        else:
            share = {k: float(v[a:b].mean()) for k, v in steady.items()}; best = max(share, key=share.get)
            if share[best] >= 0.6: dec = f"-> {best} (not rapid; {share[best]:.0%} frames steady {best})"; new = best
            else: dec = "kept, borderline (not rapid but not clear traveling; check video)"; new = sg.canon
        radial_rows.append(dict(dataset=ds, seg=sg.orig[0], label=sg.canon, start=a, end=b, decision=dec, **d))
        if new != sg.canon:
            old = od(sg); sg.set_label(new); sg.notes.append("relabelled")
            log(ds, "relabel", old, dict(label=sg.raw, start=old["start"], end=old["end"], frames=old["frames"]),
                "strict exp/comp: " + dec + "; " + fmt_rad(d))
        elif "borderline" in dec:
            sg.notes.append("borderline radial")
            log(ds, "unchanged_flagged", od(sg), od(sg), "strict exp/comp: " + dec + "; " + fmt_rad(d))
    # ---------- 1b. transition names after relabels; A->A transitions ----------
    def fix_transitions():
        segs.sort(key=lambda s: (s.a, s.b))
        for i, sg in enumerate(segs):
            if "_to_" not in sg.canon: continue
            A, B = sg.canon.split("_to_")
            prv = segs[i-1] if i > 0 and abs(segs[i-1].b - sg.a) <= 2 else None
            nxt = segs[i+1] if i + 1 < len(segs) and abs(segs[i+1].a - sg.b) <= 2 else None
            nA = prv.canon if (prv is not None and "_to_" not in prv.canon and "relabelled" in prv.notes) else A
            nB = nxt.canon if (nxt is not None and "_to_" not in nxt.canon and "relabelled" in nxt.notes) else B
            if (nA, nB) == (A, B): continue
            old = od(sg)
            if nA != nB:
                sg.set_label(f"{nA}_to_{nB}"); sg.notes.append("renamed")
                log(ds, "relabel", old, od(sg), "transition renamed because neighbour was relabelled")
            else:
                frac = float(steady[nA][sg.a:sg.b].mean()) if nA in steady else 0.0
                if frac >= 0.8:
                    sg.set_label(nA); sg.notes.append("relabelled")
                    log(ds, "relabel", old, od(sg), f"no state change left after neighbour relabel; {frac:.0%} frames steady {nA}")
                else:
                    sg.notes.append("REMOVE"); log(ds, "removed", old, {}, f"transition {nA}->{nA} after neighbour relabel; only {frac:.0%} steady")
    fix_transitions(); segs[:] = [s for s in segs if "REMOVE" not in s.notes]
    def merge():
        segs.sort(key=lambda s: (s.a, s.b)); out = []
        for sg in segs:
            if out and out[-1].canon == sg.canon and "_to_" not in sg.canon and abs(out[-1].b - sg.a) <= 2:
                p = out[-1]; old = dict(ids=p.orig + sg.orig, label=f"{p.raw} + {sg.raw}", frames=f"{p.a}-{p.b} + {sg.a}-{sg.b}")
                strs = (p.out()["start"], sg.out()["end"]); p.orig = p.orig + sg.orig; p.strs = strs
                p.start_s, p.end_s = p.a / fps, p.b / fps; p.notes += sg.notes + ["merged"]
                log(ds, "merged", old, od(p), "adjacent segments with identical label after relabel")
            else: out.append(sg)
        segs[:] = out
    merge()
    # ---------- 2. carve strict NEW exp/comp events (earlier 'missed' list, plus all detected events) ----------
    E = ev_all[(ev_all.dataset == ds) & ev_all.robust]
    new_events = []
    for _, e in E.iterrows():
        a, b = int(e.start), int(e.end); d = radial_eval(S, e.kind, a, b, fps)
        cover = [s for s in segs if s.a < b and s.b > a]
        annotated_same = any(s.canon == e.kind for s in cover)
        surv = d["fast"] and d["burst"] and not d["clear_travel"] and d["P_min"] < 0.5 and d["P_mean"] < 0.65   # stricter for NEW events
        if e.unannotated and e.strong:
            radial_rows.append(dict(dataset=ds, seg=f"event {a}-{b}", label=e.kind, start=a, end=b,
                                    decision="survives strict (new segment candidate)" if surv else ("fails: clear traveling" if d["clear_travel"] else "fails strict"), **d))
        if surv and not annotated_same: new_events.append((a, b, e.kind, d))
    for a, b, kind, d in new_events:
        ta, tb = snap_in(a, b, fps)
        if tb - ta < 1.0: continue
        fa, fb = int(round(ta*fps)), int(round(tb*fps))
        cover = [s for s in segs if s.a < fb and s.b > fa]
        if any("_to_" in s.canon or s.canon in RAD for s in cover):
            log(ds, "candidate_not_applied", {}, dict(label=kind, start=t2s(ta), end=t2s(tb), frames=f"{fa}-{fb}"),
                "strict event overlaps a transition/radial segment; not carved automatically. " + fmt_rad(d)); continue
        for s in cover:   # split the containing stable segment(s)
            old = od(s); left = Seg(s.start_s, ta, s.raw, fps, s.orig); right = Seg(tb, s.end_s, s.raw, fps, s.orig)
            if s.strs: left.strs = (s.strs[0], t2s(ta)); right.strs = (t2s(tb), s.strs[1])
            segs.remove(s)
            for part in (left, right):
                if part.b - part.a >= MIN_STEADY_RUN * fps: part.notes.append("split"); segs.append(part)
            log(ds, "split", old, dict(label=s.raw, frames=" + ".join(f"{p.a}-{p.b}" for p in (left, right) if p.b - p.a >= MIN_STEADY_RUN*fps)),
                f"split around new {kind} {fa}-{fb}")
        ns = Seg(ta, tb, WORD[kind], fps, []); ns.notes.append("new"); segs.append(ns)
        log(ds, "new_event", {}, od(ns), "strict rapid event (fast, polarization broken, speed burst): " + fmt_rad(d)
            + ("; inside gap" if not cover else f"; carved from {cover[0].raw}"))
    segs.sort(key=lambda s: (s.a, s.b))
    # ---------- 3. weak stable segments ----------
    for sg in list(segs):
        if sg.canon not in STABLE or "new" in sg.notes: continue
        a, b = sg.a, min(sg.b, T); st = steady[sg.canon][a:b]; f = float(st.mean())
        if f >= WEAK_FRAC: continue
        m = metrics(S, a, b); old = od(sg)
        closed = binary_closing(st, structure=np.ones(int(0.5*fps)))
        rr = [(a + x, a + y) for x, y in runs(closed, int(MIN_STEADY_RUN*fps))]
        if rr:
            segs.remove(sg); parts = []
            for x, y in rr:
                ta, tb = snap_in(x, y, fps)
                if tb - ta < MIN_STEADY_RUN: continue
                p = Seg(ta, tb, sg.raw, fps, sg.orig); p.notes.append("weak-trimmed"); segs.append(p); parts.append(p)
            typ = "split" if len(parts) > 1 else "boundary_trim"
            if not parts:
                log(ds, "removed", old, {}, f"weak {sg.canon}: steady {f:.0%}, no clear run >= {MIN_STEADY_RUN}s after grid snap; P {m['P']:.2f}, M {m['M']:.2f}"); continue
            log(ds, typ, old, dict(label=sg.raw, frames=" + ".join(f"{p.a}-{p.b}" for p in parts),
                                   start=" + ".join(p.out()["start"] for p in parts), end=" + ".join(p.out()["end"] for p in parts)),
                f"weak {sg.canon} (steady {f:.0%}; P {m['P']:.2f}, M {m['M']:.2f}): kept only the clear part(s)", steady_frac=f)
            continue
        share = {k: float(v[a:b].mean()) for k, v in steady.items() if k != sg.canon}; best = max(share, key=share.get)
        if share[best] >= 0.6:
            sg.set_label(best); sg.notes.append("relabelled")
            log(ds, "relabel", old, od(sg), f"weak {old['label']} (steady {f:.0%}); {share[best]:.0%} of frames steady {best}; P {m['P']:.2f}, M {m['M']:.2f}")
        else:
            segs.remove(sg)
            log(ds, "removed", old, {}, f"weak {sg.canon}: steady {f:.0%}, no other state >= 60% ({best} {share[best]:.0%}); P {m['P']:.2f}, M {m['M']:.2f} -> leave unlabelled")
    fix_transitions(); segs[:] = [s for s in segs if "REMOVE" not in s.notes]; merge()
    # ---------- 4. trim stable segments to the steady core ----------
    hold = int(EDGE_HOLD * fps)
    for sg in list(segs):
        if sg.canon not in STABLE: continue
        a, b = sg.a, min(sg.b, T); st = steady[sg.canon][a:b]
        if len(st) < hold: continue
        ok = np.convolve(st.astype(int), np.ones(hold, int), "valid") == hold   # window [i, i+hold) all steady
        if not ok.any():
            continue
        na = a + int(np.argmax(ok)); nb = a + int(len(ok) - 1 - np.argmax(ok[::-1])) + hold
        ta, tb = snap_in(na, nb, fps)
        oa, ob = sg.a / fps, sg.b / fps
        ta = max(ta, oa) if ta - oa >= 0.5 - 1e-9 else oa
        tb = min(tb, ob) if ob - tb >= 0.5 - 1e-9 else ob
        if ta == oa and tb == ob: continue
        if tb - ta < 1.0: continue
        old = od(sg); keep_s = sg.strs
        sg.set_bounds(ta, tb)
        if keep_s:   # keep his exact string on the untouched side
            sg.strs = (keep_s[0] if ta == oa else t2s(ta), keep_s[1] if tb == ob else t2s(tb))
        m = metrics(S, a, b)
        log(ds, "boundary_trim", old, od(sg), f"trimmed to steady {sg.canon} ({STEADY_TXT[sg.canon]} held >= {EDGE_HOLD}s at edges): "
            f"start {sg.a - a:+d} fr ({(sg.a - a)/fps:+.1f}s), end {sg.b - b:+d} fr ({(sg.b - b)/fps:+.1f}s); edge P/M before trim "
            f"{S['P'][a]:.2f}/{S['M'][a]:.2f} .. {S['P'][b-1]:.2f}/{S['M'][b-1]:.2f}")
    # ---------- 5. gaps of the ORIGINAL annotation: clear behaviour only ----------
    segs.sort(key=lambda s: (s.a, s.b))
    cov = np.zeros(T, bool)
    for s in segs: cov[s.a:min(s.b, T)] = True
    gaps = runs(~orig_cov, int(1.0*fps))
    for ga, gb in gaps:
        free = ~cov[ga:gb]
        added = False
        for lab in STABLE:
            mask = steady[lab][ga:gb] & free
            if lab == "milling": mask &= (S["M"][ga:gb] >= 0.65) | (S["P"][ga:gb] < 0.35)   # clear milling only
            for x, y in runs(mask, int(MIN_NEW_GAP * fps)):
                ta, tb = snap_in(ga + x, ga + y, fps)
                if tb - ta < MIN_NEW_GAP: continue
                ns = Seg(ta, tb, WORD[lab], fps, []); ns.notes.append("new"); segs.append(ns); cov[ns.a:ns.b] = True; added = True
                m = metrics(S, ns.a, ns.b)
                log(ds, "new_from_gap", {}, od(ns), f"gap {ga}-{gb}: {tb-ta:.1f}s continuous steady {lab}; P {m['P']:.2f}, M {m['M']:.2f}")
        if added: continue
        # clear transition filling a short gap between two different stable states
        prv = [s for s in segs if s.b <= ga + 2 and abs(s.b - ga) <= 2]; nxt = [s for s in segs if abs(s.a - gb) <= 2]
        if prv and nxt and (gb - ga) <= 6*fps:
            A, B = prv[-1].canon, nxt[0].canon
            if A in STABLE and B in STABLE and A != B:
                sa = {k: float(steady[k][ga:ga+int(fps)].mean()) for k in (A, B)}; sb = {k: float(steady[k][gb-int(fps):gb].mean()) for k in (A, B)}
                if sa[A] > sa[B] and sb[B] > sb[A] and sa[A] >= 0.5 and sb[B] >= 0.5:
                    ta, tb = snap_in(ga, gb, fps)
                    ns = Seg(ta, tb, f"{WORD[A]} to {WORD[B]}", fps, []); ns.notes.append("new"); segs.append(ns); cov[ns.a:ns.b] = True
                    log(ds, "new_from_gap", {}, od(ns), f"gap {ga}-{gb} between {A} and {B}: starts {sa[A]:.0%} steady {A}, ends {sb[B]:.0%} steady {B}")
    # ---------- write ----------
    segs.sort(key=lambda s: (s.a, s.b))
    for i in range(1, len(segs)):
        assert segs[i].a >= segs[i-1].b - 1, (ds, segs[i-1].out(), segs[i].out())
    # transitions whose stable neighbour disappeared: kept (rule 3) but flagged
    for i, s in enumerate(segs):
        if "_to_" not in s.canon: continue
        A, B = s.canon.split("_to_")
        W5 = int(5*fps)   # a trimmed neighbour within 5 s still counts
        has_prev = any(0 <= s.a - x.b <= W5 and x.canon == A for x in segs); has_next = any(0 <= x.a - s.b <= W5 and x.canon == B for x in segs)
        if not (has_prev and has_next):
            s.notes.append("flag")
            log(ds, "unchanged_flagged" if s.strs and len(s.orig) == 1 else "note", od(s), od(s),
                "transition kept as is (rule 3) but " + ("its 'from' state segment is not adjacent any more" if not has_prev else "") +
                (" and " if not (has_prev or has_next) else "") + ("its 'to' state segment is not adjacent any more" if not has_next else "") +
                " (trimmed/removed neighbour or original gap)")
    for s in segs:
        if not s.notes and len(s.orig) == 1:
            log(ds, "unchanged", od(s), od(s), "")
    for k, s in enumerate(segs):
        o = s.out(); m = metrics(S, s.a, min(s.b, T))
        final_rows.append(dict(dataset=ds, new_seg=k, label=s.raw, canon=s.canon, start=o["start"], end=o["end"], a=s.a, b=s.b,
                               orig=";".join(map(str, s.orig)), notes=";".join(s.notes), P=round(m["P"], 3), M=round(m["M"], 3), rate=round(m["rate"], 3)))
    outj = dict(dataset=ann["dataset"], fps=ann["fps"], source=ann["source"], segments=[s.out() for s in segs])
    (OUT/"annotations"/f"{ds}_motion.json").write_text(json.dumps(outj, indent=2) + "\n")
    print(ds, "orig", len(ann["segments"]), "-> revised", len(segs), flush=True)


pd.DataFrame(changes).to_csv(OUT/"changes_steps.csv", index=False)
pd.DataFrame(final_rows).to_csv(OUT/"final_segments.csv", index=False)
pd.DataFrame(radial_rows).to_csv(OUT/"radial_recheck.csv", index=False)
