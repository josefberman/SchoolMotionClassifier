"""Per-frame order parameters + tracking-quality signals for every dataset -> cache/<id>.npz"""
import time
import numpy as np
from scipy.spatial import ConvexHull, cKDTree
from common import IDS, load_ds, REVIEW
from src.features.order_params import compute_order_params_series   # repo Φ features

def extra_metrics(pos, vel):
    T, N, _ = pos.shape
    sp = np.linalg.norm(vel, axis=-1)
    hv = np.where(sp[..., None] > 1e-9, vel / np.maximum(sp[..., None], 1e-12), 0.0)
    c = pos.mean(1, keepdims=True); q = pos - c
    qn = np.linalg.norm(q, axis=-1); rh = q / np.maximum(qn[..., None], 1e-12)
    cross = rh[..., 0]*hv[..., 1] - rh[..., 1]*hv[..., 0]
    M_signed = cross.mean(1)                                   # Tunstrom rotation order (signed)
    M = np.abs(M_signed)
    u = vel - vel.mean(1, keepdims=True)
    vrad = (u*rh).sum(-1).mean(1)                              # px/frame, + = outward
    R = qn.mean(1)                                             # mean distance to centroid
    hull = np.zeros(T); nnd = np.zeros(T); close = np.zeros(T, int)
    for t in range(T):
        p = pos[t]
        try: hull[t] = ConvexHull(p).volume
        except Exception: hull[t] = np.nan
        tr = cKDTree(p); d, _ = tr.query(p, k=2); nnd[t] = d[:, 1].mean()
        close[t] = len(tr.query_pairs(3.0))                    # pairs < 3 px: merged tracks / swap risk
    return dict(M_tun=M, M_signed=M_signed, vrad=vrad, vrad_norm=vrad/np.maximum(sp.mean(1), 1e-9),
                R=R, hull=hull, nnd=nnd, speed=sp.mean(1), close_pairs=close)

def quality(pos, vel):
    T, N, _ = pos.shape
    step = np.zeros((T, N)); step[1:] = np.linalg.norm(np.diff(pos, axis=0), axis=-1)
    sp = np.linalg.norm(vel, axis=-1)
    med = np.median(step[1:]); q999 = np.quantile(step[1:], 0.999)
    jump_thr = max(10*med, q999, 10.0)
    jump = step > jump_thr
    frozen = np.zeros((T, N), bool); frozen[1:] = step[1:] < 1e-9           # held position (dropout fill)
    d2 = np.zeros((T, N)); d2[1:-1] = np.linalg.norm(pos[2:] - 2*pos[1:-1] + pos[:-2], axis=-1)
    linear = (d2 < 1e-6) & (step > 1e-9)                                     # exactly linear = interpolated
    mism = np.zeros((T, N)); mism[1:] = np.linalg.norm(vel[1:] - (pos[1:]-pos[:-1]), axis=-1)
    # identity-swap candidates: >=2 fish jump in same frame and one lands near another's old spot
    swap = np.zeros(T, int)
    for t in np.where(jump.sum(1) >= 2)[0]:
        js = np.where(jump[t])[0]
        for i in js:
            dd = np.linalg.norm(pos[t-1, js] - pos[t, i], axis=-1)
            if np.any((dd < jump_thr) & (js != i)): swap[t] += 1
    return dict(n_jump=jump.sum(1), n_frozen=frozen.sum(1), n_linear=linear.sum(1),
                n_zero_vel=(sp < 1e-9).sum(1), vel_mismatch=np.median(mism, 1), n_swap=swap,
                jump_thr=np.array(jump_thr), step_median=np.array(med))

for ds in IDS:
    t0 = time.time()
    pos, vel, fps = load_ds(ds)
    out = {k: v for k, v in compute_order_params_series(pos, vel).items()}
    out.update(extra_metrics(pos, vel)); out.update(quality(pos, vel))
    out["fps"] = np.array(fps); out["n_fish"] = np.array(pos.shape[1])
    np.savez_compressed(REVIEW/"cache"/f"{ds}.npz", **out)
    print(ds, pos.shape, f"{time.time()-t0:.0f}s", "jump_thr", float(out["jump_thr"]), "jumps", int(out["n_jump"].sum()),
          "frozen", int(out["n_frozen"].sum()), "linear", int(out["n_linear"].sum()), "swapc", int(out["n_swap"].sum()),
          "closepair-frames", int((out["close_pairs"]>0).sum()), "velmis med", float(np.median(out["vel_mismatch"])), flush=True)
