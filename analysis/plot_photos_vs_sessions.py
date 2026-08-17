# -*- coding: utf-8 -*-
"""Figure: photographs against capture sessions, one point per colony member.

Carries four claims that are otherwise only prose:
  1. the two inclusion criteria and which individuals each one excludes
  2. that the session rule, not the photograph rule, is the binding one
  3. the proposed >= 4 session collection target
  4. Nicki vs Gonzo -- near-identical photograph counts, very different
     session counts, very different accuracy

Run:
  D:/Anaconda/python.exe analysis/plot_photos_vs_sessions.py
"""
from __future__ import annotations

import json
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
GAP, MIN_PHOTOS, MIN_SESSIONS, TARGET = 50, 16, 3, 4
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

birds = {}
for name in sorted(os.listdir(SRC)):
    d = SRC / name
    if not d.is_dir():
        continue
    files = sorted(f for f in os.listdir(d) if f.lower().endswith(IMG))
    if files:
        birds[name] = (len(files), len(cluster_sessions(files, GAP)))

evaluated = set(json.load(open(ROOT / "analysis/artifacts/cv_folds.json"))["folds"])

fig, ax = plt.subplots(figsize=(7.0, 4.6))

# Shade the region excluded by the session rule.
ax.axhspan(0.4, MIN_SESSIONS - 0.5, color=ORANGE, alpha=0.06, zorder=0)

kept = [(p, s) for b, (p, s) in birds.items() if b in evaluated]
drop = [(p, s) for b, (p, s) in birds.items() if b not in evaluated]
ax.scatter([p for p, _ in drop], [s for _, s in drop], s=42, color=ORANGE,
           alpha=0.8, linewidths=0.8, edgecolors=SURFACE, zorder=4,
           label=f"excluded ({len(drop)})")
ax.scatter([p for p, _ in kept], [s for _, s in kept], s=42, color=BLUE,
           alpha=0.85, linewidths=0.8, edgecolors=SURFACE, zorder=5,
           label=f"evaluated ({len(kept)})")

# Only the two INCLUSION criteria are drawn. The >= 4 session collection target is
# deliberately not shown: it is a conclusion derived in the Discussion from the
# accuracy gradient, so drawing it on a Methods figure would assert a result before
# its evidence, and a second reference line one unit from the 3-session rule reads
# as a second threshold. Set SHOW_TARGET = True only if this figure is moved to the
# Discussion, where the target has already been argued.
SHOW_TARGET = False

ax.axvline(MIN_PHOTOS, color=MUTED, lw=1.0, linestyle="--", zorder=2)
ax.axhline(MIN_SESSIONS - 0.5, color=MUTED, lw=1.0, linestyle="--", zorder=2)

ax.text(MIN_PHOTOS * 1.08, 26, "16 photographs", fontsize=8.5, color=MUTED, rotation=90,
        va="top")
ax.text(330, MIN_SESSIONS - 0.5, "3 sessions", fontsize=8.5, color=MUTED,
        ha="right", va="bottom")

if SHOW_TARGET:
    ax.axhline(TARGET, color=BLUE, lw=1.0, linestyle=":", zorder=2)
    ax.text(330, TARGET + 0.25, "proposed target: 4 sessions", fontsize=8.5, color=BLUE,
            ha="right", va="bottom")

# Nicki and Gonzo sit at almost the same x. A connector makes "same photograph
# count, different session count" readable without repeating the numbers, which
# the caption already gives.
(np_, ns_), (gp_, gs_) = birds["Nicki"], birds["Gonzo"]
xmid = (np_ * gp_) ** 0.5                      # geometric midpoint, x is log
ax.plot([xmid, xmid], [ns_, gs_], color=INK2, lw=0.9, linestyle="-",
        alpha=0.55, zorder=3)
for label, dx, dy, ha in (("Nicki", 13, -4, "left"), ("Gonzo", -13, 6, "right")):
    p, s = birds[label]
    ax.annotate(label, (p, s), textcoords="offset points", xytext=(dx, dy),
                fontsize=9, color=INK2, ha=ha)
    ax.scatter([p], [s], s=95, facecolors="none", edgecolors=INK2,
               linewidths=1.2, zorder=6)
# Anchored high on the connector: the band above y=10 and right of the connector
# is the only region of the panel with no points in it.
ax.annotate("same photograph count,\nfour times the accuracy", (xmid, 10.8),
            textcoords="offset points", xytext=(14, 0), fontsize=8.5,
            color=INK2, va="center", ha="left")

ax.set_xscale("log")
ax.set_xlim(0.8, 380)
ax.set_ylim(0.4, 26)
ax.set_xticks([1, 3, 10, 16, 30, 100, 291])
ax.set_xticklabels(["1", "3", "10", "16", "30", "100", "291"])
ax.set_xlabel("photographs held for that individual (log scale)")
ax.set_ylabel("capture sessions")
ax.set_title("Photographs and capture sessions are not the same thing", loc="left")
ax.legend(frameon=False, loc="upper left", fontsize=9, labelcolor=INK2)

for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_linewidth(0.8)
ax.grid(True, axis="both")
ax.tick_params(length=3, width=0.8)

n_lo_sess = sum(1 for p, s in birds.values() if s < MIN_SESSIONS)
n_lo_phot = sum(1 for p, s in birds.values() if p < MIN_PHOTOS)
both = sum(1 for p, s in birds.values() if s < MIN_SESSIONS and p < MIN_PHOTOS)

lines = [
    f"One point per colony member ({len(birds)} individuals). {n_lo_sess} fall below three "
    f"capture sessions and {n_lo_phot} below sixteen photographs",
    f"({both} fail both). Nicki and Gonzo hold almost the same number of photographs but "
    f"differ fourfold in accuracy (0.189 against 0.827),",
    "because they differ in the number of separate occasions on which they were photographed.",
]
for i, line in enumerate(lines):
    fig.text(0.005, -0.06 - 0.055 * i, line, fontsize=8.5, color=MUTED, ha="left")

OUT.mkdir(exist_ok=True)
path = OUT / "14_photos_vs_sessions.png"
fig.savefig(path)
plt.close(fig)
print(f"wrote {path.relative_to(ROOT)}")
print(f"  {len(birds)} individuals | evaluated {len(kept)} | excluded {len(drop)}")
print(f"  below 3 sessions: {n_lo_sess} | below 16 photos: {n_lo_phot} | both: {both}")
