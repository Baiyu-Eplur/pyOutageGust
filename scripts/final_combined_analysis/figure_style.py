"""Shared RESS-compliant figure style settings, v3 (command #35 revision).

Command #34 supersedes command #33's Section 0 on three points:
  1. Map figures must carry a scale bar + north arrow (+ GB locator inset).
  2. No in-figure title text anywhere -- the filename is the figure's name.
  3. In-figure text sizes raised to the 9-10pt band (was 7-8pt).

Command #35 redesigns the map furniture for a cleaner, consistent look:
  - Locator inset: always top-left, with a thin border and white background.
  - North arrow: an elongated triangle (not a thick matplotlib annotate-arrow),
    always bottom-right.
  - Scale bar: a thin line with solid dot end caps (not a filled block bar),
    always bottom-left.
"""
from __future__ import annotations

from matplotlib.patches import Polygon, Rectangle
import matplotlib as mpl
import matplotlib.pyplot as plt

MM_TO_INCH = 1 / 25.4
SINGLE_COL_MM = 90.0
DOUBLE_COL_MM = 185.0


def apply_style():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "axes.labelsize": 10,
        "axes.titlesize": 10,  # reserved for panel labels (a)(b), never a figure title
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "font.size": 9,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.2,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "axes.grid": False,
        "pdf.fonttype": 42,  # embed fonts as real vector text, not outline paths
        "ps.fonttype": 42,
    })


def mm_to_in(mm: float) -> float:
    return mm * MM_TO_INCH


def panel_label(ax, label: str, x=-0.10, y=1.05):
    """(a)(b)(c)(d) panel labels: 10pt bold. Not a figure title."""
    ax.text(x, y, label, transform=ax.transAxes, fontsize=10, fontweight="bold",
             va="bottom", ha="right")


def add_north_arrow(ax, x=0.93, y=0.08, height=0.075, width_ratio=0.24):
    """Elongated-triangle north arrow, bottom-right by default. 9pt 'N' label above the tip."""
    half_w = height * width_ratio
    tip_y = y + height
    tri = Polygon(
        [(x - half_w, y), (x + half_w, y), (x, tip_y)],
        closed=True, transform=ax.transAxes, facecolor="#222222", edgecolor="none", zorder=10,
    )
    ax.add_patch(tri)
    ax.text(x, tip_y + 0.012, "N", transform=ax.transAxes, fontsize=9, fontweight="bold",
             ha="center", va="bottom", color="#222222", zorder=10)


def _nice_length_km(width_m: float) -> float:
    """Round a target scale-bar length (~22% of the visible map width) to a clean number."""
    target_km = (width_m / 1000.0) * 0.22
    steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000]
    return min(steps, key=lambda v: abs(v - target_km))


def add_scale_bar(ax, location="lower left", x0=None, y0=0.055):
    """Thin scale bar with solid dot end caps, in a projected CRS with metre units
    (e.g. EPSG:27700). Position is fixed in axes-fraction coordinates so it stays
    in the same corner regardless of the map's data extent."""
    xlim = ax.get_xlim()
    width_m = abs(xlim[1] - xlim[0])
    length_km = _nice_length_km(width_m)
    frac_len = (length_km * 1000.0) / width_m

    if x0 is None:
        x0 = 0.04 if "left" in location else 0.96 - frac_len
    x1 = x0 + frac_len

    ax.plot([x0, x1], [y0, y0], transform=ax.transAxes, color="#222222",
             linewidth=0.9, solid_capstyle="butt", zorder=10)
    ax.plot([x0, x1], [y0, y0], transform=ax.transAxes, color="#222222",
             marker="o", markersize=3.2, linestyle="none", zorder=11)
    ax.text((x0 + x1) / 2, y0 + 0.018, f"{length_km:g} km", transform=ax.transAxes,
             fontsize=9, ha="center", va="bottom", color="#222222", zorder=10)


def add_locator_inset(fig, ax_main, gb_boundary_gdf, highlight_gdf, rect=(0.02, 0.72, 0.20, 0.20)):
    """Small bordered GB-outline inset (always top-left) showing where the main
    map sits within Great Britain."""
    ax_inset = fig.add_axes(rect)
    ax_inset.set_facecolor("white")
    gb_boundary_gdf.plot(ax=ax_inset, color="#ececec", edgecolor="#aaaaaa", linewidth=0.35, zorder=1)
    highlight_gdf.dissolve().plot(ax=ax_inset, color="#d95f02", edgecolor="none", zorder=2)
    ax_inset.set_axis_off()
    ax_inset.set_aspect("equal")
    ax_inset.add_patch(Rectangle(
        (0, 0), 1, 1, transform=ax_inset.transAxes, fill=False,
        edgecolor="#888888", linewidth=0.6, zorder=3,
    ))
    return ax_inset


def save_fig(fig, out_dir, basename: str, dpi_png=300):
    fig.savefig(out_dir / f"{basename}.pdf", bbox_inches="tight")
    fig.savefig(out_dir / f"{basename}.png", dpi=dpi_png, bbox_inches="tight")
