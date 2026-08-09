"""Load and merge behavior YAML configs."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs" / "behaviors"

DEFAULTS: dict[str, Any] = {
    "fps": 30.0,
    # Frame-based integration: positions/velocities match real CSV units (px/frame).
    "dt": 1.0,
    "arena": {
        "shape": "square",
        "center": [1100.0, 750.0],
        "half_extent": 420.0,
        "wall_margin": 40.0,
        "w_wall": 2.5,
    },
    "body_length": 12.0,
    "r_repulse": 18.0,
    "r_orient": 55.0,
    "r_attract": 120.0,
    "d0": 28.0,
    "w_r": 1.8,
    "w_o": 1.0,
    "w_a": 0.8,
    "w_p": 0.0,
    "sigma_theta": 0.15,
    "theta_init_std": 0.25,
    "speed_spread": 0.22,
    "sigma_speed": 0.05,
    "omega_max": 0.45,
    "tau_s": 3.0,
    "a_max": 0.45,
    "s_cruise": 1.5,
    "s_min": 0.20,
    "s_escape": 3.5,
    "blind_half_deg": 30.0,
    "max_neighbor_dist": 160.0,
    "use_voronoi": True,
    "burn_in": 45,
    "record_frames": 150,
    "circulation_bias": 0.0,  # +1 / -1 for bidirectional mill subpopulations
    "w_circ": 0.0,
    "cross_align_scale": 1.0,
    "threat": {
        "enabled": False,
        "mode": None,  # fountain | startle | compact
        "full_clip": True,
        "start_frame": 0,
        "duration": 150,
        "predator_speed": 7.0,
        "predator_radius": 80.0,
        "flee_angle_deg": 35.0,
        "w_p": 4.5,
        "escape_duration": 45,
        "compact_delta_d0": 12.0,
        "compact_tau": 20.0,
        "z_thr": 0.55,
        "beta_p": 1.2,
        "beta_n": 0.8,
        "tau_z": 8.0,
    },
}


def deep_merge(base: dict, override: dict) -> dict:
    out = deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = deepcopy(v)
    return out


def load_behavior_config(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / f"{name}.yaml"
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    cfg = deep_merge(DEFAULTS, data)
    return sync_threat_to_record(cfg)


def sync_threat_to_record(cfg: dict[str, Any]) -> dict[str, Any]:
    """Keep threat behaviours active for the full recorded window."""
    threat = cfg.get("threat")
    if not threat or not threat.get("enabled"):
        return cfg
    if not threat.get("full_clip", True):
        return cfg
    rf = int(cfg["record_frames"])
    threat["start_frame"] = 0
    threat["duration"] = rf
    if threat.get("mode") == "startle":
        threat["escape_duration"] = rf
    return cfg
