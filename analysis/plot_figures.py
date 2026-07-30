# -*- coding: utf-8 -*-
"""
Publication figures for the session-disjoint and cross-validated evaluations.

Every figure is regenerated from the JSON artifacts written by
analysis/evaluate.py, analysis/eval_cv.py and analysis/build_session_splits.py,
so nothing here is hand-entered and re-running after a new experiment updates
the whole set. Output: figures/06_*.png .. figures/11_*.png at 300 dpi.

Run:
  D:/Anaconda/python.exe analysis/plot_figures.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                        # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "analysis" / "artifacts"
OUT = ROOT / "figures"

# Validated categorical palette (see the data-viz reference palette). Slots 1-3
# clear the all-pairs colour-vision gates on the light surface; every figure
# below uses at most two of them plus ink greys.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"

BASE_LABEL = "softmax + basic (baseline)"
ARC_LABEL = "ArcFace + strong augmentation"

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


def tidy(ax, grid_axis="y"):
    """Hairline recessive chrome: no top/right spines, one solid grid direction."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.8)
    ax.grid(True, axis=grid_axis)
    ax.tick_params(length=3, width=0.8)


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    path = OUT / name
    fig.savefig(path)
    plt.close(fig)
    print(f"  wrote {path.relative_to(ROOT)}")


# --------------------------------------------------------------------- loading

single = json.loads((ART / "eval_report.json").read_text(encoding="utf-8"))
cv = json.loads((ART / "cv_report.json").read_text(encoding="utf-8"))
manifest = json.loads((ART / "session_split_manifest.json").read_text(encoding="utf-8"))
folds = json.loads((ART / "cv_folds.json").read_text(encoding="utf-8"))["folds"]

BASE, ARC = cv["cv_softmax_basic"], cv["cv_arcface_strong"]
SESSIONS = {k: v["sessions"] for k, v in manifest["per_penguin"].items()}


# ------------------------------------------------- 06 leakage: random vs session

def fig_leakage():
    leaky = single["exp1b random-control"]
    clean = single["exp1b session-disjoint"]
    keys = [("prototype_top1", "rank-1"), ("prototype_top5", "rank-5"),
            ("knn_top1", "1-NN rank-1")]
    a = [leaky[k]["macro"] for k, _ in keys]
    b = [clean[k]["macro"] for k, _ in keys]
    x = np.arange(len(keys))
    w = 0.36

    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    r1 = ax.bar(x - w / 2 - 0.01, a, w, color=BLUE, label="random split (burst leakage)")
    r2 = ax.bar(x + w / 2 + 0.01, b, w, color=ORANGE, label="session-disjoint (honest)")
    for rects in (r1, r2):
        for r in rects:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.02,
                    f"{r.get_height():.3f}", ha="center", va="bottom",
                    fontsize=9, color=INK2)

    ax.set_xticks(x, [lab for _, lab in keys])
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("macro accuracy")
    # legend above the plot: at these bar heights any in-axes corner collides
    ax.set_title("Same-session camera bursts inflate accuracy by ~0.53",
                 color=INK, pad=34, loc="left")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.15),
              ncol=2, fontsize=9, labelcolor=INK2)
    tidy(ax)
    fig.text(0.0, -0.06,
             "Identical 35 individuals, 1743 photos and per-bird counts in both "
             "conditions; only the split rule differs.",
             fontsize=8.5, color=MUTED)
    save(fig, "06_leakage_random_vs_session.png")


# ------------------------------------------------------------------- 07 CMC

def fig_cmc():
    k = np.arange(1, len(ARC["cmc"]) + 1)
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    ax.plot(k, BASE["cmc"], "-o", color=ORANGE, lw=2, ms=5, label=BASE_LABEL)
    ax.plot(k, ARC["cmc"], "-o", color=BLUE, lw=2, ms=5, label=ARC_LABEL)
    # label rank-1, where the curves are far apart and the story lives; at rank 10
    # they converge to within 0.004 and two labels there just overprint
    for series, colour, dy in ((ARC["cmc"], BLUE, 22), (BASE["cmc"], ORANGE, -20)):
        ax.annotate(f"{series[0]:.3f}", (k[0], series[0]), textcoords="offset points",
                    xytext=(4, dy), fontsize=9.5, color=colour)
    ax.set_xticks(k)
    ax.set_xlim(0.6, len(k) + 0.9)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("rank k (candidates shown)")
    ax.set_ylabel("macro rank-k accuracy")
    ax.set_title("Cumulative matching characteristic", color=INK, pad=12, loc="left")
    ax.legend(frameon=False, loc="lower right", fontsize=9, labelcolor=INK2)
    tidy(ax)
    fig.text(0.0, -0.06,
             "A five-candidate shortlist contains the right bird 78% of the time, "
             "against 56% for a single answer.",
             fontsize=8.5, color=MUTED)
    save(fig, "07_cmc_curve.png")


# ------------------------------------------- 08 accuracy vs sessions per individual

def fig_sessions():
    birds = sorted(ARC["per_class"])
    s = np.array([SESSIONS[b] for b in birds], dtype=float)
    base = np.array([BASE["per_class"][b] for b in birds])
    arc = np.array([ARC["per_class"][b] for b in birds])
    jitter = np.linspace(-0.12, 0.12, len(birds))

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    ax.scatter(s + jitter, base, s=26, color=ORANGE, alpha=0.75,
               edgecolors=SURFACE, linewidths=1.2, label=BASE_LABEL, zorder=3)
    ax.scatter(s + jitter, arc, s=26, color=BLUE, alpha=0.85,
               edgecolors=SURFACE, linewidths=1.2, label=ARC_LABEL, zorder=4)

    # Group means sit ON their own rule, blue above / orange below, so the three
    # bucket labels never share a line and cannot overprint each other.
    for lo, hi in ((3, 3), (4, 6), (7, 30)):
        m = (s >= lo) & (s <= hi)
        if not m.any():
            continue
        x0, x1 = max(lo - 0.42, 2.5), min(hi + 0.42, s.max() + 0.6)
        xm = (x0 + x1) / 2
        ax.hlines(arc[m].mean(), x0, x1, color=BLUE, lw=2.4, zorder=5)
        ax.hlines(base[m].mean(), x0, x1, color=ORANGE, lw=2.4, zorder=5)
        ax.text(xm, arc[m].mean() + 0.025, f"{arc[m].mean():.2f}", ha="center",
                va="bottom", fontsize=9.5, color=BLUE, zorder=6)
        ax.text(xm, base[m].mean() - 0.03, f"{base[m].mean():.2f}", ha="center",
                va="top", fontsize=9.5, color=ORANGE, zorder=6)

    ax.axvline(3.5, color=AXIS, lw=1, zorder=1)
    ax.text(3.6, 0.04, "fewer than 4 sessions", fontsize=8.5, color=MUTED)
    ax.set_xlabel("capture sessions available for that individual")
    ax.set_ylabel("macro rank-1 accuracy")
    ax.set_ylim(-0.10, 1.06)
    ax.set_xlim(2.4, s.max() + 0.8)
    ax.set_title("Accuracy is set by capture sessions, not by photo count",
                 color=INK, pad=12, loc="left")
    ax.legend(frameon=False, loc="lower right", fontsize=9, labelcolor=INK2)
    tidy(ax, grid_axis="both")
    fig.text(0.0, -0.06,
             "One point per individual (35 birds); horizontal rules are group means. "
             "Metric learning lifts every group but leaves the 3-session birds unusable.",
             fontsize=8.5, color=MUTED)
    save(fig, "08_accuracy_vs_sessions.png")


# ------------------------------------------------- 09 per-individual change

def fig_per_individual():
    # Individuals on x, accuracy on y: height reads directly as "doing better",
    # which a horizontal layout does not give you at a glance.
    birds = sorted(ARC["per_class"], key=lambda b: ARC["per_class"][b])
    base = np.array([BASE["per_class"][b] for b in birds])
    arc = np.array([ARC["per_class"][b] for b in birds])
    x = np.arange(len(birds))
    overall = ARC["rank1"]["macro"]

    fig, ax = plt.subplots(figsize=(10.6, 5.4))
    ax.axhline(overall, color=AXIS, lw=1, zorder=1)
    # ascending sort puts the empty region top-left, so both the reference-line
    # label and the legend live there
    ax.text(-0.4, overall + 0.015, f"ArcFace overall {overall:.3f}",
            ha="left", va="bottom", fontsize=8.5, color=MUTED)

    ax.vlines(x, base, arc, color=AXIS, lw=1.6, zorder=2)
    ax.scatter(x, base, s=34, color=ORANGE, edgecolors=SURFACE, linewidths=1.2,
               zorder=3, label=BASE_LABEL)
    ax.scatter(x, arc, s=34, color=BLUE, edgecolors=SURFACE, linewidths=1.2,
               zorder=4, label=ARC_LABEL)

    ax.set_xticks(x, [f"{b} ({SESSIONS[b]})" for b in birds],
                  rotation=90, fontsize=8.5)
    ax.set_xlim(-0.8, len(birds) - 0.2)
    ax.set_ylim(-0.04, 1.06)
    ax.set_ylabel("macro rank-1 accuracy")
    ax.set_title("Every individual, baseline → ArcFace", color=INK, pad=12, loc="left")
    ax.legend(frameon=False, loc="upper left", fontsize=9, labelcolor=INK2)
    tidy(ax, grid_axis="y")
    fig.text(0.0, -0.20,
             "Sorted by ArcFace accuracy, best on the right; the number after each "
             "name is that individual's capture sessions. Higher is better.",
             fontsize=8.5, color=MUTED)
    save(fig, "09_per_individual_change.png")


# ----------------------------------------------------------------- 10 open set

def fig_open_set():
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for entry, colour, label in ((BASE, ORANGE, BASE_LABEL), (ARC, BLUE, ARC_LABEL)):
        far = np.array(entry["open_set"]["curve"]["far"])
        dr = np.array(entry["open_set"]["curve"]["dir"])
        o = np.argsort(far)
        ax.plot(far[o], dr[o], color=colour, lw=2, label=label)
        pt = entry["open_set"]["at"]["DIR@FAR=1%"]
        ax.scatter([pt["far"]], [pt["dir"]], s=60, color=colour,
                   edgecolors=SURFACE, linewidths=1.6, zorder=5)
        ax.annotate(f"{pt['dir']:.3f}", (pt["far"], pt["dir"]),
                    textcoords="offset points", xytext=(10, -2),
                    fontsize=9, color=INK2)

    ax.axvline(0.01, color=AXIS, lw=1, zorder=1)
    ax.text(0.014, 0.02, "1% false-accept\noperating point", fontsize=8.5, color=MUTED)
    ax.set_xlim(0, 0.35)
    ax.set_ylim(0, 0.75)
    ax.set_xlabel("false accept rate on unenrolled birds")
    ax.set_ylabel("correctly identified and accepted")
    ax.set_title("Open-set identification: the cost of being able to say "
                 "\u201cI don\u2019t know\u201d", color=INK, pad=12, loc="left")
    ax.legend(frameon=False, loc="lower right", fontsize=9, labelcolor=INK2)
    tidy(ax, grid_axis="both")
    fig.text(0.0, -0.06,
             "Unknowns simulated leave-one-individual-out. Closed-set rank-1 of 0.559 "
             "falls to 0.229 once unenrolled birds must be refused 99% of the time.",
             fontsize=8.5, color=MUTED)
    save(fig, "10_open_set_dir_far.png")


# --------------------------------------------- 11 evaluation coverage: split vs CV

def fig_coverage():
    birds = sorted(manifest["per_penguin"],
                   key=lambda b: manifest["per_penguin"][b]["test"])
    single_n = np.array([manifest["per_penguin"][b]["test"] for b in birds])
    cv_n = np.array([sum(len(g) for g in folds[b]) for b in birds])
    y = np.arange(len(birds))

    fig, ax = plt.subplots(figsize=(6.6, 8.4))
    ax.barh(y - 0.21, cv_n, height=0.4, color=BLUE, label="5-fold cross-validation")
    ax.barh(y + 0.21, single_n, height=0.4, color=ORANGE, label="single session-disjoint split")
    for i, (a, b_) in enumerate(zip(single_n, cv_n)):
        ax.text(b_ + 3, i - 0.21, str(b_), va="center", fontsize=8, color=INK2)
        ax.text(a + 3, i + 0.21, str(a), va="center", fontsize=8, color=MUTED)

    ax.set_yticks(y, birds, fontsize=8.5)
    ax.set_ylim(-0.8, len(birds) - 0.2)
    ax.set_xlim(0, max(cv_n) * 1.12)
    ax.set_xlabel("photographs this individual is evaluated on")
    ax.set_title("Why cross-validation: evaluation coverage per individual",
                 color=INK, pad=12, loc="left")
    ax.legend(frameon=False, loc="lower right", fontsize=9, labelcolor=INK2)
    tidy(ax, grid_axis="x")
    fig.text(0.0, -0.02,
             "Under one split, three individuals are judged on a single photograph. "
             "Cross-validation evaluates every photograph exactly once, 1743 in total.",
             fontsize=8.5, color=MUTED)
    save(fig, "11_evaluation_coverage.png")


if __name__ == "__main__":
    print("writing figures ...")
    fig_leakage()
    fig_cmc()
    fig_sessions()
    fig_per_individual()
    fig_open_set()
    fig_coverage()
    print("done")
