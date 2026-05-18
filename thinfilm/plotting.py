"""Shared plotting helpers for report-style figures.

The project exports figures for teaching cases and research modules.  This
module keeps the visual defaults consistent without changing the underlying
data or adding interpolated points.
"""

from __future__ import annotations

from typing import Sequence

import matplotlib.pyplot as plt


INK = "#172033"
MUTED = "#64748b"
GRID = "#d8dee9"
FRAME = "#b8c2d3"
PAPER = "#f7f3eb"
PANEL = "#fffdf8"
BLUE = "#2563eb"
CYAN = "#0891b2"
GREEN = "#15803d"
AMBER = "#d97706"
RED = "#dc2626"
PURPLE = "#7c3aed"

PALETTE = [BLUE, GREEN, AMBER, RED, CYAN, PURPLE]


def apply_plot_style() -> None:
    """Apply a consistent, presentation-oriented Matplotlib style."""
    plt.rcParams.update(
        {
            "font.sans-serif": [
                "Microsoft YaHei",
                "SimHei",
                "Noto Sans CJK SC",
                "Arial Unicode MS",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
            "figure.facecolor": PAPER,
            "axes.facecolor": PANEL,
            "axes.edgecolor": FRAME,
            "axes.labelcolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": INK,
            "axes.titleweight": "semibold",
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.frameon": True,
            "legend.facecolor": "#ffffff",
            "legend.edgecolor": "#d7dce5",
            "legend.framealpha": 0.92,
            "savefig.facecolor": PAPER,
            "savefig.dpi": 190,
        }
    )


def style_axis(ax: plt.Axes, *, grid: bool = True) -> None:
    """Style one axis using the shared report theme."""
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_color(FRAME)
        spine.set_linewidth(0.95)
    ax.tick_params(axis="both", colors=MUTED, labelsize=9)
    if grid:
        ax.grid(True, color=GRID, linewidth=0.75, alpha=0.65)
        ax.set_axisbelow(True)


def style_colorbar(cbar: object) -> None:
    """Style a Matplotlib colorbar if present."""
    if hasattr(cbar, "outline"):
        cbar.outline.set_edgecolor(FRAME)
        cbar.outline.set_linewidth(0.8)
    if hasattr(cbar, "ax"):
        cbar.ax.tick_params(colors=MUTED, labelsize=8)
        cbar.ax.yaxis.label.set_color(INK)


def annotate_point(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    *,
    xytext: tuple[float, float] = (8.0, 8.0),
) -> None:
    """Annotate a highlighted data point."""
    ax.annotate(
        text,
        xy=(x, y),
        xytext=xytext,
        textcoords="offset points",
        fontsize=8.5,
        color=INK,
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "#ffffff", "edgecolor": "#d7dce5", "alpha": 0.92},
        arrowprops={"arrowstyle": "->", "color": MUTED, "linewidth": 0.9},
    )


def add_value_labels(
    ax: plt.Axes,
    xs: Sequence[float],
    ys: Sequence[float],
    *,
    fmt: str = "{:.3f}",
    dy: float = 0.012,
) -> None:
    """Add compact numeric labels above markers or bars."""
    for x, y in zip(xs, ys):
        ax.text(float(x), float(y) + dy, fmt.format(float(y)), ha="center", va="bottom", fontsize=8, color=INK)


apply_plot_style()
