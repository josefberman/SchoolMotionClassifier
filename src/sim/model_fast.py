"""Vectorized-ish school step for faster bulk generation.

Uses kNN instead of Voronoi (still local, anisotropic via blind spot approx).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from src.sim.model import SimResult, STATE_BASELINE, STATE_FOUNTAIN, STATE_STARTLE, STATE_COMPACT, STATE_RECOVER, _wrap


def _knn_idx(pos: np.ndarray, k: int) -> np.ndarray:
    n = pos.shape[0]
    k = min(k, n - 1)
    d2 = np.sum((pos[:, None, :] - pos[None, :, :]) ** 2, axis=-1)
    np.fill_diagonal(d2, np.inf)
    return np.argpartition(d2, kth=k, axis=1)[:, :k]


class FastSchoolSimulator:
    def __init__(self, n: int, cfg: dict[str, Any], seed: int = 0):
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
        self.k = min(8, max(3, n - 1))
        self._neigh_idx: np.ndarray | None = None
        self._neigh_age = 999
        self.in_recording = False

        self.pos = np.zeros((n, 2))
        self.theta = np.zeros(n)
        self.speed = np.full(n, float(cfg["s_cruise"]))
        self.state = np.full(n, STATE_BASELINE, dtype=np.int32)
        self.state_timer = np.zeros(n)
        self.z = np.zeros(n)
        self.circ_sign = np.ones(n)
        self.predator_pos = None
        self.predator_vel = None
        self.frame = 0
        self.d0_base = float(cfg["d0"])
        self.d0 = np.full(n, self.d0_base)
        self.w_r = np.full(n, float(cfg["w_r"]))
        self.w_o = np.full(n, float(cfg["w_o"]))
        self.w_a = np.full(n, float(cfg["w_a"]))
        self.w_p = np.zeros(n)
        self.s_star = np.full(n, float(cfg["s_cruise"]))
        self._init_agents()

    def _reset_baseline_params(self) -> None:
        cfg = self.cfg
        self.w_r[:] = float(cfg["w_r"])
        self.w_o[:] = float(cfg["w_o"])
        self.w_a[:] = float(cfg["w_a"])
        self.w_p[:] = 0.0
        self.d0[:] = self.d0_base
        self._init_speeds()
        self.state[:] = STATE_BASELINE
        self.z[:] = 0.0
        self.predator_pos = None
        self.predator_vel = None

    def _spawn_predator(self) -> None:
        threat = self.cfg["threat"]
        y0 = float(np.mean(self.pos[:, 1]))
        spd = float(threat["predator_speed"])
        self.predator_pos = np.array([self.xmin - 50.0, y0], dtype=np.float64)
        self.predator_vel = np.array([spd, 0.0], dtype=np.float64)

    def _init_speeds(self) -> None:
        cfg = self.cfg
        spread = float(cfg.get("speed_spread", 0.0))
        cruise = float(cfg["s_cruise"])
        if spread > 0:
            self.speed[:] = cruise * self.rng.uniform(1.0 - spread, 1.0 + spread, self.n)
        else:
            self.speed[:] = cruise
        self.s_star[:] = self.speed

    def _init_agents(self) -> None:
        cfg = self.cfg
        span = 0.35 * self.half_extent
        theta_std = float(cfg.get("theta_init_std", 0.25))
        behavior = cfg.get("behavior", "traveling_polarized")
        if behavior == "traveling_polarized":
            h0 = self.rng.uniform(0, 2 * np.pi)
            self.theta = h0 + self.rng.normal(0, theta_std, self.n)
            self.pos[:, 0] = self.center[0] + self.rng.uniform(-span * 0.7, span * 0.7, self.n)
            self.pos[:, 1] = self.center[1] + self.rng.uniform(-span * 0.7, span * 0.7, self.n)
        elif behavior == "milling":
            self.pos[:, 0] = self.center[0] + self.rng.uniform(-span * 0.5, span * 0.5, self.n)
            self.pos[:, 1] = self.center[1] + self.rng.uniform(-span * 0.5, span * 0.5, self.n)
            r = self.pos - self.center
            base = np.arctan2(r[:, 1], r[:, 0]) + np.pi / 2
            frac_bi = float(cfg.get("bidirectional_frac", 0.0))
            if frac_bi > 0:
                flip = self.rng.random(self.n) < frac_bi
                self.circ_sign = np.where(flip, -1.0, 1.0)
                self.theta = base + np.where(flip, np.pi, 0.0)
            else:
                sense = 1.0 if self.rng.random() < 0.5 else -1.0
                self.circ_sign[:] = sense
                self.theta = np.arctan2(r[:, 1], r[:, 0]) + sense * np.pi / 2
            self.theta += self.rng.normal(0, theta_std, self.n)
        elif behavior == "swarming":
            self.pos[:, 0] = self.center[0] + self.rng.uniform(-span, span, self.n)
            self.pos[:, 1] = self.center[1] + self.rng.uniform(-span, span, self.n)
            self.theta = self.rng.uniform(0, 2 * np.pi, self.n)
        else:
            self.pos[:, 0] = self.center[0] + self.rng.uniform(-span, span, self.n)
            self.pos[:, 1] = self.center[1] + self.rng.uniform(-span, span, self.n)
            h0 = self.rng.uniform(0, 2 * np.pi)
            self.theta = h0 + self.rng.normal(0, theta_std, self.n)
        self.theta = np.mod(self.theta, 2 * np.pi)
        self._init_speeds()

    def headings(self) -> np.ndarray:
        return np.stack((np.cos(self.theta), np.sin(self.theta)), axis=1)

    def velocities(self) -> np.ndarray:
        return self.speed[:, None] * self.headings()

    def _social(self, headings: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        cfg = self.cfg
        n = self.n
        refresh = 1 if n <= 40 else 3
        if self._neigh_idx is None or self._neigh_age >= refresh:
            self._neigh_idx = _knn_idx(self.pos, self.k)
            self._neigh_age = 0
        else:
            self._neigh_age += 1
        idx = self._neigh_idx
        t_r = np.zeros(n)
        t_o = np.zeros(n)
        t_a = np.zeros(n)
        r_rep = float(cfg["r_repulse"])
        r_ori = float(cfg["r_orient"])
        r_att = float(cfg["r_attract"])
        cross_scale = float(cfg.get("cross_align_scale", 1.0))
        blind_cos = np.cos(np.pi - np.deg2rad(float(cfg["blind_half_deg"])))
        lat_repulse = float(cfg.get("lateral_repulse_scale", 1.0))

        for i in range(n):
            pi = self.pos[i]
            hi = headings[i]
            d0_i = self.d0[i]
            for j in idx[i]:
                dvec = self.pos[j] - pi
                dist = np.hypot(dvec[0], dvec[1])
                if dist < 1e-9:
                    continue
                u = dvec / dist
                if hi[0] * u[0] + hi[1] * u[1] < blind_cos:
                    continue
                if dist < max(r_rep, d0_i):
                    desired = np.arctan2(-u[1], -u[0])
                    w = (max(r_rep, d0_i) - dist) / max(r_rep, d0_i)
                    dot_lat = abs(hi[0] * (-u[1]) + hi[1] * u[0])
                    w *= 1.0 + (lat_repulse - 1.0) * dot_lat
                    t_r[i] += w * _wrap(desired - self.theta[i])
                if dist < r_ori:
                    align_w = cross_scale if (hi[0] * headings[j, 0] + hi[1] * headings[j, 1] < 0) else 1.0
                    t_o[i] += align_w * _wrap(self.theta[j] - self.theta[i]) * (1.0 - dist / r_ori)
                if d0_i < dist < r_att:
                    desired = np.arctan2(u[1], u[0])
                    w = (dist - d0_i) / (r_att - d0_i + 1e-9)
                    if lat_repulse > 1.0:
                        dot_along = abs(hi[0] * u[0] + hi[1] * u[1])
                        w *= 0.2 + 0.8 * dot_along
                    t_a[i] += w * _wrap(desired - self.theta[i])
        return t_r, t_o, t_a

    def _wall(self) -> np.ndarray:
        wall_scale = 0.15 if np.any(self.state == STATE_STARTLE) else 1.0
        torque = np.zeros(self.n)
        m = self.wall_margin
        x, y = self.pos[:, 0], self.pos[:, 1]
        theta = self.theta

        d_right = x - (self.xmax - m)
        near_r = d_right > 0
        if np.any(near_r) and wall_scale > 0:
            strength = (d_right[near_r] / max(m, 1e-6)) ** 2
            torque[near_r] += self.w_wall * wall_scale * strength * _wrap(np.pi - theta[near_r])

        d_left = (self.xmin + m) - x
        near_l = d_left > 0
        if np.any(near_l) and wall_scale > 0:
            strength = (d_left[near_l] / max(m, 1e-6)) ** 2
            torque[near_l] += self.w_wall * wall_scale * strength * _wrap(0.0 - theta[near_l])

        d_top = y - (self.ymax - m)
        near_t = d_top > 0
        if np.any(near_t) and wall_scale > 0:
            strength = (d_top[near_t] / max(m, 1e-6)) ** 2
            torque[near_t] += self.w_wall * wall_scale * strength * _wrap(-np.pi / 2 - theta[near_t])

        d_bot = (self.ymin + m) - y
        near_b = d_bot > 0
        if np.any(near_b) and wall_scale > 0:
            strength = (d_bot[near_b] / max(m, 1e-6)) ** 2
            torque[near_b] += self.w_wall * wall_scale * strength * _wrap(np.pi / 2 - theta[near_b])

        overshoot = 1.25 if np.any(self.state == STATE_STARTLE) else 1.0
        limit = self.half_extent * overshoot
        cx, cy = self.center
        self.pos[:, 0] = np.clip(self.pos[:, 0], cx - limit, cx + limit)
        self.pos[:, 1] = np.clip(self.pos[:, 1], cy - limit, cy + limit)
        if overshoot <= 1.0:
            hard = self.half_extent * 0.98
            self.pos[:, 0] = np.clip(self.pos[:, 0], cx - hard, cx + hard)
            self.pos[:, 1] = np.clip(self.pos[:, 1], cy - hard, cy + hard)
        return torque

    def _predator(self) -> np.ndarray:
        torque = np.zeros(self.n)
        if self.predator_pos is None or self.predator_vel is None:
            return torque
        cfg_t = self.cfg["threat"]
        flee_ang = np.deg2rad(float(cfg_t["flee_angle_deg"]))
        resp = float(cfg_t["predator_radius"])
        pv = self.predator_vel
        rpi = self.pos - self.predator_pos
        dist = np.linalg.norm(rpi, axis=1)
        active = dist < resp
        if not np.any(active):
            return torque
        radial = rpi[active] / np.maximum(dist[active, None], 1e-9)
        cross = pv[0] * rpi[active, 1] - pv[1] * rpi[active, 0]
        sgn = np.where(cross >= 0, 1.0, -1.0)
        ca, sa = np.cos(flee_ang), np.sin(flee_ang)
        fx = radial[:, 0] * ca - sgn * radial[:, 1] * sa
        fy = radial[:, 1] * ca + sgn * radial[:, 0] * sa
        desired = np.arctan2(fy, fx)
        strength = 1.0 - dist[active] / resp
        torque[active] = strength * _wrap(desired - self.theta[active])
        self.z[active] += float(cfg_t["beta_p"]) * strength * self.dt
        return torque

    def _update_threat(self) -> None:
        if not self.in_recording:
            return
        cfg = self.cfg
        threat = cfg["threat"]
        if not threat.get("enabled"):
            return
        mode = threat.get("mode")
        start = int(threat["start_frame"])
        dur = int(threat["duration"])
        t = self.frame
        full_clip = bool(threat.get("full_clip", True))
        active = start <= t < start + dur

        if mode == "fountain" and active:
            if self.predator_pos is None:
                self._spawn_predator()
            else:
                self.predator_pos = self.predator_pos + self.predator_vel * self.dt
                if self.predator_pos[0] > self.xmax + 50.0:
                    self._spawn_predator()

        if mode == "startle" and active:
            if full_clip:
                self.state[:] = STATE_STARTLE
                self.w_r[:] = float(cfg["w_r"]) * 2.8
                self.w_a[:] = float(cfg["w_a"]) * 0.12
                self.w_o[:] = float(cfg["w_o"]) * 0.15
                self.s_star[:] = float(cfg.get("s_escape", cfg["s_cruise"] * 2.0))
                if t == start:
                    away = self.pos - self.pos.mean(axis=0)
                    self.theta = np.mod(
                        np.arctan2(away[:, 1], away[:, 0]) + self.rng.normal(0, 0.35, self.n),
                        2 * np.pi,
                    )
            elif start <= t < start + dur + int(threat["escape_duration"]):
                idx = _knn_idx(self.pos, min(5, self.n - 1))
                z_thr = float(threat["z_thr"])
                if self.predator_pos is not None:
                    dpred = np.linalg.norm(self.pos - self.predator_pos, axis=1)
                    close = dpred < float(threat["predator_radius"])
                    self.z[close] += float(threat["beta_p"]) * 0.8
                dz = -self.z / max(float(threat["tau_z"]), 1e-6)
                for i in range(self.n):
                    for j in idx[i]:
                        if self.z[j] > z_thr or self.state[j] == STATE_STARTLE:
                            dz[i] += float(threat["beta_n"]) * 0.35
                self.z = np.clip(self.z + dz * self.dt, 0, 5)
                if t == start:
                    self.z[:] = np.maximum(self.z, z_thr + 0.1)
                newly = (self.z > z_thr) & (self.state != STATE_STARTLE)
                if np.any(newly):
                    self.state[newly] = STATE_STARTLE
                    self.state_timer[newly] = float(threat["escape_duration"]) * self.dt
                    self.s_star[newly] = float(cfg["s_escape"])
                    self.speed[newly] = np.maximum(self.speed[newly], float(cfg["s_escape"]) * 0.85)
                    self.w_r[newly] = float(cfg["w_r"]) * 3.0
                    self.w_a[newly] = float(cfg["w_a"]) * 0.1
                    self.w_o[newly] = float(cfg["w_o"]) * 0.1
                    away = self.pos[newly] - self.pos.mean(axis=0)
                    if self.predator_pos is not None:
                        away = away + 0.7 * (self.pos[newly] - self.predator_pos)
                    self.theta[newly] = np.arctan2(away[:, 1], away[:, 0]) + self.rng.normal(
                        0, 0.5, int(np.sum(newly))
                    )

        if mode == "fountain" and active:
            self.state[:] = STATE_FOUNTAIN
            self.w_p[:] = float(threat["w_p"])
            self.w_a[:] = float(cfg["w_a"]) * 0.7
            self.w_o[:] = float(cfg["w_o"]) * 0.5

        if mode == "compact" and active:
            self.state[:] = STATE_COMPACT
            elapsed = (t - start) * self.dt
            tau = float(threat["compact_tau"]) * self.dt
            delta = float(threat["compact_delta_d0"])
            factor = 1.0 - np.exp(-elapsed / max(tau, 1e-6))
            self.d0[:] = np.maximum(6.0, self.d0_base - delta * factor)
            self.w_a[:] = float(cfg["w_a"]) * 3.0
            self.w_o[:] = float(cfg["w_o"]) * 0.35
            self.w_r[:] = float(cfg["w_r"]) * 0.55
            self.s_star[:] = float(cfg["s_cruise"]) * 0.55

        recover_start = start + dur
        if t >= recover_start and not full_clip:
            if mode == "startle":
                self.state_timer -= self.dt
                done = (self.state == STATE_STARTLE) & (self.state_timer <= 0)
                if np.any(done):
                    self.state[done] = STATE_RECOVER
            alpha = 0.08
            self.w_r += alpha * (float(cfg["w_r"]) - self.w_r)
            self.w_o += alpha * (float(cfg["w_o"]) - self.w_o)
            self.w_a += alpha * (float(cfg["w_a"]) - self.w_a)
            self.w_p *= 1.0 - alpha
            self.d0 += alpha * (self.d0_base - self.d0)
            self.s_star += alpha * (float(cfg["s_cruise"]) - self.s_star)
            if t > recover_start + 90:
                self.state[:] = STATE_BASELINE
                self.z[:] = 0.0

    def step(self) -> None:
        cfg = self.cfg
        self._update_threat()
        headings = self.headings()
        t_r, t_o, t_a = self._social(headings)
        t_w = self._wall()
        t_p = self._predator()
        t_circ = np.zeros(self.n)
        w_circ = float(cfg.get("w_circ", 0.0))
        if w_circ > 0:
            r = self.pos - self.center
            desired = np.arctan2(r[:, 1], r[:, 0]) + self.circ_sign * np.pi / 2
            t_circ = w_circ * _wrap(desired - self.theta)
        t_cent = np.zeros(self.n)
        if np.any(self.state == STATE_COMPACT):
            to_c = self.center - self.pos
            desired = np.arctan2(to_c[:, 1], to_c[:, 0])
            t_cent = 0.9 * _wrap(desired - self.theta)
        omega = (
            self.w_r * t_r + self.w_o * t_o + self.w_a * t_a + t_w + self.w_p * t_p + t_circ + t_cent
            + self.rng.normal(0, float(cfg["sigma_theta"]), self.n)
        )
        omega = np.clip(omega, -float(cfg["omega_max"]), float(cfg["omega_max"]))
        self.theta = np.mod(self.theta + omega * self.dt, 2 * np.pi)
        a = np.clip(
            (self.s_star - self.speed) / max(float(cfg["tau_s"]), 1e-6),
            -float(cfg["a_max"]),
            float(cfg["a_max"]),
        )
        sigma_s = float(cfg.get("sigma_speed", 0.0))
        speed_noise = self.rng.normal(0, sigma_s, self.n) * np.sqrt(self.dt) if sigma_s > 0 else 0.0
        self.speed = np.clip(
            self.speed + a * self.dt + speed_noise,
            float(cfg["s_min"]),
            float(cfg.get("s_escape", 3.0)) * 1.2,
        )
        self.pos = self.pos + self.velocities() * self.dt
        w_file = float(cfg.get("w_file", 0.0))
        if w_file > 0:
            centroid = self.pos.mean(axis=0)
            mean_h = self.headings().mean(axis=0)
            norm_h = np.linalg.norm(mean_h)
            if norm_h > 0.3:
                mean_h = mean_h / norm_h
                perp = np.array([-mean_h[1], mean_h[0]])
                offset = (self.pos - centroid) @ perp
                self.pos -= w_file * offset[:, None] * perp[None, :]
        self.frame += 1

    def run(self) -> SimResult:
        cfg = self.cfg
        self.in_recording = False
        for _ in range(int(cfg["burn_in"])):
            self.step()
        T = int(cfg["record_frames"])
        pos_hist = np.zeros((T, self.n, 2))
        vel_hist = np.zeros((T, self.n, 2))
        self._reset_baseline_params()
        self.frame = 0
        self.in_recording = True
        for t in range(T):
            self.step()
            pos_hist[t] = self.pos
            vel_hist[t] = self.velocities()
        self.in_recording = False
        return SimResult(
            positions=pos_hist,
            velocities=vel_hist,
            meta={"n": self.n, "behavior": cfg.get("behavior"), "fps": self.fps},
        )


def run_simulation_fast(behavior: str, n: int, seed: int, overrides: dict | None = None) -> SimResult:
    from src.sim.config import deep_merge, load_behavior_config
    from src.labels import BEHAVIOR_SHORT

    short = BEHAVIOR_SHORT[behavior]
    base = load_behavior_config(short)
    if overrides:
        base = deep_merge(base, overrides)
    base["behavior"] = behavior
    return FastSchoolSimulator(n=n, cfg=base, seed=seed).run()
