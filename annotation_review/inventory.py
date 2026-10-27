"""Inventory of annotations: raw labels, canonicalization, gaps/overlaps/short segments."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from src.labels import canonicalize, load_aliases
from src.sim.io import load_motion_json, mmss_to_frame

IDS = ["0066","0084","0103","0105","0107","0115","0120","0124","0126","0200"]
meta = json.load(open(ROOT/"annotations/datasets.json"))
aliases = load_aliases()
rows = []
for ds in IDS:
    ann = load_motion_json(ROOT/f"annotations/{ds}_motion.json")
    fps = float(ann.get("fps", meta[ds]["fps"]))
    assert ann["dataset"] == ds, (ds, ann["dataset"])
    for i, s in enumerate(ann["segments"]):
        try:
            lab = canonicalize(s["label"], aliases); err = ""
        except ValueError as e:
            lab = ""; err = str(e)
        a, b = mmss_to_frame(s["start"], fps), mmss_to_frame(s["end"], fps)
        rows.append(dict(dataset=ds, seg=i, raw_label=s["label"], label=lab, canon_error=err,
                         start_str=s["start"], end_str=s["end"], start=a, end=b, fps=fps,
                         group=meta[ds]["fish_group"], extra_keys=",".join(sorted(set(s)-{"start","end","label"}))))
df = pd.DataFrame(rows)
df.to_csv(Path(__file__).parent/"segments_inventory.csv", index=False)
print(df.groupby("dataset").size().to_dict())
print("canon errors:\n", df[df.canon_error!=""][["dataset","seg","raw_label","start_str","end_str"]].to_string())
print("raw->canon:\n", df.groupby(["raw_label","label"]).size().to_string())
print("nonpositive length:\n", df[df.end<=df.start][["dataset","seg","raw_label","start_str","end_str"]].to_string())
print("extra keys:", df.extra_keys.unique())
