"""Continuous bounded-acceleration ROA fish-school simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from src.sim.neighbors import filter_visual, knn_neighbors, voronoi_first_shell


STATE_BASELINE = 0
STATE_FOUNTAIN = 1
STATE_STARTLE = 2
STATE_COMPACT = 3
STATE_RECOVER = 4


@dataclass
class SimResult:
    positions: np.ndarray  # (T, N, 2)
    velocities: np.ndarray
    metrics: dict[str, float] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


class SchoolSimulator:
    def __init__(self, n: int, cfg: dict[str, Any], seed: int = 0):
        self.n = n
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        self.dt = float(cfg["dt"])
        self.fps = float(cfg["fps"])

        arena = cfg["arena"]
        self.center = np.asarray(arena["center"], dtype=np.float64)
        self.radius = float(arena["radius"])
        self.wall_margin = float(arena["wall_margin"])
        self.w_wall = float(arena["w_wall"])

        self.pos = np.zeros((n, 2), dtype=np.float64)
        self.theta = np.zeros(n, dtype=np.float64)
        self.speed = np.full(n, float(cfg["s_cruise"]), dtype=np.float64)
        self.state = np.full(n, STATE_BASELINE, dtype=np.int32)
        self.state_timer = np.zeros(n, dtype=np.float64)
        self.z = np.zeros(n, dtype=np.float64)
        self.circ_sign = np.ones(n, dtype=np.float64)

        self.predator_pos: np.ndarray | None = None
        self.predator_vel: np.ndarray | None = None
        self.frame = 0
        self.d0_base = float(cfg["d0"])
        self.d0 = np.full(n, self.d0_base, dtype=np.float64)

        # Per-fish weight multipliers (threat modifies)
        self.w_r = np.full(n, float(cfg["w_r"]))
        self.w_o = np.full(n, float(cfg["w_o"]))
        self.w_a = np.full(n, float(cfg["w_a"]))
        self.w_p = np.zeros(n, dtype=np.float64)
        self.s_star = np.full(n, float(cfg["s_cruise"]))

        self._init_agents()

    def _init_agents(self) -> None:
        cfg = self.cfg
        # Compact blob near arena center
        ang = self.rng.uniform(0, 2 * np.pi, self.n)
        rad = self.rng.uniform(0, 0.35 * self.radius, self.n)
        self.pos[:, 0] = self.center[0] + rad * np.cos(ang)
        self.pos[:, 1] = self.center[1] + rad * np.sin(ang)

        behavior = cfg.get("behavior", "traveling_polarized")
        if behavior == "milling":
            # Tangential headings for mill; optional opposite subpopulations
            r = self.pos - self.center
            base = np.arctan2(r[:, 1], r[:, 0]) + np.pi / 2
            frac_bi = float(cfg.get("bidirectional_frac", 0.0))
            if frac_bi > 0:
                flip = self.rng.random(self.n) < frac_bi
                self.circ_sign = np.where(flip, -1.0, 1.0)
                self.theta = base + np.where(flip, np.pi, 0.0)
            else:
                # Random global CW or CCW
                sense = 1.0 if self.rng.random() < 0.5 else -1.0
                self.circ_sign[:] = sense
                self.theta = np.arctan2(r[:, 1], r[:, 0]) + sense * np.pi / 2
            self.theta += self.rng.normal(0, 0.2, self.n)
        elif behavior == "swarming":
            self.theta = self.rng.uniform(0, 2 * np.pi, self.n)
            self.speed[:] = float(cfg["s_cruise"]) * self.rng.uniform(0.7, 1.1, self.n)
        else:
            # Polarized: common heading with noise
            h0 = self.rng.uniform(0, 2 * np.pi)
            self.theta = h0 + self.rng.normal(0, 0.25, self.n)

        self.theta = np.mod(self.theta, 2 * np.pi)
        self.speed = np.clip(self.speed, cfg["s_min"], cfg.get("s_escape", 3.0))

    def headings(self) -> np.ndarray:
        return np.stack((np.cos(self.theta), np.sin(self.theta)), axis=1)

    def velocities(self) -> np.ndarray:
        return self.speed[:, None] * self.headings()

    def _wall_torque(self, headings: np.ndarray) -> np.ndarray:
        rel = self.pos - self.center
        dist = np.linalg.norm(rel, axis=1)
        margin_start = self.radius - self.wall_margin
        torque = np.zeros(self.n)
        near = dist > margin_start
        if not np.any(near):
            return torque
        # Desired heading: tangential along wall (inward component)
        radial = rel[near] / np.maximum(dist[near, None], 1e-9)
        # Prefer heading with inward + along-wall mix
        inward = -radial
        strength = ((dist[near] - margin_start) / max(self.wall_margin, 1e-6)) ** 2
        # Turning angle toward inward
        desired = np.arctan2(inward[:, 1], inward[:, 0])
        dtheta = _wrap(desired - self.theta[near])
        torque[near] = self.w_wall * strength * dtheta
        outside = dist > self.radius
        if np.any(outside):
            r_out = rel[outside] / np.maximum(dist[outside, None], 1e-9)
            self.pos[outside] = self.center + r_out * (self.radius * 0.98)
        return torque

    def _social_torques(self, headings: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        cfg = self.cfg
        n = self.n
        if cfg.get("use_voronoi", True) and n >= 3:
            neigh = voronoi_first_shell(self.pos)
        else:
            neigh = knn_neighbors(self.pos, k=min(7, n - 1))

        blind = np.deg2rad(float(cfg["blind_half_deg"]))
        max_d = float(cfg["max_neighbor_dist"])
        r_rep = float(cfg["r_repulse"])
        r_ori = float(cfg["r_orient"])
        r_att = float(cfg["r_attract"])
        cross_scale = float(cfg.get("cross_align_scale", 1.0))

        t_r = np.zeros(n)
        t_o = np.zeros(n)
        t_a = np.zeros(n)

        for i in range(n):
            js = filter_visual(i, neigh[i], self.pos, headings, blind, max_d)
            if not js:
                continue
            pi = self.pos[i]
            hi = headings[i]
            for j in js:
                dvec = self.pos[j] - pi
                dist = np.linalg.norm(dvec)
                if dist < 1e-9:
                    continue
                u = dvec / dist
                # Repulsion: turn away if too close (relative to preferred d0)
                d0_i = self.d0[i]
                if dist < max(r_rep, d0_i):
                    away = -u
                    desired = np.arctan2(away[1], away[0])
                    w = (max(r_rep, d0_i) - dist) / max(r_rep, d0_i)
                    t_r[i] += w * _wrap(desired - self.theta[i])

                # Orientation
                if dist < r_ori:
                    align_w = 1.0
                    if cross_scale < 1.0:
                        # Reduce alignment with opposite heading
                        if np.dot(hi, headings[j]) < 0:
                            align_w = cross_scale
                    desired = self.theta[j]
                    t_o[i] += align_w * _wrap(desired - self.theta[i]) * (1.0 - dist / r_ori)

                # Attraction toward distant neighbours
                if dist > d0_i and dist < r_att:
                    desired = np.arctan2(u[1], u[0])
                    w = (dist - d0_i) / (r_att - d0_i + 1e-9)
                    t_a[i] += w * _wrap(desired - self.theta[i])

        return t_r, t_o, t_a

    def _predator_torque(self, headings: np.ndarray) -> np.ndarray:
        torque = np.zeros(self.n)
        if self.predator_pos is None or self.predator_vel is None:
            return torque
        cfg_t = self.cfg["threat"]
        flee_ang = np.deg2rad(float(cfg_t["flee_angle_deg"]))
        resp = float(cfg_t["predator_radius"])
        pv = self.predator_vel
        pv_n = np.linalg.norm(pv)
        if pv_n < 1e-9:
            side = np.array([0.0, 1.0])
        else:
            # Perpendicular to predator travel
            side = np.array([-pv[1], pv[0]]) / pv_n

        for i in range(self.n):
            rpi = self.pos[i] - self.predator_pos  # predator -> fish? flee away from predator
            # Vector from predator to fish
            dist = np.linalg.norm(rpi)
            if dist > resp or dist < 1e-9:
                continue
            radial = rpi / dist
            # Side opposite predator travel: choose sign so fish goes around
            # Sign: send toward side opposite predator's direction of travel relative to fish
            # Use cross product (pv x rpi)_z to choose side
            cross = pv[0] * rpi[1] - pv[1] * rpi[0]
            sgn = 1.0 if cross >= 0 else -1.0
            # Rotate radial flee by ±flee_ang
            ca, sa = np.cos(flee_ang), np.sin(flee_ang)
            # Rotate radial away from predator by signed angle
            fx = radial[0] * ca - sgn * radial[1] * sa
            fy = radial[1] * ca + sgn * radial[0] * sa
            # Also bias with side
            flee = np.array([fx, fy]) + 0.15 * sgn * side
            flee /= np.linalg.norm(flee) + 1e-12
            desired = np.arctan2(flee[1], flee[0])
            strength = 1.0 - dist / resp
            torque[i] = strength * _wrap(desired - self.theta[i])
            # Activation for startle cascade
            self.z[i] += float(cfg_t["beta_p"]) * strength * self.dt
        return torque

    def _update_threat_state(self) -> None:
        cfg = self.cfg
        threat = cfg["threat"]
        if not threat.get("enabled"):
            return

        mode = threat.get("mode")
        start = int(threat["start_frame"])
        dur = int(threat["duration"])
        t = self.frame

        # Schedule predator for fountain / startle / compact cues
        if mode in ("fountain", "startle", "compact") and start <= t < start + dur:
            if self.predator_pos is None:
                # Cross arena horizontally through school centroid
                y0 = float(np.mean(self.pos[:, 1]))
                spd = float(threat["predator_speed"])
                self.predator_pos = np.array(
                    [self.center[0] - self.radius - 50.0, y0], dtype=np.float64
                )
                self.predator_vel = np.array([spd, 0.0], dtype=np.float64)
            else:
                self.predator_pos = self.predator_pos + self.predator_vel * self.dt
        elif t >= start + dur:
            self.predator_pos = None
            self.predator_vel = None

        # Excitable startle cascade
        if mode == "startle" and start <= t < start + dur + int(threat["escape_duration"]):
            neigh = knn_neighbors(self.pos, k=min(5, self.n - 1))
            beta_n = float(threat["beta_n"])
            tau_z = float(threat["tau_z"])
            z_thr = float(threat["z_thr"])
            dz = -self.z / max(tau_z, 1e-6)
            for i in range(self.n):
                for j in neigh[i]:
                    if self.z[j] > z_thr or self.state[j] == STATE_STARTLE:
                        dz[i] += beta_n * 0.25
            self.z = np.clip(self.z + dz * self.dt, 0.0, 3.0)
            newly = (self.z > z_thr) & (self.state != STATE_STARTLE)
            if np.any(newly):
                self.state[newly] = STATE_STARTLE
                self.state_timer[newly] = float(threat["escape_duration"]) * self.dt
                self.s_star[newly] = float(cfg["s_escape"])
                self.w_r[newly] = float(cfg["w_r"]) * 2.2
                self.w_a[newly] = float(cfg["w_a"]) * 0.25
                self.w_o[newly] = float(cfg["w_o"]) * 0.2
                # Turn roughly away from predator / outward
                if self.predator_pos is not None:
                    away = self.pos[newly] - self.predator_pos
                else:
                    away = self.pos[newly] - self.center
                self.theta[newly] = np.arctan2(away[:, 1], away[:, 0]) + self.rng.normal(
                    0, 0.4, np.sum(newly)
                )

        if mode == "fountain" and start <= t < start + dur:
            self.state[:] = STATE_FOUNTAIN
            self.w_p[:] = float(threat["w_p"])
            # Keep residual social
            self.w_a[:] = float(cfg["w_a"]) * 0.7
            self.w_o[:] = float(cfg["w_o"]) * 0.5

        if mode == "compact" and start <= t < start + dur:
            self.state[:] = STATE_COMPACT
            elapsed = (t - start) * self.dt
            tau = float(threat["compact_tau"]) * self.dt
            delta = float(threat["compact_delta_d0"])
            factor = 1.0 - np.exp(-elapsed / max(tau, 1e-6))
            self.d0[:] = self.d0_base - delta * factor
            self.w_a[:] = float(cfg["w_a"]) * 1.6
            self.s_star[:] = float(cfg["s_cruise"]) * 0.75

        # Recovery after threat window
        recover_start = start + dur
        if t >= recover_start:
            recovering = self.state != STATE_BASELINE
            if mode == "startle":
                self.state_timer -= self.dt
                done = (self.state == STATE_STARTLE) & (self.state_timer <= 0)
                if np.any(done):
                    self.state[done] = STATE_RECOVER
            if t > recover_start + 30 or mode in ("fountain", "compact", "startle"):
                # Blend weights back
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
        self._update_threat_state()
        headings = self.headings()
        t_r, t_o, t_a = self._social_torques(headings)
        t_w = self._wall_torque(headings)
        t_p = self._predator_torque(headings)

        # Circulation bias for milling
        t_circ = np.zeros(self.n)
        w_circ = float(cfg.get("w_circ", 0.0))
        if w_circ > 0:
            r = self.pos - self.center
            desired = np.arctan2(r[:, 1], r[:, 0]) + self.circ_sign * np.pi / 2
            t_circ = w_circ * _wrap(desired - self.theta)

        sigma = float(cfg["sigma_theta"])
        noise = self.rng.normal(0, sigma, self.n)
        omega = (
            self.w_r * t_r
            + self.w_o * t_o
            + self.w_a * t_a
            + t_w
            + self.w_p * t_p
            + t_circ
            + noise
        )
        omega_max = float(cfg["omega_max"])
        omega = np.clip(omega, -omega_max, omega_max)
        self.theta = np.mod(self.theta + omega * self.dt, 2 * np.pi)

        # Speed dynamics
        a = (self.s_star - self.speed) / max(float(cfg["tau_s"]), 1e-6)
        a = np.clip(a, -float(cfg["a_max"]), float(cfg["a_max"]))
        self.speed = np.clip(
            self.speed + a * self.dt,
            float(cfg["s_min"]),
            float(cfg.get("s_escape", 3.0)) * 1.2,
        )

        self.pos = self.pos + self.velocities() * self.dt
        self.frame += 1

    def run(self) -> SimResult:
        cfg = self.cfg
        burn = int(cfg["burn_in"])
        T = int(cfg["record_frames"])
        for _ in range(burn):
            self.step()

        pos_hist = np.zeros((T, self.n, 2), dtype=np.float64)
        vel_hist = np.zeros((T, self.n, 2), dtype=np.float64)
        # Adjust threat start relative to recording (threat.start_frame is in recorded frames)
        # During burn-in threat shouldn't trigger: start_frame is absolute from recording start.
        # Reset frame counter so threat.start_frame refers to recorded timeline.
        threat_cfg = cfg["threat"]
        saved_start = int(threat_cfg.get("start_frame", 0))
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
                "threat_start": saved_start,
                "fps": self.fps,
            },
        )


def _wrap(a: np.ndarray | float) -> np.ndarray | float:
    return (a + np.pi) % (2 * np.pi) - np.pi


def run_simulation(behavior: str, n: int, seed: int, cfg: dict[str, Any] | None = None) -> SimResult:
    from src.sim.config import load_behavior_config

    short = {
        "traveling_polarized": "tpol",
        "milling": "milling",
        "swarming": "swarming",
        "fountain_evasion": "fountain",
        "expansion_burst": "expansion",
        "compaction": "compaction",
    }[behavior]
    base = load_behavior_config(short)
    if cfg:
        from src.sim.config import deep_merge

        base = deep_merge(base, cfg)
    base["behavior"] = behavior
    sim = SchoolSimulator(n=n, cfg=base, seed=seed)
    return sim.run()
