"""Load and merge behavior YAML configs."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs" / "behaviors"

# Simulation-level defaults (not behavior class parameters).
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
    "r_r": 30.0,
    "r_o": 90.0,
    "r_a": 150.0,
    "w_r": 1.6,
    "w_o": 1.0,
    "w_a": 0.8,
    "w_tan": 0.0,
    "w_rad": 0.0,
    "sigma_theta": 0.12,
    "s_0": 1.5,
    "sigma_s": 0.05,
    "omega_max": 0.45,
    "a_max": 0.35,
    "burn_in": 60,
    "record_frames": 150,
}

BEHAVIOR_KEYS = (
    "r_r",
    "r_o",
    "r_a",
    "w_r",
    "w_o",
    "w_a",
    "w_tan",
    "w_rad",
    "sigma_theta",
    "s_0",
    "sigma_s",
    "omega_max",
    "a_max",
)


def deep_merge(base: dict, override: dict) -> dict:
    out = deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = deepcopy(v)
    return out


def validate_radii(cfg: dict[str, Any]) -> None:
    r_r = float(cfg["r_r"])
    r_o = float(cfg["r_o"])
    r_a = float(cfg["r_a"])
    if not (0.0 < r_r < r_o < r_a):
        raise ValueError(f"Require 0 < r_r < r_o < r_a, got r_r={r_r}, r_o={r_o}, r_a={r_a}")


def load_behavior_config(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / f"{name}.yaml"
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    cfg = deep_merge(DEFAULTS, data)
    validate_radii(cfg)
    return cfg
