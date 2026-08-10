"""Publication-style rendering of school simulations (stills + video)."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle
from matplotlib.collections import PatchCollection

FISH_COLOR = "#3a86ff"
ARENA = "#b0b0b0"
BG = "#ffffff"
PREDATOR = "#c0392b"

VIDEO_FISH_LEN = 9.0
STILL_FISH_LEN = 12.0

_FISH_SHAPE = np.array([
    [0.50, 0.00],
    [0.42, 0.12],
    [0.25, 0.18],
    [0.05, 0.16],
    [-0.15, 0.11],
    [-0.35, 0.05],
    [-0.50, 0.00],
    [-0.35, -0.05],
    [-0.15, -0.11],
    [0.05, -0.16],
    [0.25, -0.18],
    [0.42, -0.12],
])


def _make_fish_patches(
    pos: np.ndarray,
    vel: np.ndarray,
    length: float,
) -> list[Polygon]:
    """Create rotated fish-shaped polygons for each agent."""
    n = pos.shape[0]
    speeds = np.linalg.norm(vel, axis=1)
    angles = np.arctan2(vel[:, 1], vel[:, 0])

    patches = []
    for i in range(n):
        a = angles[i] if speeds[i] > 1e-9 else 0.0
        cos_a, sin_a = np.cos(a), np.sin(a)
        rot = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
        verts = (rot @ (_FISH_SHAPE * length).T).T + pos[i]
        patches.append(Polygon(verts, closed=True))
    return patches


def _arena_rect(
    positions: np.ndarray,
    center: Sequence[float] | None = None,
    half_extent: float | None = None,
    pad: float = 40.0,
) -> tuple[np.ndarray, float, tuple[float, float, float, float]]:
    """Return center, half_extent, and (xmin, xmax, ymin, ymax) limits for framing."""
    if center is None:
        c = positions.reshape(-1, 2).mean(axis=0)
    else:
        c = np.asarray(center, dtype=float)
    if half_extent is None:
        rel = positions.reshape(-1, 2) - c
        he = float(max(np.max(np.abs(rel[:, 0])), np.max(np.abs(rel[:, 1]))) * 1.12 + pad * 0.5)
    else:
        he = float(half_extent)
    lim = (c[0] - he - pad, c[0] + he + pad, c[1] - he - pad, c[1] + he + pad)
    return c, he, lim


def _make_axes(
    figsize: tuple[float, float],
    dpi: int,
    *,
    title: str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(BG)
    if title:
        fig.subplots_adjust(left=0.06, right=0.94, bottom=0.06, top=0.78)
        fig.text(
            0.5,
            0.93,
            title,
            ha="center",
            va="bottom",
            fontsize=11,
            color="#222222",
            fontfamily="sans-serif",
        )
    else:
        fig.subplots_adjust(left=0.06, right=0.94, bottom=0.06, top=0.94)
    return fig, ax


def _draw_frame(
    ax: plt.Axes,
    pos: np.ndarray,
    vel: np.ndarray,
    *,
    center: np.ndarray,
    half_extent: float,
    limits: tuple[float, float, float, float],
    fish_len: float = STILL_FISH_LEN,
    arrow_scale: float = 0.35,
    show_arena: bool = True,
    predator: np.ndarray | None = None,
) -> None:
    ax.clear()
    ax.set_facecolor(BG)
    ax.set_aspect("equal")
    ax.set_xlim(limits[0], limits[1])
    ax.set_ylim(limits[2], limits[3])
    ax.axis("off")

    if show_arena:
        ax.add_patch(
            Rectangle(
                (center[0] - half_extent, center[1] - half_extent),
                2 * half_extent,
                2 * half_extent,
                fill=False,
                edgecolor=ARENA,
                linewidth=1.0,
                zorder=0,
            )
        )

    patches = _make_fish_patches(pos, vel, fish_len)
    col = PatchCollection(patches, facecolor=FISH_COLOR, edgecolor="none", alpha=0.92, zorder=2)
    ax.add_collection(col)

    if predator is not None:
        ax.scatter(
            [predator[0]],
            [predator[1]],
            s=90,
            c=PREDATOR,
            marker="X",
            linewidths=0.8,
            edgecolors="#7f1d1d",
            zorder=4,
        )


def save_still(
    positions: np.ndarray,
    velocities: np.ndarray,
    out_path: Path,
    *,
    frame: int | None = None,
    center: Sequence[float] | None = None,
    half_extent: float | None = None,
    title: str | None = None,
    dpi: int = 300,
    figsize: tuple[float, float] = (3.5, 3.8),
    predator: np.ndarray | None = None,
) -> Path:
    t = positions.shape[0]
    if frame is None:
        frame = t // 2
    frame = int(np.clip(frame, 0, t - 1))
    c, he, lim = _arena_rect(positions, center, half_extent)

    fig, ax = _make_axes(figsize, dpi, title=title)
    _draw_frame(
        ax,
        positions[frame],
        velocities[frame],
        center=c,
        half_extent=he,
        limits=lim,
        fish_len=STILL_FISH_LEN,
        predator=predator,
    )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, facecolor=BG, pad_inches=0.02)
    plt.close(fig)
    return out_path


def save_stills_panel(
    positions: np.ndarray,
    velocities: np.ndarray,
    out_dir: Path,
    frames: Sequence[int],
    *,
    stem: str = "frame",
    center: Sequence[float] | None = None,
    half_extent: float | None = None,
    title: str | None = None,
    dpi: int = 300,
) -> list[Path]:
    paths = []
    for i, f in enumerate(frames):
        p = Path(out_dir) / f"{stem}_{i:02d}_t{f:04d}.png"
        paths.append(
            save_still(
                positions,
                velocities,
                p,
                frame=f,
                center=center,
                half_extent=half_extent,
                title=title,
                dpi=dpi,
            )
        )
    return paths


def save_video(
    positions: np.ndarray,
    velocities: np.ndarray,
    out_path: Path,
    *,
    fps: float = 30.0,
    stride: int = 1,
    center: Sequence[float] | None = None,
    half_extent: float | None = None,
    title: str | None = None,
    dpi: int = 150,
    figsize: tuple[float, float] = (4.0, 4.3),
    arrow_scale: float = 0.35,
) -> Path:
    from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c, he, lim = _arena_rect(positions, center, half_extent)
    idx = np.arange(0, positions.shape[0], max(1, stride))

    fig, ax = _make_axes(figsize, dpi, title=title)

    def update(k: int) -> list:
        t = int(idx[k])
        _draw_frame(
            ax,
            positions[t],
            velocities[t],
            center=c,
            half_extent=he,
            limits=lim,
            fish_len=VIDEO_FISH_LEN,
            arrow_scale=arrow_scale,
        )
        return []

    anim = FuncAnimation(fig, update, frames=len(idx), interval=1000.0 / fps, blit=False)

    out_fps = max(1.0, fps / max(1, stride))
    written = out_path.with_suffix(".mp4")
    saved = False
    import logging
    logging.getLogger("matplotlib.animation").setLevel(logging.ERROR)
    for codec in ("mpeg4", "libx264", "h264", "libopenh264"):
        try:
            writer = FFMpegWriter(fps=out_fps, bitrate=1800, codec=codec,
                                  extra_args=["-loglevel", "error"])
            anim.save(str(written), writer=writer, dpi=dpi)
            if written.exists() and written.stat().st_size > 1000:
                saved = True
                break
        except Exception:
            if written.exists():
                written.unlink(missing_ok=True)
            continue
    if not saved:
        written = out_path.with_suffix(".gif")
        writer = PillowWriter(fps=max(1, int(round(out_fps))))
        anim.save(str(written), writer=writer, dpi=dpi)
    plt.close(fig)
    return written


def characteristic_frames(behavior: str, n_frames: int) -> list[int]:
    """Representative frames spread across the clip."""
    if n_frames <= 1:
        return [0]
    return [int(n_frames * f) for f in (0.25, 0.5, 0.75)]


def render_simulation(
    positions: np.ndarray,
    velocities: np.ndarray,
    out_dir: Path,
    stem: str,
    *,
    behavior: str | None = None,
    fps: float = 30.0,
    center: Sequence[float] | None = (1100.0, 750.0),
    half_extent: float | None = 420.0,
    video: bool = True,
    stills: bool = True,
    video_stride: int = 1,
    title: str | None = None,
) -> dict[str, list[str] | str | None]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict = {"stills": [], "video": None}

    if stills:
        frames = characteristic_frames(behavior or "", positions.shape[0])
        frames = [min(f, positions.shape[0] - 1) for f in frames]
        paths = save_stills_panel(
            positions,
            velocities,
            out_dir,
            frames,
            stem=f"{stem}_still",
            center=center,
            half_extent=half_extent,
            title=title,
        )
        result["stills"] = [str(p) for p in paths]

    if video:
        vpath = save_video(
            positions,
            velocities,
            out_dir / f"{stem}.mp4",
            fps=fps,
            stride=video_stride,
            center=center,
            half_extent=half_extent,
            title=title,
        )
        result["video"] = str(vpath)

    return result
