"""Search space for behavior YAML overrides."""

from __future__ import annotations

import copy
from typing import Any

from src.labels import CANONICAL

# Ranges are (low, high) inclusive for uniform sampling.
SEARCH_SPACE: dict[str, dict[str, Any]] = {
    "traveling_polarized": {
        "sigma_theta": (0.08, 0.18),
        "theta_init_std": (0.18, 0.38),
        "speed_spread": (0.15, 0.32),
        "sigma_speed": (0.04, 0.09),
        "w_o": (3.0, 5.0),
        "s_cruise": (1.5, 2.0),
    },
    "milling": {
        "sigma_theta": (0.06, 0.14),
        "theta_init_std": (0.15, 0.30),
        "speed_spread": (0.14, 0.26),
        "sigma_speed": (0.03, 0.08),
        "w_a": (2.0, 3.2),
        "w_circ": (1.8, 3.0),
        "s_cruise": (0.95, 1.35),
    },
    "swarming": {
        "sigma_theta": (0.40, 0.65),
        "speed_spread": (0.22, 0.38),
        "sigma_speed": (0.06, 0.12),
        "w_a": (1.2, 2.0),
        "w_o": (0.0, 0.12),
        "s_cruise": (0.70, 1.05),
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
        span = (hi - lo) * jitter
        lo = max(lo, center_val - span)
        hi = min(hi, center_val + span)
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
