"""Shared simulation types and the slower run_simulation entry point."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class SimResult:
    positions: np.ndarray  # (T, N, 2)
    velocities: np.ndarray
    metrics: dict[str, float] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


def _wrap(a: np.ndarray | float) -> np.ndarray | float:
    """Signed shortest-angle difference into [-pi, pi]."""
    return (a + np.pi) % (2 * np.pi) - np.pi


def run_simulation(behavior: str, n: int, seed: int, cfg: dict[str, Any] | None = None) -> SimResult:
    from src.sim.model_fast import run_simulation_fast

    return run_simulation_fast(behavior, n, seed, overrides=cfg)
