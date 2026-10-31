# How `annotated_config.csv` is calculated

Produced by `python scripts/tune_trajectories.py --extract` (`build_annotated_config` in `src/tune/trajectory_match.py`). One row per non-overlapping 15-frame window (0.5 s at 29.97 fps) inside a canonical annotation interval. A trailing piece shorter than 15 frames is dropped. Transition labels (`a_to_b`) are not included. Intervals shorter than `0.5 * fps` are already dropped by `load_real_segments`.

Positions and velocities come from `schooling-datasets/{group}/{id}/{id}_loc_vel_data.csv`. Velocity components are pixels per frame. The fit uses a frame step of 1, so every rate below is per frame.

A fish-step is kept only when that fish has finite position and velocity and speed above `1e-3` px/frame at both the current frame and the next frame, and at least two such fish exist on that step. A window is dropped if it yields fewer than 10 fish-steps or a non-finite design.

If a window has more than 30,000 fish-steps, the Tobit fit uses a fixed sample of 30,000 rows (`numpy` generator seed 0). The same sample is used for every parameter of that window.

## Identity columns

| column | value |
|---|---|
| `dataset` | Dataset id. Digit-only ids are written as integers, so `0066` becomes `66`. |
| `start_frame` | First frame of the 15-frame window. |
| `end_frame` | Frame after the window (`start_frame + 15`). |
| `fps` | Frames per second stored with the annotation. Not used in the fit. |
| `label` | Canonical behavior: `traveling`, `milling`, `shoaling`, `expansion`, or `compaction`. |

## Shared model

The fitted numbers are the parameters of the simulator update in `FastSchoolSimulator.step`.

Heading of fish `i` at frame `t` is `θ = atan2(vy, vx)`. The observed turn is the wrapped angle

```
Δθ = wrap(θ_{t+1} - θ_t)    in (-π, π]
```

and the observed speed change is `Δs = speed_{t+1} - speed_t`, with `speed = hypot(vx, vy)`.

The simulator advances those by

```
Δθ = clip(w_r t_r + w_o t_o + w_a t_a + w_tan t_tan + w_rad t_rad + σ_θ ε + wall, ±omega_max)
Δs = clip(s_0 - speed + σ_s ε, ±a_max)
```

`ε` is standard normal. `wall` is the simulator's wall torque from the traveling config (arena, `wall_margin`, `w_wall`). It is computed and added; it is not a column.

Zone torques are means of wrapped angle errors over neighbors in mutually exclusive rings:

- `t_r`: neighbors with distance `< r_r`. Desired heading points away from the neighbor.
- `t_o`: neighbors with `r_r ≤ distance < r_o`. Desired heading matches the neighbor's heading.
- `t_a`: neighbors with `r_o ≤ distance < r_a`. Desired heading points toward the neighbor.

`t_tan` is the wrapped angle from the fish's heading to the tangential direction around the school centroid. The tangent is rotated by `c_mill * π/2`. `c_mill` is `+1` or `-1`, chosen as the sign of `Σ (r_x sin θ - r_y cos θ)` over valid fish in the window (`+1` when that sum is about 0). `t_rad` is `sin` of the angle from the fish's heading to the outward radial direction. Positive `t_rad` is away from the centroid.

Weights `w_r`, `w_o`, `w_a`, `w_tan` are constrained to be ≥ 0. `w_rad` is free. `s_0` is ≥ 0. `σ_θ` and `σ_s` are optimized as `log σ` inside `[1e-4, 5]`.

Both fits are two-sided Tobit maximum likelihood: rows with `|y|` strictly inside the clip bound contribute a normal density, and rows on either cap contribute the corresponding tail probability. The optimizer is L-BFGS-B, started from nonnegative least squares for the heading weights (initial `σ = 0.05`) and from `median(speed + Δs)` for `s_0`. If L-BFGS-B fails, the heading row keeps that least-squares start and `sigma_theta = 0.05`; the speed row keeps the median start and `sigma_s = 0.05`.

## `r_r`, `r_o`, `r_a`

These are chosen before the other parameters by minimizing the heading Tobit negative log-likelihood. The search is continuous inside `r_r` 10–80, `r_o` 40–250, `r_a` 80–500, with `r_r + 1 < r_o` and `r_o + 1 < r_a`. Differential evolution proposes any ordered triple in that box. Each proposal is scored by the heading Tobit loss at the nonnegative least-squares weights. The ten parameters below are then the full Tobit fit on the same 15-frame window at the winning radii. Speed does not depend on the radii.

## Heading parameters

Fit at the winning radii, on every valid fish-step of the window.

`omega_max` is the 99th percentile of `|Δθ|`. If fewer than 20 turns are available it is the maximum of `|Δθ|`. It is floored at `1e-4`. It is held fixed while the weights and `sigma_theta` are fit; it is not a free likelihood parameter.

`w_r`, `w_o`, `w_a`, `w_tan`, `w_rad`, and `sigma_theta` are the Tobit MLE of

```
Δθ = clip(w_r t_r + w_o t_o + w_a t_a + w_tan t_tan + w_rad t_rad + sigma_theta * ε + wall, ±omega_max)
```

`t_r`, `t_o`, and `t_a` use the row's own `r_r`, `r_o`, and `r_a`.

## Speed parameters

Fit on the same fish-steps. Radii and heading weights do not enter.

`a_max` is the 99th percentile of `|Δs|`, or the maximum when fewer than 20 steps are available, floored at `1e-4`. It is held fixed.

`s_0` and `sigma_s` are the Tobit MLE of

```
Δs = clip(s_0 - speed + sigma_s * ε, ±a_max)
```

`speed` is the speed at the start of the step.
