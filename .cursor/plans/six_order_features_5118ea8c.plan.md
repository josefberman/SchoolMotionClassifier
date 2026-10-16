---
name: Six order features
overview: Replace the current 3-D order-parameter set with six named Φ features (original three renamed, plus unsigned tan, local alignment, dilation). Classifier inputs are the instantaneous per-frame values, not segment means.
todos:
  - id: rename-branch
    content: Rename the current branch to six_features
    status: completed
  - id: implement-order-params
    content: Add 3 new Φ features and rename psi_tan/psi_rad_pm → phi_tan/phi_rad_pm in order_params.py
    status: completed
  - id: frame-level-classifier
    content: Train, eval, and predict on instantaneous per-frame FEATURE_NAMES; inverse-weight classes by frame count
    status: completed
  - id: update-consumers
    content: Update validate, calibration weights, tuner prints, README, and notebooks to the new keys/symbols
    status: completed
  - id: regen-artifacts
    content: Regenerate calibration_report.json, annotated_features.csv, and retrain classifier.joblib
    status: in_progress
isProject: false
---

# Six Φ order features (frame-level classifier)

Classifier inputs are the **six instantaneous order parameters at each frame**. One training/eval sample = one frame, labeled with that clip/segment’s behavior. No segment-mean pooling and no 2 s rolling mean/std.

Calibration, validation, and EDA plots can still summarize a clip as mean/std of the frame series. That is not what the classifier sees.

## Feature set

- `phi_trans` — \(\Phi_{\mathrm{trans}}=\lVert\langle\hat{\mathbf v}_i\rangle\rVert\) (unchanged)
- `phi_tan` — \(\Phi_{\mathrm{tan}}=\lvert\sum_i (r'_i\times v'_i)_z\rvert/D\) (same anisotropy-corrected heading order; **rename** `psi_tan` → `phi_tan`)
- `phi_rad_pm` — \(\Phi_{\mathrm{rad}}^{\pm}=\sum_i v'_i\cdot r'_i / D\) (same; **rename** `psi_rad_pm` → `phi_rad_pm`)
- `phi_tan_unsigned` — \(\Phi_{\mathrm{tan}}^{\mathrm{unsigned}}=T_{\mathrm{energy}}=\sum_i[(\hat r_i\times\mathbf u_i)_z]^2/\sum_i\lVert\mathbf u_i\rVert^2\) using **actual** relative velocities \(\mathbf u_i=\mathbf v_i-\bar{\mathbf v}\), \(\mathbf q_i=\mathbf x_i-\bar{\mathbf x}\), \(\hat r_i=\mathbf q_i/\lVert\mathbf q_i\rVert\)
- `phi_local` — \(\Phi_{\mathrm{local}}=\frac1N\sum_i\lVert\frac1{\lvert\mathcal N_i\rvert}\sum_{j\in\mathcal N_i}\hat{\mathbf v}_j\rVert\) with \(k=5\) nearest neighbors, excluding self; if \(N\le5\) use \(k=N-1\)
- `phi_dilation` — \(\Phi_{\mathrm{dilation}}=\alpha=\sum_i\mathbf q_i\cdot\mathbf u_i/\sum_i\lVert\mathbf q_i\rVert^2\) (dimensional, \(1/\mathrm{time}\); implement the pictured formula as-is)

```python
FEATURE_NAMES = (
    "phi_trans", "phi_tan", "phi_rad_pm",
    "phi_tan_unsigned", "phi_local", "phi_dilation",
)
# clip summaries for calibration/EDA only — not classifier inputs
AGG_FEATURE_NAMES = [f"{k}_mean" for k in FEATURE_NAMES]
```

## Implementation

First rename the current branch (`delta_features`) to `six_features` (`git branch -m six_features`).

All per-frame math stays in [`compute_order_params_series`](src/features/order_params.py) (vectorized over time).

- Reuse existing \(\hat{\mathbf v}\), centered \(v'\), \(r'\), \(D\) for the three original features.
- For the two kinetic features, compute \(\mathbf q\) and \(\mathbf u\) once from raw positions/velocities (not unit headings).
- For \(\Phi_{\mathrm{local}}\), batched kNN over frames: pairwise \(T\times N\times N\) distances, `argpartition` \(k=5\), gather neighbor headings, mean then norm then mean over fish. Memory is fine for current \(N\le100\). Do **not** use Voronoi/`src/sim/neighbors.py` (those are for the simulator).

Safe-divide the new denominators the same way as \(D\) (`where > 1e-12`).

## Frame-level train / eval / predict

Today train uses one **segment mean** per clip ([`features_from_sim_entry`](src/features/dataset.py) / [`build_real_xy`](src/features/dataset.py)), while predict already labels every frame with a **2 s rolling mean** ([`frame_feature_matrix`](src/features/windows.py)). Both change.

- **Features:** stack `compute_order_params_series` into `(T, 6)` using `FEATURE_NAMES`. Replace `frame_feature_matrix` with this (drop rolling mean/std). Drop `window_sec` from predict.
- **Sim train samples:** every frame in the clip (event-window frames only for expansion/compaction; morph-window frames only for transitions). Label = clip behavior.
- **Real train/eval samples:** every frame inside each annotated interval. Label = segment label.
- **Default train mode:** `"frame"` in [`src/classify/train.py`](src/classify/train.py).
- **Eval:** [`src/classify/eval.py`](src/classify/eval.py) scores frames, not one vote per segment.

### Inverse class-frequency weights

Frame counts are badly unbalanced (traveling dominates). Weight each frame by \(w_i=1/n_{y_i}\), so every class contributes equally.

- **Train:** pass `sample_weight=1/n_class` into both the grid-search fit (sim fold) and the final `model.fit(X_sim, yt, sample_weight=...)`. Compute counts from the sim training labels only.
- **Grid-search score:** keep real **macro-F1** (already averages classes equally). Do not use support-weighted F1.
- **Eval headline:** class-balanced accuracy \(\frac1C\sum_c \mathrm{recall}_c\) (same as accuracy with weights \(1/n_c\)) plus macro-F1. Still write raw accuracy and per-class support, but do not use them as the primary number.
- Subset metrics (baseline / transition) recompute \(n_c\) on that subset.

`aggregate_series` / `segment_feature_vector` remain for calibration reports and notebooks.

## Downstream key updates (no formula changes)

Rename every `psi_tan` / `psi_rad_pm` key to `phi_tan` / `phi_rad_pm`:

- Validation gates in [`src/sim/validate.py`](src/sim/validate.py) (`psi_tan_*` → `phi_tan_*`, `psi_rad_*` → `phi_rad_*`; `psi_rad_event` → `phi_rad_event`). Keep the same numerical thresholds on the original three.
- Tuner print + weights in [`src/tune/feature_match.py`](src/tune/feature_match.py) and [`src/tune/calibration.py`](src/tune/calibration.py). New features inherit default weight `1.0`. Calibration still matches **clip-level** means of the six frame series.
- [`README.md`](README.md): six instantaneous Φ values per frame.
- Notebooks [`figures.ipynb`](figures.ipynb) and [`manual eda.ipynb`](manual%20eda.ipynb): axis labels \(\Phi_{\mathrm{tan}}\), \(\Phi_{\mathrm{rad}}^{\pm}\), plus the three new features.

## Stale artifacts

These still encode the old 3-D `psi_*` names and must be regenerated after the code change:

- [`results/calibration_report.json`](results/calibration_report.json) via `scripts/calibrate_baselines.py`
- [`annotated_features.csv`](annotated_features.csv) (used by `figures.ipynb`; clip summaries are fine here)
- `results/classifier.joblib` via `scripts/train_classifier.py` (old 3-feature segment model will not match 6-D frame inputs)

Do not retune sim configs in this change.
