"""Separate real fast movements (startles) from tracking teleports: a position step above the jump threshold
that the velocity column does NOT support (|v| < 0.5*step) is counted as a teleport / tracking error."""
import numpy as np
from common import IDS, REVIEW, load_ds, load_cache
for ds in IDS:
    pos, vel, fps = load_ds(ds); c = load_cache(ds); thr = float(c["jump_thr"])
    step = np.zeros(pos.shape[:2]); step[1:] = np.linalg.norm(np.diff(pos, axis=0), axis=-1)
    sp = np.nan_to_num(np.linalg.norm(vel, axis=-1))
    jump = step > thr; tele = jump & (sp < 0.5*step)
    np.save(REVIEW/"cache"/f"{ds}_teleport.npy", tele.sum(1))
    print(ds, "jumps", int(jump.sum()), "teleports", int(tele.sum()), "fast-but-consistent", int((jump & ~tele).sum()))
