"""Generic Couzin-zone school simulator shared by all five behaviors.

Social torques are zone means of signed shortest-angle errors:

    T_r, T_o, T_a   (0 if a zone is empty)

Collective steering is relative to the instantaneous school centroid.
Wall avoidance is an environmental constraint, not a behavior parameter.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from src.sim.config import BEHAVIOR_KEYS, deep_merge, load_behavior_config, validate_radii
from src.sim.model import SimResult, _wrap

# Shared initialization heading jitter (radians). Not a YAML/search parameter.
INIT_HEADING_NOISE = 0.15


class FastSchoolSimulator:
    def __init__(self, n: int, cfg: dict[str, Any], seed: int = 0):
        validate_radii(cfg)
        self.n = n
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        self.dt = float(cfg["dt"])
        self.fps = float(cfg["fps"])
        arena = cfg["arena"]
        self.center = np.asarray(arena["center"], dtype=np.float64)
        self.half_extent = float(arena.get("half_extent", arena.get("radius", 420.0)))
        self.xmin = self.center[0] - self.half_extent
        self.xmax = self.center[0] + self.half_extent
        self.ymin = self.center[1] - self.half_extent
        self.ymax = self.center[1] + self.half_extent
        self.wall_margin = float(arena["wall_margin"])
        self.w_wall = float(arena["w_wall"])
        self.frame = 0

        self.pos = np.zeros((n, 2), dtype=np.float64)
        self.theta = np.zeros(n, dtype=np.float64)
        self.speed = np.full(n, float(cfg["s_0"]), dtype=np.float64)
        # One circulation sign per simulation; unused when w_tan == 0.
        self.c_mill = 1.0 if self.rng.random() < 0.5 else -1.0
        self._init_agents()

    def _init_agents(self) -> None:
        cfg = self.cfg
        behavior = cfg.get("behavior", "traveling_polarized")
        span = 0.35 * self.half_extent
        self.pos[:, 0] = self.center[0] + self.rng.uniform(-span, span, self.n)
        self.pos[:, 1] = self.center[1] + self.rng.uniform(-span, span, self.n)
        noise = self.rng.normal(0.0, INIT_HEADING_NOISE, self.n)
        centroid = self.pos.mean(axis=0)
        rel = self.pos - centroid
        theta_rad = np.arctan2(rel[:, 1], rel[:, 0])

        if behavior == "traveling_polarized":
            theta_0 = float(self.rng.uniform(0.0, 2.0 * np.pi))
            self.theta = theta_0 + noise
        elif behavior == "milling":
            self.theta = theta_rad + self.c_mill * (np.pi / 2.0) + noise
        elif behavior == "swarming":
            self.theta = self.rng.uniform(0.0, 2.0 * np.pi, self.n)
        elif behavior == "expansion_burst":
            self.theta = theta_rad + noise
        elif behavior == "compaction":
            self.theta = theta_rad + np.pi + noise
        else:
            theta_0 = float(self.rng.uniform(0.0, 2.0 * np.pi))
            self.theta = theta_0 + noise

        self.theta = np.mod(self.theta, 2.0 * np.pi)
        self.speed[:] = float(cfg["s_0"])

    def headings(self) -> np.ndarray:
        return np.stack((np.cos(self.theta), np.sin(self.theta)), axis=1)

    def velocities(self) -> np.ndarray:
        return self.speed[:, None] * self.headings()

    def _social(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Mean Couzin-zone torques. Zones are mutually exclusive: r_r, then r_o, then r_a."""
        n = self.n
        t_r = np.zeros(n)
        t_o = np.zeros(n)
        t_a = np.zeros(n)
        if n < 2:
            return t_r, t_o, t_a

        dvec = self.pos[None, :, :] - self.pos[:, None, :]  # x_j - x_i
        dist = np.hypot(dvec[:, :, 0], dvec[:, :, 1])
        np.fill_diagonal(dist, np.inf)

        r_r = float(self.cfg["r_r"])
        r_o = float(self.cfg["r_o"])
        r_a = float(self.cfg["r_a"])
        mask_r = dist < r_r
        mask_o = (dist >= r_r) & (dist < r_o)
        mask_a = (dist >= r_o) & (dist < r_a)

        desired_r = np.arctan2(-dvec[:, :, 1], -dvec[:, :, 0])
        err_r = np.where(mask_r, _wrap(desired_r - self.theta[:, None]), 0.0)
        count_r = mask_r.sum(axis=1)
        np.divide(err_r.sum(axis=1), count_r, out=t_r, where=count_r > 0)

        err_o = np.where(mask_o, _wrap(self.theta[None, :] - self.theta[:, None]), 0.0)
        count_o = mask_o.sum(axis=1)
        np.divide(err_o.sum(axis=1), count_o, out=t_o, where=count_o > 0)

        desired_a = np.arctan2(dvec[:, :, 1], dvec[:, :, 0])
        err_a = np.where(mask_a, _wrap(desired_a - self.theta[:, None]), 0.0)
        count_a = mask_a.sum(axis=1)
        np.divide(err_a.sum(axis=1), count_a, out=t_a, where=count_a > 0)
        return t_r, t_o, t_a

    def _centroid_steering(self) -> tuple[np.ndarray, np.ndarray]:
        rel = self.pos - self.pos.mean(axis=0)
        theta_rad = np.arctan2(rel[:, 1], rel[:, 0])
        theta_tan = theta_rad + self.c_mill * (np.pi / 2.0)
        t_tan = _wrap(theta_tan - self.theta)
        t_rad = np.sin(theta_rad - self.theta)
        return t_tan, t_rad

    def _wall(self) -> np.ndarray:
        """Environmental turning toward the interior near square-arena walls."""
        torque = np.zeros(self.n)
        m = self.wall_margin
        x, y = self.pos[:, 0], self.pos[:, 1]
        theta = self.theta

        d_right = x - (self.xmax - m)
        near_r = d_right > 0
        if np.any(near_r):
            strength = (d_right[near_r] / max(m, 1e-6)) ** 2
            torque[near_r] += self.w_wall * strength * _wrap(np.pi - theta[near_r])

        d_left = (self.xmin + m) - x
        near_l = d_left > 0
        if np.any(near_l):
            strength = (d_left[near_l] / max(m, 1e-6)) ** 2
            torque[near_l] += self.w_wall * strength * _wrap(0.0 - theta[near_l])

        d_top = y - (self.ymax - m)
        near_t = d_top > 0
        if np.any(near_t):
            strength = (d_top[near_t] / max(m, 1e-6)) ** 2
            torque[near_t] += self.w_wall * strength * _wrap(-np.pi / 2 - theta[near_t])

        d_bot = (self.ymin + m) - y
        near_b = d_bot > 0
        if np.any(near_b):
            strength = (d_bot[near_b] / max(m, 1e-6)) ** 2
            torque[near_b] += self.w_wall * strength * _wrap(np.pi / 2 - theta[near_b])
        return torque

    def _clip_to_arena(self) -> None:
        cx, cy = self.center
        hard = self.half_extent * 0.98
        self.pos[:, 0] = np.clip(self.pos[:, 0], cx - hard, cx + hard)
        self.pos[:, 1] = np.clip(self.pos[:, 1], cy - hard, cy + hard)

    def step(self) -> None:
        cfg = self.cfg
        t_r, t_o, t_a = self._social()
        t_tan, t_rad = self._centroid_steering()
        eps_w = self.rng.normal(0.0, 1.0, self.n)
        omega = (
            float(cfg["w_r"]) * t_r
            + float(cfg["w_o"]) * t_o
            + float(cfg["w_a"]) * t_a
            + float(cfg["w_tan"]) * t_tan
            + float(cfg["w_rad"]) * t_rad
            + float(cfg["sigma_theta"]) * eps_w
            + self._wall()
        )
        omega = np.clip(omega, -float(cfg["omega_max"]), float(cfg["omega_max"]))
        self.theta = np.mod(self.theta + omega, 2.0 * np.pi)

        eps_a = self.rng.normal(0.0, 1.0, self.n)
        delta_s = np.clip(
            float(cfg["s_0"]) - self.speed + float(cfg["sigma_s"]) * eps_a,
            -float(cfg["a_max"]),
            float(cfg["a_max"]),
        )
        self.speed = np.maximum(0.0, self.speed + delta_s)
        self.pos = self.pos + self.velocities() * self.dt
        self._clip_to_arena()
        self.frame += 1

    def run(self) -> SimResult:
        cfg = self.cfg
        for _ in range(int(cfg["burn_in"])):
            self.step()
        T = int(cfg["record_frames"])
        pos_hist = np.zeros((T, self.n, 2))
        vel_hist = np.zeros((T, self.n, 2))
        self.frame = 0
        for t in range(T):
            self.step()
            pos_hist[t] = self.pos
            vel_hist[t] = self.velocities()
        return SimResult(
            positions=pos_hist,
            velocities=vel_hist,
            meta={
                "n": self.n,
                "behavior": cfg.get("behavior"),
                "fps": self.fps,
                "c_mill": self.c_mill,
            },
        )


def run_simulation_fast(behavior: str, n: int, seed: int, overrides: dict | None = None) -> SimResult:
    from src.labels import BEHAVIOR_SHORT

    short = BEHAVIOR_SHORT.get(behavior, behavior)
    base = load_behavior_config(short)
    if overrides:
        base = deep_merge(base, overrides)
        validate_radii(base)
    base["behavior"] = behavior
    return FastSchoolSimulator(n=n, cfg=base, seed=seed).run()


def run_transition_fast(
    behavior_from: str,
    behavior_to: str,
    n: int,
    seed: int,
    *,
    total_frames: int = 300,
    morph_start_frac: float = 0.30,
    morph_end_frac: float = 0.70,
    burn_in: int = 80,
) -> SimResult:
    """Simulate a transition by linearly morphing the 13 behavior parameters."""
    from src.labels import BEHAVIOR_SHORT

    cfg_from = load_behavior_config(BEHAVIOR_SHORT[behavior_from])
    cfg_to = load_behavior_config(BEHAVIOR_SHORT[behavior_to])
    cfg_from["behavior"] = behavior_from
    cfg_to["behavior"] = behavior_to

    he = max(float(cfg_from["arena"]["half_extent"]), float(cfg_to["arena"]["half_extent"]))
    cfg_from["arena"]["half_extent"] = he
    cfg_to["arena"]["half_extent"] = he
    cfg_from["burn_in"] = burn_in
    cfg_from["record_frames"] = total_frames

    sim = FastSchoolSimulator(n=n, cfg=cfg_from, seed=seed)
    for _ in range(burn_in):
        sim.step()

    morph_start = int(total_frames * morph_start_frac)
    morph_end = int(total_frames * morph_end_frac)
    morph_len = max(morph_end - morph_start, 1)
    vals_from = {k: float(cfg_from[k]) for k in BEHAVIOR_KEYS}
    vals_to = {k: float(cfg_to[k]) for k in BEHAVIOR_KEYS}

    T = total_frames
    pos_hist = np.zeros((T, n, 2))
    vel_hist = np.zeros((T, n, 2))
    sim.frame = 0
    for t in range(T):
        if t < morph_start:
            alpha = 0.0
        elif t >= morph_end:
            alpha = 1.0
        else:
            alpha = (t - morph_start) / morph_len
        for k in BEHAVIOR_KEYS:
            sim.cfg[k] = vals_from[k] * (1.0 - alpha) + vals_to[k] * alpha
        if t >= morph_end:
            sim.cfg["behavior"] = behavior_to
        sim.step()
        pos_hist[t] = sim.pos
        vel_hist[t] = sim.velocities()

    label = f"{behavior_from}_to_{behavior_to}"
    return SimResult(
        positions=pos_hist,
        velocities=vel_hist,
        meta={
            "n": n,
            "behavior": label,
            "behavior_from": behavior_from,
            "behavior_to": behavior_to,
            "fps": sim.fps,
            "morph_start": morph_start,
            "morph_end": morph_end,
            "c_mill": sim.c_mill,
        },
    )
