"""Search space for behavior YAML overrides."""

from __future__ import annotations

import copy
from typing import Any

from src.labels import CANONICAL

# Radii are fixed from annotated_config.csv (the extraction grid) and are not searched.
# sigma_theta spans the real per-frame heading noise (extracted medians 0.11-0.19).
# omega_max is capped at 0.1 for every behavior.
SEARCH_SPACE: dict[str, dict[str, Any]] = {
    "traveling": {
        "w_r": (0.0, 3.2),
        "w_o": (1.2, 2.5),
        "w_a": (0.0, 1.8),
        "w_tan": (0.0, 0.30),
        "w_rad": (-0.30, 0.30),
        "sigma_theta": (0.01, 0.30),
        "s_0": (0.4, 2.60),
        "sigma_s": (0.0, 0.30),
        "omega_max": (0.04, 0.10),
        "a_max": (0.0, 1.20),
    },
    "milling": {
        "w_r": (0.0, 3.2),
        "w_o": (0.3, 1.8),
        "w_a": (0.0, 1.6),
        "w_tan": (0.0, 2.2),
        "w_rad": (-0.30, 0.30),
        "sigma_theta": (0.0, 0.30),
        "s_0": (0.4, 1.4),
        "sigma_s": (0.0, 0.30),
        "omega_max": (0.08, 0.10),
        "a_max": (0.0, 1.50),
    },
    "shoaling": {
        "w_r": (0.0, 2.8),
        "w_o": (0.0, 0.55),
        "w_a": (0.0, 2.0),
        "w_tan": (0.0, 0.30),
        "w_rad": (-0.35, 0.35),
        "sigma_theta": (0.04, 0.30),
        "s_0": (0.4, 1.8),
        "sigma_s": (0.0, 0.30),
        "omega_max": (0.03, 0.10),
        "a_max": (0.0, 1.80),
    },
    "expansion": {
        "w_r": (0.0, 2.2),
        "w_o": (0.2, 1.6),
        "w_a": (0.0, 0.70),
        "w_tan": (0.0, 0.20),
        "w_rad": (0.0, 2.20),
        "sigma_theta": (0.01, 0.30),
        "s_0": (0.4, 2.20),
        "sigma_s": (0.0, 0.30),
        "omega_max": (0.06, 0.10),
        "a_max": (0.0, 2.20),
    },
    "compaction": {
        "w_r": (0.0, 1.8),
        "w_o": (0.4, 2.2),
        "w_a": (0.0, 2.5),
        "w_tan": (0.0, 0.20),
        "w_rad": (-2.20, -0.80),
        "sigma_theta": (0.01, 0.30),
        "s_0": (0.3, 1.3),
        "sigma_s": (0.0, 0.30),
        "omega_max": (0.04, 0.10),
        "a_max": (0.0, 1.90),
    },
}
SEARCH_PARAM_NAMES: tuple[str, ...] = (
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


def random_samples(
    behavior: str,
    n: int,
    rng,
) -> list[dict[str, float]]:
    """n independent uniform draws from SEARCH_SPACE[behavior]."""
    if n <= 0 or behavior not in SEARCH_SPACE:
        return []
    return [_sample_node(rng, SEARCH_SPACE[behavior], None, 0.0) for _ in range(n)]


def param_bounds(behavior: str) -> list[tuple[str, float, float]]:
    """Ordered (name, low, high) bounds for SEARCH_SPACE[behavior]."""
    if behavior not in SEARCH_SPACE:
        raise KeyError(behavior)
    bounds: list[tuple[str, float, float]] = []
    for key, spec in SEARCH_SPACE[behavior].items():
        if isinstance(spec, tuple) and len(spec) == 2:
            bounds.append((key, float(spec[0]), float(spec[1])))
    return bounds


def unit_to_overrides(behavior: str, x) -> dict[str, float]:
    """Map a unit-cube point in [0, 1]^D back to behavior overrides."""
    ov: dict[str, float] = {}
    for (key, lo, hi), raw in zip(param_bounds(behavior), x):
        u = min(1.0, max(0.0, float(raw)))
        val: float | int = lo + u * (hi - lo)
        if key in _INT_KEYS:
            val = int(round(val))
        ov[key] = val
    return ov


def box_center_unit(behavior: str) -> list[float]:
    """Unit-cube center (0.5 on every tuned axis)."""
    return [0.5] * len(param_bounds(behavior))


def round_overrides(overrides: dict[str, dict]) -> dict[str, dict]:
    """Deep-copy overrides with stable float rounding for JSON logs."""

    def _round(obj):
        if isinstance(obj, dict):
            return {k: _round(v) for k, v in obj.items()}
        if isinstance(obj, float):
            return round(obj, 6)
        return obj

    return _round(copy.deepcopy(overrides))
