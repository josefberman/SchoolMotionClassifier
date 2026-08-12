# School Motion Classifier

Simulate six fish-school behaviours, extract collective order parameters, train a classifier on simulations, and evaluate on held-out sims plus manually annotated real trajectories.

## Behaviours


| Canonical label       | Short      | Description                                         |
| --------------------- | ---------- | --------------------------------------------------- |
| `traveling_polarized` | tpol       | High directional alignment, net school translation  |
| `milling`             | milling    | Coherent (or bidirectional) rotation about centroid |
| `swarming`            | swarming   | Cohesive, low polarization                          |
| `fountain_evasion`    | fountain   | Split-and-merge around a crossing predator          |
| `expansion_burst`     | expansion  | Startle cascade, rapid expansion                    |
| `compaction`          | compaction | Threat-driven reduction of preferred spacing        |




## Order-parameter features

Per frame, then aggregated over a segment/window:

1. **Φdir** — directional polarization
2. **L̄** — normalized angular momentum
3. **Φrot** — rotational polarization
4. **Φtan** — tangential order
5. **v̄r** — signed mean radial velocity
6. **σd** — spread \mathrm{std}(r_i)

Classifier inputs: mean/std of each, plus length-normalized `sigma_d_slope`, `v_r_bar_slope`, and `l_bar_abs_mean`.

## Layout

```
src/sim/           # continuous ROA simulator + threat layer + IO
src/features/      # order parameters, windows, dataset builders
src/classify/      # train / eval
configs/behaviors/ # frozen YAML parameter sets
scripts/           # CLI entry points
sim_datasets/      # generated trajectories + manifest.json
schooling-datasets/# real trajectories
annotations/       # real segment labels (test)
results/           # models + metrics
```



## Setup

```bash
pip install -r requirements.txt
```



## Generate simulations

100 seeds × 6 behaviours × N∈{10,20,30,40,100,200} = 3600 clips. Seeds 0–79 train, 80–99 test.

```bash
python scripts/generate_sims.py --n-jobs 8
# quick check:
python scripts/generate_sims.py --smoke --n-jobs 4
```



### Publication figures / video

Clean white-background stills (300 dpi PNG) and optional MP4/GIF. Fish are dark discs with short heading ticks; circular arena outline only.

```bash
# While generating (stills for seed 0 only + video):
python scripts/generate_sims.py --smoke --render --video --render-seeds 0 --n-jobs 2

# From existing sim_datasets (manuscript set: one clip per behaviour):
python scripts/render_sims.py --manuscript --video

# Selected clips:
python scripts/render_sims.py --n-values 30 --seeds 0 --video
```

Outputs land in `sim_datasets/.../renders/` or `results/figures/<behavior>/`.

## Calibrate / inspect signatures

```bash
python scripts/calibrate_baselines.py
```



## Train & evaluate

```bash
python scripts/train_classifier.py   # sim train → sim test metrics
python scripts/eval_real.py          # annotated real segments (no compaction)
```

Outputs:

- `results/classifier.joblib`
- `results/sim_test_metrics.json`
- `results/real_eval_metrics.json`
- `results/sim_confusion.png` / `results/real_confusion.png`
- `results/calibration_report.json`

```bash
python scripts/plot_confusion.py
```



## Dataset split


| Split | Seeds | Count |
| ----- | ----- | ----- |
| train | 0–79  | 2880  |
| test  | 80–99 | 720   |




## Real data notes

- Label aliases live in `annotations/_label_aliases.json` (`polarized`→`traveling_polarized`, `burst`/`spread`→`expansion_burst`, …).
- Real annotations are class-imbalanced; fountain/burst are rare; **compaction has no real labels** and is excluded from real eval.
- Expect a sim↔real domain gap: the model is trained only on simulations; real metrics are a secondary sanity check.

