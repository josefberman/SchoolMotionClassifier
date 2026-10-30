"""Timeline figures per dataset + trajectory snapshots per segment."""
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np, pandas as pd
from scipy.ndimage import uniform_filter1d
from common import IDS, REVIEW, load_cache, load_ds

COL = {"traveling": "#1f77b4", "milling": "#2ca02c", "shoaling": "#ff7f0e", "expansion": "#d62728", "compaction": "#9467bd"}
VCOL = {"agree": "#2ca02c", "questionable": "#ffbf00", "disagree": "#d62728"}
FIG = REVIEW/"figures"; (FIG/"segments").mkdir(parents=True, exist_ok=True)
seg = pd.read_csv(REVIEW/"segment_review.csv", dtype={"dataset": str})
bnd = pd.read_csv(REVIEW/"boundary_review.csv", dtype={"dataset": str})
evt = pd.read_csv(REVIEW/"radial_events.csv", dtype={"dataset": str})
gaps = pd.read_csv(REVIEW/"gaps_review.csv", dtype={"dataset": str})
sm = lambda x, w=15: uniform_filter1d(np.nan_to_num(x, nan=np.nanmean(x)), w, mode="nearest")

def band(ax, r, y0, h):
    if "_to_" in r.label:
        A, B = r.label.split("_to_")
        ax.axvspan(r.start, r.end, ymin=y0 + h/2, ymax=y0 + h, color=COL[A], alpha=.55, lw=0)
        ax.axvspan(r.start, r.end, ymin=y0, ymax=y0 + h/2, color=COL[B], alpha=.55, lw=0)
    else:
        ax.axvspan(r.start, r.end, ymin=y0, ymax=y0 + h, color=COL[r.label], alpha=.8, lw=0)

def timeline(ds, chunk_s=90):
    c = load_cache(ds); fps = float(c["fps"]); T = len(c["phi_trans"]); t = np.arange(T)
    P, M = sm(c["phi_trans"]), sm(c["M_tun"])
    rate = sm(np.gradient(np.log(sm(c["R"], 5))) * fps); prad = sm(c["phi_rad_pm"])
    S = seg[seg.dataset == ds]; Bd = bnd[(bnd.dataset == ds)]; E = evt[(evt.dataset == ds) & evt.robust & evt.strong & evt.unannotated]
    G = gaps[(gaps.dataset == ds) & gaps.kind.str.startswith("gap")]
    nch = int(np.ceil(T / (chunk_s*fps)))
    fig, axs = plt.subplots(nch*3, 1, figsize=(18, 3.1*nch*1.25), gridspec_kw=dict(height_ratios=[3, 2, 1.1]*nch, hspace=0.12))
    for k in range(nch):
        a, b = int(k*chunk_s*fps), int(min(T, (k+1)*chunk_s*fps))
        a1, a2, a3 = axs[3*k], axs[3*k+1], axs[3*k+2]
        a1.plot(t[a:b], P[a:b], c="k", lw=1, label="polarization P (=Φ_trans)")
        a1.plot(t[a:b], M[a:b], c="g", lw=1, label="rotation M (Tunstrom)")
        for y in (0.35, 0.65): a1.axhline(y, c="0.5", ls=":", lw=.8)
        a1.set_ylim(0, 1); a1.set_ylabel("order"); a1.set_xlim(a, b)
        a2.plot(t[a:b], np.clip(rate[a:b], -1, 1), c="m", lw=1, label="d log R/dt [1/s]")
        a2.plot(t[a:b], prad[a:b], c="c", lw=.8, label="Φ_rad± (repo)")
        a2.axhline(0, c="0.5", lw=.6); a2.set_ylim(-0.8, 0.8); a2.set_ylabel("radial"); a2.set_xlim(a, b)
        for _, e in E[(E.end > a) & (E.start < b)].iterrows():
            for ax in (a1, a2): ax.axvspan(e.start, e.end, color="k", alpha=.12, hatch="//", lw=0)
        for _, r in S[(S.end > a) & (S.start < b)].iterrows():
            band(a3, r, 0.35, 0.65)
            a3.axvspan(r.start, r.end, ymin=0, ymax=0.3, color=VCOL[r.verdict], alpha=.9, lw=0)
            if r.end - r.start > 0.04*(b - a) and "_to_" not in r.label:
                a3.text((r.start + r.end)/2, 0.68, f"{r.seg}", ha="center", va="center", fontsize=7, weight="bold")
        for _, g in G[(G.end > a) & (G.start < b)].iterrows():
            a3.axvspan(g.start, g.end, ymin=0.35, ymax=1, color="white", hatch="xx", ec="0.6", lw=0)
        for _, x in Bd[(Bd.frame >= a) & (Bd.frame < b)].iterrows():
            if x.status == "shift_suggested":
                for ax in (a1, a2, a3): ax.axvline(x.suggested_frame, c="r", ls="--", lw=1)
            elif str(x.status).startswith("shift_possible"):
                for ax in (a1, a2): ax.axvline(x.suggested_frame, c="orange", ls=":", lw=.9)
        a3.set_yticks([]); a3.set_xlim(a, b); a3.set_ylim(0, 1)
        ticks = np.arange(a - a % int(10*fps), b, int(10*fps)); ticks = ticks[ticks >= a]
        for ax in (a1, a2): ax.set_xticks(ticks); ax.set_xticklabels([])
        a3.set_xticks(ticks); a3.set_xticklabels([f"{x}\n{int(x/fps)//60:02d}:{x/fps%60:04.1f}" for x in ticks], fontsize=7)
    h = [Patch(color=v, label=k) for k, v in COL.items()] + [Patch(color=v, label="verdict: " + k) for k, v in VCOL.items()]
    h += [Patch(facecolor="white", hatch="xx", ec="0.6", label="unannotated gap"), Patch(color="k", alpha=.15, hatch="//", label="unannotated robust radial event"),
          plt.Line2D([], [], c="r", ls="--", label="suggested boundary (2 methods agree)"), plt.Line2D([], [], c="orange", ls=":", label="possible boundary (1 method)")]
    h += axs[0].get_legend_handles_labels()[0] + axs[1].get_legend_handles_labels()[0]
    fig.subplots_adjust(top=1 - 0.9/(3.1*nch*1.25), bottom=0.01)
    fig.legend(handles=h, loc="upper center", ncol=7, fontsize=8, bbox_to_anchor=(0.5, 1 - 0.1/(3.1*nch*1.25)))
    fig.text(0.5, 1 - 0.02/(3.1*nch*1.25), f"Dataset {ds} ({int(c['n_fish'])} fish) — order parameters vs annotation (transitions: top half = from, bottom half = to; segment ids in strip)", ha="center", fontsize=12)
    out = FIG/f"timeline_{ds}.png"; fig.savefig(out, dpi=80, bbox_inches="tight"); plt.close(fig); return out

def snapshots(pos, vel, fps, frames, titles, fname, header, P, M, R):
    fig, axs = plt.subplots(1, len(frames), figsize=(3.4*len(frames), 3.8))
    cs = [pos[f].mean(0) for f in frames]
    half = max(np.max(np.abs(pos[f] - cs[i])) for i, f in enumerate(frames)) * 1.15 + 5
    for ax, f, ttl, cen in zip(axs, frames, titles, cs):
        tr = pos[max(0, f-15):f+1]
        for i in range(pos.shape[1]): ax.plot(tr[:, i, 0], tr[:, i, 1], c="0.75", lw=.6)
        sp = np.linalg.norm(vel[f], axis=-1, keepdims=True); hv = np.nan_to_num(vel[f] / np.maximum(sp, 1e-9))
        ax.quiver(pos[f, :, 0], pos[f, :, 1], hv[:, 0], hv[:, 1], color="#1f77b4", scale=18, width=.006)
        ax.scatter(pos[f, :, 0], pos[f, :, 1], s=6, c="k", zorder=3)
        ax.plot(*cen, marker="*", c="r", ms=12, zorder=4)
        ax.set_xlim(cen[0]-half, cen[0]+half); ax.set_ylim(cen[1]-half, cen[1]+half); ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{ttl}\nfr {f} ({int(f/fps)//60:02d}:{f/fps%60:04.1f})  P={P[f]:.2f} M={M[f]:.2f} R={R[f]:.0f}", fontsize=8)
    fig.suptitle(header, fontsize=9); fig.tight_layout()
    fig.savefig(FIG/"segments"/fname, dpi=70); plt.close(fig)

def segment_figs(ds, rng):
    pos, vel, fps = load_ds(ds); c = load_cache(ds); T = pos.shape[0]
    P, M, R = sm(c["phi_trans"], 5), sm(c["M_tun"], 5), c["R"]
    S = seg[seg.dataset == ds]
    sel = S[S.verdict != "agree"]
    ag = S[S.verdict == "agree"]
    sel = pd.concat([sel, ag.sample(frac=1, random_state=rng).drop_duplicates("label")])
    n = 0
    for _, r in sel.iterrows():
        d = int(1.0*fps)
        fr = [max(0, r.start - d), r.start, (r.start + min(r.end, T-1))//2, min(r.end, T-1), min(T-1, r.end + d)]
        tt = ["1 s before start", "annotated start", "middle", "annotated end", "1 s after end"]
        hdr = f"{ds} seg {r.seg}: {r.raw_label} → {r.label}  [{r.start}-{r.end}, {r.dur_s}s]  verdict={r.verdict}: {r.reason}"
        if isinstance(r.evt_unannotated_inside, str) and r.evt_unannotated_inside: hdr += f"\nunannotated: {r.evt_unannotated_inside}"
        hdr += f"\nboundary start: {r.start_status} ({r.start_offset_s:+}s), end: {r.end_status} ({r.end_offset_s:+}s)"
        snapshots(pos, vel, fps, fr, tt, f"{ds}_seg{r.seg:03d}_{r.label}_{r.verdict}.png", hdr, P, M, R); n += 1
    E = evt[(evt.dataset == ds) & evt.robust & evt.strong & evt.unannotated].sort_values("dlogR", key=abs, ascending=False).head(4)
    for _, e in E.iterrows():
        d = int(1.0*fps)
        fr = [max(0, e.start - d), e.start, (e.start + e.end)//2, e.end, min(T-1, e.end + d)]
        snapshots(pos, vel, fps, fr, ["1 s before", "event start", "middle", "event end", "1 s after"],
                  f"{ds}_unannotated_{e.kind}_{e.start}-{e.end}.png",
                  f"{ds} UNANNOTATED {e.kind} {e.start}-{e.end} ({e.dur_s}s) dlogR={e.dlogR:+.2f} hull={e.dlogHull:+.2f} NND={e.dlogNND:+.2f}; "
                  f"{e.frac_fish_moving_with_event:.0%} of fish move {'out' if e.kind=='expansion' else 'in'}\ninside: {e.overlapping_labels}", P, M, R); n += 1
    return n

if __name__ == "__main__":
    ids = sys.argv[1:] or IDS
    for ds in ids:
        print(timeline(ds), segment_figs(ds, 0), flush=True)
