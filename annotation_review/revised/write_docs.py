"""CHANGELOG.md + REPORT_v2.md for the second pass."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from common import IDS, REVIEW, META
OUT = REVIEW/"revised"
ch = pd.read_csv(OUT/"changes.csv", dtype={"dataset": str})
r = pd.read_csv(OUT/"radial_recheck.csv", dtype={"dataset": str, "seg": str})
val = pd.read_csv(OUT/"validation.csv", dtype={"dataset": str})
tails = pd.read_csv(OUT/"rate_tails.csv", dtype={"dataset": str})
ann = r[~r.seg.str.startswith("event")]; ev = r[r.seg.str.startswith("event")]
dec = ann.decision
n_clear = dec.str.startswith("-> traveling (clear")
n_trav = int(n_clear.sum())
n_trav_slow = int((dec.str.startswith("-> traveling") & ~n_clear).sum())
n_sh = int(dec.str.startswith("-> shoaling").sum()); n_keep = int(dec.str.startswith("kept (").sum()); n_border = int(dec.str.startswith("kept, borderline").sum())
fast_trav = int(ann[dec.str.startswith("-> traveling (clear")].fast.sum())
surv = ev[ev.decision.str.startswith("survives")]
steps = pd.read_csv(OUT/"changes_steps.csv", dtype={"dataset": str})
ne = steps[steps.change == "new_event"]; cna = steps[steps.change == "candidate_not_applied"]
def applied(s):
    h = ne[ne.dataset == s.dataset]
    if not len(h): return False
    fr = h.new_frames.str.split("-", expand=True).astype(int); return bool(((fr[0] < s.end) & (fr[1] > s.start)).any())
n_surv_applied = int(surv.apply(applied, axis=1).sum()) if len(surv) else 0
CT = ch.change_type.value_counts().to_dict()
def md(df):
    cols = list(df.columns); out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|"*len(cols)]
    for _, x in df.iterrows():
        out.append("| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else str(v).replace("|", "/").replace("\n", " ") for v in x.values) + " |")
    return "\n".join(out)
def trimmed(x):
    oa, ob = map(int, x.old_frames.split("-")); s = sum(int(b) - int(a) for a, b in (p.split("-") for p in x.new_frames.split(" | ")))
    return round((ob - oa - s) / 29.97, 1)

# ---------------- CHANGELOG ----------------
L = ["# CHANGELOG: draft revised annotations (second pass)\n",
     "Drop-in files: `revised/annotations/<id>_motion.json` (same schema as the originals: `json.dumps(indent=2)` + newline, same `dataset`/`fps`/`source`, his raw label words, 0.5 s timestamp grid). "
     "Frames are `mmss_to_frame(t, 29.97)`. Every original segment appears exactly once below. Machine-readable versions: `changes.csv` (one row per original segment plus one per new segment) and `changes_steps.csv` (every individual edit, in order).\n",
     "Change types: **relabel** (label changed; frames may also have been trimmed or merged), **boundary_trim** (same label, trimmed inward to the steady part), **split** (kept only the clear sub-parts), "
     "**merged** (absorbed into a neighbour with the same label after a relabel), **new_from_gap** / **new_event_in_segment** (new segments), **removed** (left unlabelled), **unchanged**. "
     "`flagged` = transition kept unchanged (rule 3) whose from/to state neighbour no longer sits next to it.\n"]
order = ["relabel", "boundary_trim", "split", "merged", "new_from_gap", "new_event_in_segment", "removed", "unchanged"]
for ds in IDS:
    d = ch[ch.dataset == ds]; vc = d.change_type.value_counts().to_dict()
    L.append(f"## {ds} ({META[ds]['fish_group']}): {val[val.dataset == ds].segments.iloc[0]} revised segments (from {int(d.old_seg.notna().sum())}); {vc}\n")
    for t in order:
        x = d[d.change_type == t]
        if not len(x): continue
        L.append(f"### {t} ({len(x)})\n")
        if t == "unchanged":
            fl = x[x.flagged == True]
            L.append("Segments: " + ", ".join(str(int(s)) for s in x.old_seg) + ".")
            if len(fl): L.append(f"\nFlagged (kept per rule 3, but a state neighbour was trimmed away, removed or relabelled; check): " + ", ".join(f"{int(s)} ({l})" for s, l in zip(fl.old_seg, fl.old_label)) + ".")
            L.append(""); continue
        if t.startswith("new"):
            L.append(md(x[["new_label", "new_start", "new_end", "new_frames", "reason"]].rename(columns={"reason": "reason / key metrics"}))); L.append(""); continue
        y = x.copy(); y["old"] = y.old_label + " " + y.old_frames
        y["new"] = y.new_label.fillna("—").astype(str) + " " + y.new_frames.fillna("").astype(str)
        if t == "boundary_trim": y["trimmed_s"] = y.apply(trimmed, axis=1)
        y["metrics"] = "P " + y.old_P.round(2).astype(str) + ", M " + y.old_M.round(2).astype(str) + ", dlogR " + y.old_dlogR.round(2).astype(str)
        cols = ["old_seg", "old", "new"] + (["trimmed_s"] if t == "boundary_trim" else []) + (["merged_with_orig"] if t == "merged" else []) + ["reason", "metrics"]
        y["old_seg"] = y.old_seg.astype(int); y["reason"] = y.reason.fillna("")
        if t == "merged": y["reason"] = y.reason.where(y.reason != "", "absorbed into a same-label neighbour after an adjacent relabel")
        L.append(md(y[cols])); L.append("")
(OUT/"CHANGELOG.md").write_text("\n".join(L) + "\n")

# ---------------- REPORT_v2 ----------------
bt = ch[ch.change_type == "boundary_trim"].copy(); bt["trim_s"] = bt.apply(trimmed, axis=1)
rl = ch[ch.change_type == "relabel"]
R = ["# Annotation review v2: draft corrected annotations\n",
     "This pass applies Josef's domain corrections to the first audit (`REPORT.md`). The output is a **draft** for him to review against video. It replaces nothing in the repo; all files live in `annotation_review/revised/`.\n",
     "## Summary\n",
     f"- **Strict expansion/compaction** (rapid, startle-like). Every condition is quantified:",
     f"  - *Fast*: the peak d log R/dt (R = mean distance to the centroid, 0.5 s smoothing) must reach the dataset's **95th percentile of |d log R/dt|**. That is {tails.absrate_p95.min():.2f}–{tails.absrate_p95.max():.2f} s⁻¹; it is group-size dependent, and 10-fish groups are noisier. In addition, |Δlog R| over the event must be **≥ 0.15** (≥16% spread change), with a duration of **≤ 6 s**.",
     "  - *Polarization low or broken*: mean P < 0.65, or min P < 0.50, or P drops ≥ 0.20 from the 1 s before.",
     "  - *Clear traveling*: ≥ 80% of event frames have P ≥ 0.65 and P never drops below 0.50. **Rule: clear traveling → `traveling`**, whether the spread change is fast or not.",
     "  - *Speed burst*: peak mean speed ≥ **1.3×** the trailing 5 s median. This is supporting evidence for annotated events and **required** for new ones. New events also need min P < 0.5 and mean P < 0.65.",
     f"- **Annotated expansion/compaction (194)**:",
     f"  - **{n_keep} survive** as rapid events with broken polarization.",
     f"  - **{n_border} are kept but flagged borderline**: polarization is broken but the spread change is slow or below the tail threshold. Check the video.",
     f"  - **{n_trav} become `traveling`** because they are clear traveling ({fast_trav} of them even had a fast spread change, but P stayed ≥ 0.65).",
     f"  - **{n_trav_slow}** become `traveling` because they are not rapid and ≥ 60% of frames are steady traveling. **{n_sh}** becomes `shoaling`.",
     f"  - By label: compaction {int((ann.label=='compaction').sum())} → {int(((ann.label=='compaction') & dec.str.startswith('kept')).sum())} kept / {int(((ann.label=='compaction') & dec.str.startswith('-> traveling')).sum())} traveling. Expansion {int((ann.label=='expansion').sum())} → {int(((ann.label=='expansion') & dec.str.startswith('kept')).sum())} kept / {int(((ann.label=='expansion') & dec.str.startswith('-> traveling')).sum())} traveling / {int(((ann.label=='expansion') & dec.str.startswith('-> shoaling')).sum())} shoaling.",
     f"- **The 138 'missed' events from v1**: {len(surv)} survive the strict definition, and {n_surv_applied} of them were added as segments (the others overlap a transition or an already-annotated radial segment and are listed as candidates, not applied). "
     f"{int(ev.decision.str.startswith('fails: clear').sum())} were clear traveling and {int((ev.decision=='fails strict').sum())} failed another criterion. **v1 bullet 1 is withdrawn**: most of those events are spread drift while traveling.",
     f"- **New segments**: {CT.get('new_from_gap',0)} from gaps ({int((ch.change_type.eq('new_from_gap') & ch.new_label.isin(['expansion','compaction'])).sum())} strict exp/comp events, the rest steady states ≥ 3 s). Plus {CT.get('new_event_in_segment',0)} strict exp/comp events carved out of stable segments. {len(cna)} further strict candidates overlap transitions and were *not* applied; they are listed in `changes_steps.csv` as `candidate_not_applied`. No gap transition qualified.",
     f"- **Boundary trims**: {len(bt)} original stable segments were trimmed inward only (median {bt.trim_s.median():.1f} s, IQR {bt.trim_s.quantile(.25):.1f}–{bt.trim_s.quantile(.75):.1f} s). Another {CT.get('split',0)} were split into their clear parts. Steady criteria: traveling P ≥ 0.65; milling M ≥ 0.50 and P ≤ 0.50; shoaling P < 0.40 and M < 0.40. The criterion must hold for ≥ 1 s at each new edge, and edges are snapped *inward* to the 0.5 s grid. Freed frames are left unlabelled; transitions are never extended.",
     f"- **Relabels**: {len(rl)} original segments changed label:",
     f"  - {int((rl.old_label.isin(['expansion','compaction'])).sum())} expansion/compaction segments.",
     f"  - {int((rl.old_label.str.contains(' to ') & ~rl.new_label.astype(str).str.contains(' to ')).sum())} transitions that became `traveling` once both sides were traveling.",
     f"  - {int((rl.old_label.str.contains(' to ') & rl.new_label.astype(str).str.contains(' to ')).sum())} transitions renamed because a neighbour changed, e.g. `compaction to shoaling` → `traveling to shoaling`.",
     f"- **Merged**: {CT.get('merged',0)} segments were absorbed into a same-label neighbour.",
     f"- **Removed**: {CT.get('removed',0)} left unlabelled. These are weak stable segments with no clear part ≥ 2 s and no other state on ≥ 60% of frames, plus transitions that no longer had a state change. **Unchanged**: {CT.get('unchanged',0)}.",
     f"- **Segment count**: {int(ch.old_seg.notna().sum())} → {int(val.segments.sum())}. No `mixed` label is used. Every file parses with `src.features.dataset.load_real_segments` and every label maps through `src.labels.canonicalize` (`validation.csv`). {int(val.under_15_frames.sum())} segment is < 15 frames: an untouched original 14-frame transition (rule 3), noted only.",
     "",
     "## Case-by-case: weak long segments named by Josef\n"]
def fate(ds, s):
    x = ch[(ch.dataset == ds) & (ch.old_seg == s)].iloc[0]
    return f"{x.change_type}: {x.old_label} {x.old_frames} → {x.new_label if isinstance(x.new_label, str) else '(unlabelled)'} {x.new_frames if isinstance(x.new_frames, str) else ''}. {x.reason if isinstance(x.reason, str) else ''}"
R += [f"- **0124 seg 0, milling (96.5 s)**: {fate('0124', 0)} Kept. M = 0.61 and P = 0.15 throughout, with rotation clearly dominant: ≥ 60% of frames meet M ≥ 0.5 and P ≤ 0.5, and the edges are steady. It is 'weak' only against Tunström's 0.65. The same reasoning applies to 0124 seg 1 ({fate('0124', 1)}).",
      f"- **0084 seg 107, milling (25 s)**: {fate('0084', 107)} Only the 4.5 s with clear rotation is kept; the rest has M ≈ P ≈ 0.45 and is left unlabelled.",
      f"- **0066 seg 27, shoaling (19 s)**: {fate('0066', 27)} P ≈ 0.53 is neither swarm nor traveling, so it is left unlabelled rather than forced.",
      f"- **0124 seg 39, traveling (30.5 s, P = 0.64)**: {fate('0124', 39)}",
      f"- **0124 seg 56, traveling (24.5 s, P = 0.60)**: {fate('0124', 56)}",
      "",
      "## Most notable changes\n",
      f"1. **Compaction that is really traveling**: {int(((ann.label=='compaction') & dec.str.startswith('-> traveling')).sum())}/133 compactions become traveling. Example: 0126 seg 11 (4451–4525) has a fast spread drop (peak 0.26 s⁻¹, Δlog R −0.33) but P stays 0.73–0.87, so the school travels while tightening (`figures/snapshots/0126_seg011_compaction_to_traveling.png`).",
      "2. **0200, expansion placed too late**: the annotated expansion seg 60 (8871–8976) is polarized and not rapid, so it becomes traveling. The rapid break-up (peak speed ×1.38, P min 0.46) happens at **8781–8916**, during the original 'traveling to expansion' transition. A new expansion is placed there.",
      "3. **0126, new compaction in a gap at 13816–13906**: Δlog R −0.97 in 3.3 s, P drops from 0.83 to 0.36, speed ×1.68. This is the clearest unannotated startle.",
      "4. **0200, long clear states in gaps**: new shoaling 17008–17532 (17.5 s, P 0.24, M 0.23) and milling 14041–14550 (17 s, M 0.71).",
      "5. **0115, shoaling seg 45 (10460–10609) is really a compaction at 10504–10594**: P 0.05–0.2, Δlog R −0.58 in 3.8 s, speed ×1.48. The 1.5 s remnants are left unlabelled.",
      "",
      "## Caveats\n",
      "- This is a metrics-only draft. Every relabel and new exp/comp has a 5-panel snapshot in `revised/figures/snapshots/`. Borderline-kept events are flagged in `changes.csv` (`strict_decision`).",
      "- Thresholds are explicit constants at the top of `revised/revise.py`. The 95th-percentile tail is per dataset, so a 'fast' event in a 70-fish school is slower in absolute terms than in a 10-fish school.",
      "- Trimming leaves short unlabelled slivers between transitions and stable segments. That is intended (rule 2), but it reduces labelled time.",
      "",
      "## Files\n",
      "- `revised/annotations/<id>_motion.json` (10), `revised/CHANGELOG.md`, `revised/changes.csv`, `revised/changes_steps.csv`, `revised/radial_recheck.csv`, `revised/validation.csv`",
      "- `revised/figures/before_after_<id>.png` (10), `revised/figures/snapshots/*.png`",
      "- Scripts: `revised/radial_stats.py`, `revised/revise.py`, `revised/changelog.py`, `revised/plots_v2.py`, `revised/write_docs.py`"]
(REVIEW/"REPORT_v2.md").write_text("\n".join(R) + "\n")
print("\n".join(R[:40]))
