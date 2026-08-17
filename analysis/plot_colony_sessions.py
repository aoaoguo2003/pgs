# -*- coding: utf-8 -*-
"""Figure: capture sessions per individual across the whole 81-bird colony.

The report argues that accuracy is set by capture sessions rather than photograph
count, and derives a collection standard of >= 4 sessions per individual. Figure
05 shows PHOTOGRAPHS per individual -- the variable the results say is not the
binding one. This is its counterpart for the variable that is.

Uses the same session rule and the same palette as the rest of the figure set.

Run:
  D:/Anaconda/python.exe analysis/plot_colony_sessions.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_disjoint_eval import cluster_sessions  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "penguins_data"
OUT = ROOT / "figures"
GAP = 50
TARGET = 4
IMG = (".jpg", ".jpeg", ".png")

BLUE, ORANGE = "#2a78d6", "#eb6834"
SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.axisbelow": True, "figure.dpi": 300, "savefig.bbox": "tight",
})

sessions = []
for bird in sorted(os.listdir(SRC)):
    d = SRC / bird
    if not d.is_dir():
        continue
    names = sorted(f for f in os.listdir(d) if f.lower().endswith(IMG))
    if names:
        sessions.append(len(cluster_sessions(names, GAP)))

sessions.sort(reverse=True)
n = len(sessions)
met = sum(1 for s in sessions if s >= TARGET)
short = n - met
deficit = sum(TARGET - s for s in sessions if s < TARGET)

fig, ax = plt.subplots(figsize=(9.2, 3.6))
colours = [BLUE if s >= TARGET else ORANGE for s in sessions]
ax.bar(range(n), sessions, color=colours, width=0.82, linewidth=0)

ax.axhline(TARGET, color=MUTED, linewidth=1.0, linestyle="--", zorder=3)
ax.text(n - 0.5, TARGET + 0.5, f"target: {TARGET} capture sessions",
        ha="right", va="bottom", color=MUTED, fontsize=9)

ax.set_xlabel("individual (sorted by number of capture sessions)")
ax.set_ylabel("capture sessions")
ax.set_title("Capture sessions per individual across the colony", loc="left")
ax.set_xlim(-1, n)
ax.set_ylim(0, max(sessions) * 1.12)

for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_linewidth(0.8)
ax.grid(True, axis="y")
ax.tick_params(length=3, width=0.8)

ax.text(0.985, 0.80, f"{met} of {n} individuals reach {TARGET}",
        transform=ax.transAxes, ha="right", va="top", color=BLUE, fontsize=10)
ax.text(0.985, 0.66, f"{short} fall short",
        transform=ax.transAxes, ha="right", va="top", color=ORANGE, fontsize=10)

fig.text(0.005, -0.10,
         f"Same session rule as the evaluation (filename prefix, frame gap \u2264 {GAP}). "
         f"Bringing every colony member to {TARGET} sessions requires {deficit} further "
         f"individual capture encounters,",
         color=MUTED, fontsize=9, ha="left")
fig.text(0.005, -0.155,
         "roughly eight outings at about fifteen birds each, which must fall on different days.",
         color=MUTED, fontsize=9, ha="left")

OUT.mkdir(exist_ok=True)
path = OUT / "13_colony_sessions_per_individual.png"
fig.savefig(path)
plt.close(fig)
print(f"wrote {path.relative_to(ROOT)}")
print(f"  {n} individuals, {met} meet target, {short} short, {deficit} additional encounters")
