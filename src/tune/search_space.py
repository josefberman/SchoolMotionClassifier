"""Search space for behavior YAML overrides."""

from __future__ import annotations

import copy
from typing import Any

from src.labels import CANONICAL

# Ranges are (low, high) inclusive for uniform sampling.
SEARCH_SPACE: dict[str, dict[str, Any]] = {
    "traveling_polarized": {
        "sigma_theta": (0.06, 0.22),
        "theta_init_std": (0.08, 0.28),
        "speed_spread": (0.12, 0.28),
        "sigma_speed": (0.04, 0.10),
        "w_r": (1.2, 2.4),
        "w_o": (3.5, 6.5),
        "s_cruise": (1.5, 2.0),
    },
    "milling": {
        "sigma_theta": (0.10, 0.18),
        "theta_init_std": (0.04, 0.12),
        "speed_spread": (0.18, 0.30),
        "sigma_speed": (0.02, 0.06),
        "w_a": (2.4, 3.4),
        "w_circ": (2.8, 4.0),
        "s_cruise": (1.0, 1.3),
    },
    "swarming": {
        "sigma_theta": (0.40, 0.60),
        "speed_spread": (0.22, 0.38),
        "sigma_speed": (0.05, 0.10),
        "w_a": (0.40, 1.20),
        "w_o": (0.05, 0.35),
        "w_r": (1.2, 2.0),
        "s_cruise": (0.80, 1.0),
    },
    "expansion_burst": {
        "w_r": (0.5, 2.0),
        "w_o": (0.5, 3.5),
        "w_a": (0.3, 1.8),
        "sigma_theta": (0.003, 0.015),
        "theta_init_std": (0.25, 0.45),
        "speed_spread": (0.08, 0.18),
        "sigma_speed": (0.01, 0.04),
        "s_cruise": (1.0, 1.5),
        "s_escape": (1.8, 3.0),
        "threat": {
            "heading_noise": (0.30, 1.20),
            "radial_align": (0.0, 2.0),
            "w_r_scale": (0.5, 2.5),
            "w_o_scale": (0.4, 1.8),
            "w_a_scale": (0.3, 1.5),
            "predator_radius": (150, 210),
            "beta_p": (1.2, 2.0),
            "beta_n": (1.2, 2.0),
        },
    },
    "compaction": {
        "w_r": (0.3, 1.5),
        "w_o": (0.5, 2.5),
        "w_a": (0.8, 3.0),
        "sigma_theta": (0.001, 0.01),
        "theta_init_std": (0.20, 0.40),
        "speed_spread": (0.06, 0.15),
        "s_cruise": (0.90, 1.20),
        "threat": {
            "radial_align": (1.0, 8.0),
            "w_r_scale": (0.4, 1.5),
            "w_o_scale": (0.4, 1.5),
            "w_a_scale": (0.5, 2.0),
            "speed_scale": (0.75, 1.0),
            "predator_radius": (170, 230),
            "compact_delta_d0": (18, 32),
            "compact_tau": (3, 8),
        },
    },
}

_INT_KEYS = {
    "predator_radius",
    "compact_delta_d0",
    "compact_tau",
}


def _sample_leaf(rng, spec: tuple[float, float], *, jitter: float, center_val: float | None):
    lo, hi = spec
    if center_val is not None and jitter > 0:
        c = min(max(float(center_val), lo), hi)
        span = (hi - lo) * jitter
        lo = max(lo, c - span)
        hi = min(hi, c + span)
    if hi <= lo:
        if center_val is not None:
            return float(min(max(float(center_val), spec[0]), spec[1]))
        return float((spec[0] + spec[1]) / 2)
    return float(rng.uniform(lo, hi))


def _sample_node(rng, space: dict, center: dict | None, jitter: float) -> dict:
    out: dict = {}
    for key, spec in space.items():
        csub = (center or {}).get(key)
        if isinstance(spec, dict):
            out[key] = _sample_node(rng, spec, csub if isinstance(csub, dict) else None, jitter)
        elif isinstance(spec, tuple) and len(spec) == 2:
            val = _sample_leaf(rng, spec, jitter=jitter, center_val=csub if isinstance(csub, (int, float)) else None)
            if key in _INT_KEYS:
                val = int(round(val))
            out[key] = val
    return out


def sample_overrides(
    rng,
    *,
    behaviors: list[str] | None = None,
    center: dict[str, dict] | None = None,
    jitter: float = 0.0,
) -> dict[str, dict]:
    """Sample a full behavior-overrides dict from SEARCH_SPACE."""
    behaviors = behaviors or list(CANONICAL)
    out: dict[str, dict] = {}
    for behavior in behaviors:
        if behavior not in SEARCH_SPACE:
            continue
        out[behavior] = _sample_node(rng, SEARCH_SPACE[behavior], (center or {}).get(behavior), jitter)
    return out


def round_overrides(overrides: dict[str, dict]) -> dict[str, dict]:
    """Deep-copy overrides with stable float rounding for JSON logs."""

    def _round(obj):
        if isinstance(obj, dict):
            return {k: _round(v) for k, v in obj.items()}
        if isinstance(obj, float):
            return round(obj, 6)
        return obj

    return _round(copy.deepcopy(overrides))
