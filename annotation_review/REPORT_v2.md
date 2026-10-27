# Annotation review v2: draft corrected annotations

This pass applies Josef's domain corrections to the first audit (`REPORT.md`). The output is a **draft** for him to review against video. It replaces nothing in the repo; all files live in `annotation_review/revised/`.

## Summary

- **Strict expansion/compaction** (rapid, startle-like). Every condition is quantified:
  - *Fast*: the peak d log R/dt (R = mean distance to the centroid, 0.5 s smoothing) must reach the dataset's **95th percentile of |d log R/dt|**. That is 0.05–0.24 s⁻¹; it is group-size dependent, and 10-fish groups are noisier. In addition, |Δlog R| over the event must be **≥ 0.15** (≥16% spread change), with a duration of **≤ 6 s**.
  - *Polarization low or broken*: mean P < 0.65, or min P < 0.50, or P drops ≥ 0.20 from the 1 s before.
  - *Clear traveling*: ≥ 80% of event frames have P ≥ 0.65 and P never drops below 0.50. **Rule: clear traveling → `traveling`**, whether the spread change is fast or not.
  - *Speed burst*: peak mean speed ≥ **1.3×** the trailing 5 s median. This is supporting evidence for annotated events and **required** for new ones. New events also need min P < 0.5 and mean P < 0.65.
- **Annotated expansion/compaction (194)**:
  - **45 survive** as rapid events with broken polarization.
  - **33 are kept but flagged borderline**: polarization is broken but the spread change is slow or below the tail threshold. Check the video.
  - **107 become `traveling`** because they are clear traveling (63 of them even had a fast spread change, but P stayed ≥ 0.65).
  - **8** become `traveling` because they are not rapid and ≥ 60% of frames are steady traveling. **1** becomes `shoaling`.
  - By label: compaction 133 → 46 kept / 87 traveling. Expansion 61 → 32 kept / 28 traveling / 1 shoaling.
- **The 138 'missed' events from v1**: 16 survive the strict definition, and 11 of them were added as segments (the others overlap a transition or an already-annotated radial segment and are listed as candidates, not applied). 74 were clear traveling and 48 failed another criterion. **v1 bullet 1 is withdrawn**: most of those events are spread drift while traveling.
- **New segments**: 22 from gaps (7 strict exp/comp events, the rest steady states ≥ 3 s). Plus 7 strict exp/comp events carved out of stable segments. 6 further strict candidates overlap transitions and were *not* applied; they are listed in `changes_steps.csv` as `candidate_not_applied`. No gap transition qualified.
- **Boundary trims**: 67 original stable segments were trimmed inward only (median 1.5 s, IQR 1.0–4.0 s). Another 4 were split into their clear parts. Steady criteria: traveling P ≥ 0.65; milling M ≥ 0.50 and P ≤ 0.50; shoaling P < 0.40 and M < 0.40. The criterion must hold for ≥ 1 s at each new edge, and edges are snapped *inward* to the 0.5 s grid. Freed frames are left unlabelled; transitions are never extended.
- **Relabels**: 316 original segments changed label:
  - 116 expansion/compaction segments.
  - 170 transitions that became `traveling` once both sides were traveling.
  - 27 transitions renamed because a neighbour changed, e.g. `compaction to shoaling` → `traveling to shoaling`.
- **Merged**: 130 segments were absorbed into a same-label neighbour.
- **Removed**: 44 left unlabelled. These are weak stable segments with no clear part ≥ 2 s and no other state on ≥ 60% of frames, plus transitions that no longer had a state change. **Unchanged**: 385.
- **Segment count**: 946 → 591. No `mixed` label is used. Every file parses with `src.features.dataset.load_real_segments` and every label maps through `src.labels.canonicalize` (`validation.csv`). 1 segment is < 15 frames: an untouched original 14-frame transition (rule 3), noted only.

## Case-by-case: weak long segments named by Josef

- **0124 seg 0, milling (96.5 s)**: unchanged: milling 809-3701 → milling 809-3701.  Kept. M = 0.61 and P = 0.15 throughout, with rotation clearly dominant: ≥ 60% of frames meet M ≥ 0.5 and P ≤ 0.5, and the edges are steady. It is 'weak' only against Tunström's 0.65. The same reasoning applies to 0124 seg 1 (unchanged: milling 4870-6503 → milling 4870-6503. ).
- **0084 seg 107, milling (25 s)**: boundary_trim: milling 23526-24276 → milling 23661-23796. weak milling (steady 31%; P 0.42, M 0.47): kept only the clear part(s) Only the 4.5 s with clear rotation is kept; the rest has M ≈ P ≈ 0.45 and is left unlabelled.
- **0066 seg 27, shoaling (19 s)**: removed: shoaling 15225-15794 → (unlabelled) . weak shoaling: steady 21%, no other state >= 60% (traveling 17%); P 0.53, M 0.14 -> leave unlabelled P ≈ 0.53 is neither swarm nor traveling, so it is left unlabelled rather than forced.
- **0124 seg 39, traveling (30.5 s, P = 0.64)**: split: traveling 16783-17697 → traveling | traveling 17323-17458 | 17517-17682. weak traveling (steady 42%; P 0.64, M 0.29): kept only the clear part(s) / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +60 fr (+2.0s), end +0 fr (+0.0s); edge P/M before trim 0.66/0.32 .. 0.67/0.37
- **0124 seg 56, traveling (24.5 s, P = 0.60)**: merged: traveling 19900-20634 → traveling 19615-20125. weak traveling (steady 54%; P 0.66, M 0.08): kept only the clear part(s)

## Most notable changes

1. **Compaction that is really traveling**: 87/133 compactions become traveling. Example: 0126 seg 11 (4451–4525) has a fast spread drop (peak 0.26 s⁻¹, Δlog R −0.33) but P stays 0.73–0.87, so the school travels while tightening (`figures/snapshots/0126_seg011_compaction_to_traveling.png`).
2. **0200, expansion placed too late**: the annotated expansion seg 60 (8871–8976) is polarized and not rapid, so it becomes traveling. The rapid break-up (peak speed ×1.38, P min 0.46) happens at **8781–8916**, during the original 'traveling to expansion' transition. A new expansion is placed there.
3. **0126, new compaction in a gap at 13816–13906**: Δlog R −0.97 in 3.3 s, P drops from 0.83 to 0.36, speed ×1.68. This is the clearest unannotated startle.
4. **0200, long clear states in gaps**: new shoaling 17008–17532 (17.5 s, P 0.24, M 0.23) and milling 14041–14550 (17 s, M 0.71).
5. **0115, shoaling seg 45 (10460–10609) is really a compaction at 10504–10594**: P 0.05–0.2, Δlog R −0.58 in 3.8 s, speed ×1.48. The 1.5 s remnants are left unlabelled.

## Caveats

- This is a metrics-only draft. Every relabel and new exp/comp has a 5-panel snapshot in `revised/figures/snapshots/`. Borderline-kept events are flagged in `changes.csv` (`strict_decision`).
- Thresholds are explicit constants at the top of `revised/revise.py`. The 95th-percentile tail is per dataset, so a 'fast' event in a 70-fish school is slower in absolute terms than in a 10-fish school.
- Trimming leaves short unlabelled slivers between transitions and stable segments. That is intended (rule 2), but it reduces labelled time.

## Files

- `revised/annotations/<id>_motion.json` (10), `revised/CHANGELOG.md`, `revised/changes.csv`, `revised/changes_steps.csv`, `revised/radial_recheck.csv`, `revised/validation.csv`
- `revised/figures/before_after_<id>.png` (10), `revised/figures/snapshots/*.png`
- Scripts: `revised/radial_stats.py`, `revised/revise.py`, `revised/changelog.py`, `revised/plots_v2.py`, `revised/write_docs.py`
