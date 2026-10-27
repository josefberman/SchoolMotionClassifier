"""Before/after timelines + snapshots for every relabelled or new expansion/compaction."""
import sys, json, textwrap
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np, pandas as pd
from scipy.ndimage import uniform_filter1d
from common import IDS, REVIEW, ROOT, load_cache, load_ds
from src.labels import canonicalize
from src.sim.io import mmss_to_frame
OUT = REVIEW/"revised"; FIG = OUT/"figures"; (FIG/"snapshots").mkdir(parents=True, exist_ok=True)
COL = {"traveling": "#1f77b4", "milling": "#2ca02c", "shoaling": "#ff7f0e", "expansion": "#d62728", "compaction": "#9467bd"}
sm = lambda x, w=15: uniform_filter1d(np.nan_to_num(x, nan=np.nanmedian(x)), w, mode="nearest")
ch = pd.read_csv(OUT/"changes.csv", dtype={"dataset": str})

def segs(path, fps):
    j = json.loads(Path(path).read_text())
    return [(mmss_to_frame(s["start"], fps), mmss_to_frame(s["end"], fps), canonicalize(s["label"]), s["label"]) for s in j["segments"]]

def band(ax, a, b, lab, y0, h):
    if "_to_" in lab:
        A, B = lab.split("_to_")
        ax.axvspan(a, b, ymin=y0 + h/2, ymax=y0 + h, color=COL[A], alpha=.55, lw=0); ax.axvspan(a, b, ymin=y0, ymax=y0 + h/2, color=COL[B], alpha=.55, lw=0)
    else: ax.axvspan(a, b, ymin=y0, ymax=y0 + h, color=COL[lab], alpha=.85, lw=0)

def timeline(ds, chunk_s=90):
    c = load_cache(ds); fps = float(c["fps"]); T = len(c["phi_trans"]); t = np.arange(T)
    P, M = sm(c["phi_trans"]), sm(c["M_tun"]); rate = sm(np.gradient(np.log(sm(c["R"], 5))) * fps); spd = sm(c["speed"], 5)
    old = segs(ROOT/"annotations"/f"{ds}_motion.json", fps); new = segs(OUT/"annotations"/f"{ds}_motion.json", fps)
    nch = int(np.ceil(T / (chunk_s*fps)))
    fig, axs = plt.subplots(nch*3, 1, figsize=(18, 3.3*nch*1.25), gridspec_kw=dict(height_ratios=[3, 2, 1.6]*nch, hspace=0.12))
    for k in range(nch):
        a, b = int(k*chunk_s*fps), int(min(T, (k+1)*chunk_s*fps)); a1, a2, a3 = axs[3*k:3*k+3]
        a1.plot(t[a:b], P[a:b], c="k", lw=1, label="polarization P"); a1.plot(t[a:b], M[a:b], c="g", lw=1, label="rotation M")
        for y in (0.35, 0.5, 0.65): a1.axhline(y, c="0.6", ls=":", lw=.7)
        a1.set_ylim(0, 1); a1.set_xlim(a, b); a1.set_ylabel("order")
        a2.plot(t[a:b], np.clip(rate[a:b], -1, 1), c="m", lw=1, label="d log R/dt [1/s]")
        a2b = a2.twinx(); a2b.plot(t[a:b], spd[a:b] / np.nanmedian(spd), c="0.5", lw=.7); a2b.set_ylim(0, 3); a2b.set_yticks([1, 2])
        a2.axhline(0, c="0.6", lw=.6); a2.set_ylim(-0.8, 0.8); a2.set_xlim(a, b); a2.set_ylabel("dlogR/dt\n(grey: speed/median)", fontsize=7)
        for x0, x1, lab, raw in old:
            if x1 > a and x0 < b: band(a3, x0, x1, lab, 0.53, 0.45)
        for x0, x1, lab, raw in new:
            if x1 > a and x0 < b: band(a3, x0, x1, lab, 0.02, 0.45)
        a3.text(a, 0.75, " original", fontsize=7, va="center"); a3.text(a, 0.25, " revised", fontsize=7, va="center")
        a3.set_yticks([]); a3.set_ylim(0, 1); a3.set_xlim(a, b)
        ticks = np.arange(a - a % int(10*fps), b, int(10*fps)); ticks = ticks[ticks >= a]
        for ax in (a1, a2): ax.set_xticks(ticks); ax.set_xticklabels([])
        a3.set_xticks(ticks); a3.set_xticklabels([f"{x}\n{int(x/fps)//60:02d}:{x/fps%60:04.1f}" for x in ticks], fontsize=7)
    h = [Patch(color=v, label=k) for k, v in COL.items()] + axs[0].get_legend_handles_labels()[0] + axs[1].get_legend_handles_labels()[0]
    H = 3.3*nch*1.25
    fig.subplots_adjust(top=1 - 0.9/H, bottom=0.01)
    fig.legend(handles=h, loc="upper center", ncol=8, fontsize=8, bbox_to_anchor=(0.5, 1 - 0.1/H))
    fig.text(0.5, 1 - 0.02/H, f"{ds}: original (upper strip) vs revised draft (lower strip); transitions: top half = from, bottom half = to", ha="center", fontsize=12)
    fig.savefig(FIG/f"before_after_{ds}.png", dpi=80, bbox_inches="tight"); plt.close(fig)

def snap(pos, vel, fps, frames, titles, fname, header, P, M, R, spd):
    fig, axs = plt.subplots(1, len(frames), figsize=(3.4*len(frames), 3.9))
    cs = [pos[f].mean(0) for f in frames]
    half = max(np.max(np.abs(pos[f] - cs[i])) for i, f in enumerate(frames)) * 1.15 + 5
    for ax, f, ttl, cen in zip(axs, frames, titles, cs):
        tr = pos[max(0, f-15):f+1]
        for i in range(pos.shape[1]): ax.plot(tr[:, i, 0], tr[:, i, 1], c="0.75", lw=.6)
        sp = np.linalg.norm(vel[f], axis=-1, keepdims=True); hv = np.nan_to_num(vel[f] / np.maximum(sp, 1e-9))
        ax.quiver(pos[f, :, 0], pos[f, :, 1], hv[:, 0], hv[:, 1], color="#1f77b4", scale=18, width=.006)
        ax.scatter(pos[f, :, 0], pos[f, :, 1], s=6, c="k", zorder=3); ax.plot(*cen, marker="*", c="r", ms=12, zorder=4)
        ax.set_xlim(cen[0]-half, cen[0]+half); ax.set_ylim(cen[1]-half, cen[1]+half); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{ttl}\nfr {f} ({int(f/fps)//60:02d}:{f/fps%60:04.1f}) P={P[f]:.2f} M={M[f]:.2f}\nR={R[f]:.0f} speed x{spd[f]:.2f}", fontsize=8)
    fig.suptitle(header, fontsize=8); fig.tight_layout(rect=[0, 0, 1, 0.80]); fig.savefig(FIG/"snapshots"/fname, dpi=70); plt.close(fig)

def snapshots(ds):
    sel = ch[(ch.dataset == ds) & (((ch.change_type == "relabel") & ch.old_label.isin(["expansion", "compaction"]))
                                   | (ch.change_type.str.startswith("new") & ch.new_label.isin(["expansion", "compaction"])))]
    if not len(sel): return 0
    pos, vel, fps = load_ds(ds); c = load_cache(ds); T = pos.shape[0]
    P, M, R = sm(c["phi_trans"], 5), sm(c["M_tun"], 5), c["R"]; spd = sm(c["speed"], 5) / np.nanmedian(c["speed"])
    for _, r in sel.iterrows():
        fr0 = r.old_frames if isinstance(r.old_frames, str) else r.new_frames
        a, b = map(int, fr0.split("-")); d = int(fps)
        frames = [max(0, a-d), a, (a+b)//2, min(b, T-1), min(T-1, b+d)]
        if isinstance(r.old_frames, str):
            name = f"{ds}_seg{int(r.old_seg):03d}_{r.old_label}_to_{str(r.new_label).split(' |')[0].replace(' ', '_')}.png"
            hdr = f"{ds} seg {int(r.old_seg)}: {r.old_label} [{r.old_frames}] -> {r.new_label} [{r.new_frames}]\n{textwrap.fill(str(r.reason), 200)}"
        else:
            name = f"{ds}_NEW_{r.new_label}_{r.new_frames}.png"; hdr = f"{ds} NEW {r.new_label} [{r.new_frames}] ({r.change_type})\n{textwrap.fill(str(r.reason), 200)}"
        snap(pos, vel, fps, frames, ["1 s before", "start", "middle", "end", "1 s after"], name, hdr, P, M, R, spd)
    return len(sel)

if __name__ == "__main__":
    for ds in (sys.argv[1:] or IDS):
        timeline(ds); print(ds, snapshots(ds), flush=True)
