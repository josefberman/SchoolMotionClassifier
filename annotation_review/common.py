"""Shared helpers for the annotation review (read-only use of repo code)."""
import sys, json
from pathlib import Path
REVIEW = Path(__file__).resolve().parent
ROOT = REVIEW.parent
sys.path.insert(0, str(ROOT))
import numpy as np
from src.sim.io import load_trajectory_table, pos_vel_from_table

IDS = ["0066","0084","0103","0105","0107","0115","0120","0124","0126","0200"]
META = json.load(open(ROOT/"annotations/datasets.json"))

def load_ds(ds):
    m = META[ds]
    df = load_trajectory_table(ROOT/"schooling-datasets"/m["fish_group"]/ds/f"{ds}_loc_vel_data.h5")
    pos, vel = pos_vel_from_table(df)
    return pos, vel, float(m["fps"])

def load_cache(ds):
    z = np.load(REVIEW/"cache"/f"{ds}.npz")
    return {k: z[k] for k in z.files}
