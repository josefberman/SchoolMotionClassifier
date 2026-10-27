import sys, json, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
from src.sim.io import load_trajectory_table, pos_vel_from_table
meta = json.load(open(ROOT/"annotations/datasets.json"))
for ds, m in meta.items():
    d = ROOT/"schooling-datasets"/m["fish_group"]/ds
    t0=time.time()
    h = load_trajectory_table(d/f"{ds}_loc_vel_data.h5")
    fr = np.arange(len(h))
    pos, vel = pos_vel_from_table(h)
    nan_pos = np.isnan(pos).any(-1)
    print(ds, m["fish_group"], pos.shape, "frames", fr[0], fr[-1], "contig", bool(np.all(np.diff(fr)==1)),
          "nan fish-frames", int(nan_pos.sum()), "frames w/ any nan", int(nan_pos.any(1).sum()),
          "zero-vel", int((np.linalg.norm(vel,axis=-1)<1e-9).sum()),
          "xrange", np.nanmin(pos[...,0]).round(0), np.nanmax(pos[...,0]).round(0),
          "speed med", np.nanmedian(np.linalg.norm(vel,axis=-1)).round(2), f"{time.time()-t0:.1f}s")
# csv vs h5 for small one
c = pd.read_csv(ROOT/"schooling-datasets/10_fish/0066/0066_loc_vel_data.csv")
h = load_trajectory_table(ROOT/"schooling-datasets/10_fish/0066/0066_loc_vel_data.h5")
print("csv==h5 0066:", c.shape, h.shape, np.allclose(c.drop(columns="frame").to_numpy(float), h[[x for x in c.columns if x!="frame"]].to_numpy(float), equal_nan=True))
print("csv frame contiguous", (c.frame.diff().dropna()==1).all(), c.frame.iloc[0])
