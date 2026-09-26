"""Static matplotlib figures for the markdown report.

Palette: validated categorical slots 1-2 (blue = arm A, orange = arm B) on a light
surface; recessive grid; thin 2px lines; legend plus direct end labels.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
ARM_COLORS = {"A": "#2a78d6", "B": "#eb6834"}
ARM_NAMES = {"A": "A: all rule-based signals", "B": "B: Jev-filtered"}


def _style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def reliability_plot(table: pd.DataFrame, question: str, split: str, brier: dict, path: Path):
    fig, (ax, axh) = plt.subplots(2, 1, figsize=(5.2, 5.6), sharex=True, facecolor=SURFACE,
                                  gridspec_kw={"height_ratios": [3, 1], "hspace": 0.08})
    _style(ax)
    _style(axh)
    ax.plot([0, 1], [0, 1], color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(0.97, 0.9, "perfect calibration", color=INK_2, fontsize=8, ha="right", rotation=0)
    t = table.dropna(subset=["mean_predicted"])
    ax.plot(t["mean_predicted"], t["observed_rate"], color=ARM_COLORS["A"], linewidth=2,
            marker="o", markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Observed frequency", color=INK_2, fontsize=9)
    bs = "n/a" if brier["brier"] is None else f"{brier['brier']:.3f}"
    ref = "n/a" if brier["brier_reference"] is None else f"{brier['brier_reference']:.3f}"
    ax.set_title(f"{question}  ({split}, n={brier['n']})", color=INK, fontsize=11, loc="left")
    ax.text(0.03, 0.93, f"Brier {bs}  ·  base-rate reference {ref}", color=INK_2, fontsize=8,
            transform=ax.transAxes)
    centers = (table["bin_low"] + table["bin_high"]) / 2
    axh.bar(centers, table["count"], width=0.1 - 0.01, color=ARM_COLORS["A"], alpha=0.35)
    axh.set_ylabel("Count", color=INK_2, fontsize=9)
    axh.set_xlabel("Jev probability", color=INK_2, fontsize=9)
    fig.savefig(path, dpi=130, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


def equity_plot(arms: dict[str, pd.DataFrame], split: str, path: Path):
    fig, ax = plt.subplots(figsize=(7.5, 3.8), facecolor=SURFACE)
    _style(ax)
    for arm, trades in arms.items():
        if trades.empty:
            continue
        t = trades.sort_values("exit_ts")
        eq = t["r_multiple"].cumsum()
        ax.plot(t["exit_ts"], eq, color=ARM_COLORS[arm], linewidth=2, label=ARM_NAMES[arm])
        ax.annotate(f"{arm}  {eq.iloc[-1]:+.1f}R", (t["exit_ts"].iloc[-1], eq.iloc[-1]),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
    ax.axhline(0, color=INK_2, linewidth=0.8)
    ax.set_ylabel("Cumulative R (net of costs)", color=INK_2, fontsize=9)
    ax.set_title(f"Equity curve, {split}", color=INK, fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.autofmt_xdate()
    fig.savefig(path, dpi=130, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
