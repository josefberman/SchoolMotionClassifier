"""Search space for behavior YAML overrides."""

from __future__ import annotations

import copy
from typing import Any

from src.labels import CANONICAL

# Ranges are (low, high) inclusive for uniform sampling.
# Interaction radii r_r=30, r_o=90, r_a=150 are fixed and not tuned.
SEARCH_SPACE: dict[str, dict[str, Any]] = {
    "traveling_polarized": {
        "w_r": (2.0, 3.0),
        "w_o": (0.5, 1.5),
        "w_a": (0.5, 1.5),
        "w_tan": (0.0, 0.12),
        "w_rad": (-0.08, 0.08),
        "sigma_theta": (0.0, 0.1),
        "s_0": (0.5, 1.5),
        "sigma_s": (0.0, 0.1),
        "omega_max": (0.0, 0.1),
        "a_max": (0.0, 0.5),
    },
    "milling": {
        "w_r": (2.0, 3.0),
        "w_o": (0.5, 1.5),
        "w_a": (0.5, 1.5),
        "w_tan": (0.35, 1.40),
        "w_rad": (-0.10, 0.10),
        "sigma_theta": (0.0, 0.1),
        "s_0": (0.5, 1.5),
        "sigma_s": (0.0, 0.1),
        "omega_max": (0.0, 0.1),
        "a_max": (0.0, 0.5),
    },
    "shoaling": {
        "w_r": (2.0, 3.0),
        "w_o": (0.5, 1.5),
        "w_a": (0.5, 1.5),
        "w_tan": (0.0, 0.10),
        "w_rad": (-0.12, 0.12),
        "sigma_theta": (0.0, 0.1),
        "s_0": (0.5, 1.5),
        "sigma_s": (0.0, 0.1),
        "omega_max": (0.0, 0.1),
        "a_max": (0.0, 0.5),
    },
    "expansion_burst": {
        "w_r": (2.0, 3.0),
        "w_o": (0.5, 1.5),
        "w_a": (0.5, 1.5),
        "w_tan": (0.0, 0.10),
        "w_rad": (0.20, 1.20),
        "sigma_theta": (0.0, 0.1),
        "s_0": (0.5, 1.5),
        "sigma_s": (0.0, 0.1),
        "omega_max": (0.0, 0.1),
        "a_max": (0.0, 0.5),
    },
    "compaction": {
        "w_r": (2.0, 3.0),
        "w_o": (0.5, 1.5),
        "w_a": (0.5, 1.5),
        "w_tan": (0.0, 0.10),
        "w_rad": (-1.20, -0.20),
        "sigma_theta": (0.0, 0.1),
        "s_0": (0.5, 1.5),
        "sigma_s": (0.0, 0.1),
        "omega_max": (0.0, 0.1),
        "a_max": (0.0, 0.5),
    },
}

_INT_KEYS: set[str] = set()


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
