"""First-shell Voronoi neighbourhoods with rear blind spot."""

from __future__ import annotations

import numpy as np
from scipy.spatial import Voronoi


def voronoi_first_shell(positions: np.ndarray) -> list[list[int]]:
    """Return adjacency lists for first-shell Voronoi neighbours.

    positions: (N, 2)
    """
    n = positions.shape[0]
    neighbors: list[list[int]] = [[] for _ in range(n)]
    if n < 3:
        for i in range(n):
            neighbors[i] = [j for j in range(n) if j != i]
        return neighbors

    try:
        vor = Voronoi(positions)
    except Exception:
        # Degenerate: fall back to kNN
        return knn_neighbors(positions, k=min(6, n - 1))

    for i, j in vor.ridge_points:
        neighbors[int(i)].append(int(j))
        neighbors[int(j)].append(int(i))
    return neighbors


def knn_neighbors(positions: np.ndarray, k: int = 6) -> list[list[int]]:
    n = positions.shape[0]
    if n <= 1:
        return [[] for _ in range(n)]
    k = min(k, n - 1)
    d2 = np.sum((positions[:, None, :] - positions[None, :, :]) ** 2, axis=-1)
    np.fill_diagonal(d2, np.inf)
    idx = np.argpartition(d2, kth=k, axis=1)[:, :k]
    return [idx[i].tolist() for i in range(n)]


def filter_visual(
    i: int,
    j_list: list[int],
    positions: np.ndarray,
    headings: np.ndarray,
    blind_half_angle: float = np.deg2rad(30.0),
    max_dist: float | None = None,
) -> list[int]:
    """Drop neighbours in rear blind region and beyond max_dist."""
    if not j_list:
        return []
    pi = positions[i]
    hi = headings[i]
    out = []
    cos_blind = np.cos(np.pi - blind_half_angle)
    for j in j_list:
        d = positions[j] - pi
        dist = np.linalg.norm(d)
        if dist < 1e-12:
            continue
        if max_dist is not None and dist > max_dist:
            continue
        u = d / dist
        # Blind if behind heading
        if np.dot(hi, u) < cos_blind:
            continue
        out.append(j)
    return out
