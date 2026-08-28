# -*- coding: utf-8 -*-
"""
Build every image the deck needs, from artefacts already tracked in this repo.

Two kinds of asset:

1. Projection crops of figures/*.png. Each of those figures carries a baked-in
   title and, in most cases, an 8.5pt footnote. On a slide the title duplicates
   the slide title, and the footnote is roughly 2.5% of image height, which does
   not survive a projector. Both are cropped; the presenter speaks the footnote.
   The crop rows below were measured by scanning each PNG for horizontal bands
   of ink, so they track the figures rather than being eyeballed.

2. Two presentation-only variants (CMC and the open-set DIR/FAR curve), redrawn
   from analysis/artifacts/cv_report.json in the same visual language as
   analysis/plot_figures.py, with the annotation that carries the spoken
   punchline drawn onto the axes: rank-5 = 0.782, and the simulated-impostor
   0.230 beside the genuine 0.123. Nothing is hand-entered.

Plus one crop of Color_Bands1.jpg, the colony's own identification sheet.

Run:  python presentation/prepare_assets.py
Out:  presentation/assets/ (gitignored - regenerate rather than commit)
"""
from pathlib import Path
import json

from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "figures"
OUT = Path(__file__).resolve().parent / "assets"
OUT.mkdir(exist_ok=True)

# figure -> (crop above this row, crop below this row or None for full height)
CROPS = {
    "03_belly_detector_map":            (0, None),     # backup slide, title kept
    "06_leakage_random_vs_session":     (95, None),    # footnote kept: it is the control statement
    "08_accuracy_vs_sessions":          (95, None),   # footnote is the legend for the group-mean rules
    "09_per_individual_change":         (95, None),
    "11_evaluation_coverage":           (95, None),
    "12_loss_x_augmentation":           (95, 1380),   # keeps line 1 only: what the error bars are
    "13_colony_sessions_per_individual": (95, None),   # footnote is 9pt and does project
    "14_photos_vs_sessions":            (85, None),
}
MAX_W = 2200


def crop_figures():
    for name, (top, bot) in CROPS.items():
        src = FIGS / f"{name}.png"
        im = Image.open(src).convert("RGB")
        im = im.crop((0, top, im.width, bot if bot else im.height))
        if im.width > MAX_W:
            im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
        dst = OUT / (f"{name}.png" if top == 0 and bot is None else f"{name}_notitle.png")
        im.save(dst)
        print(f"  {dst.name:46s} {im.width}x{im.height}")


def band_sheet():
    """The upper half of the laminated colour-band sheet, excluding the hand."""
    im = Image.open(ROOT / "Color_Bands1.jpg")
    im = im.crop((360, 120, 2976, 2580))
    im = im.resize((1500, round(im.height * 1500 / im.width)), Image.LANCZOS)
    im.save(OUT / "band_sheet.jpg", quality=88)
    print(f"  {'band_sheet.jpg':46s} {im.width}x{im.height}")


# --------------------------------------------------------------------------
# presentation variants, same palette and chrome as analysis/plot_figures.py
BLUE, ORANGE, SIM = "#2a78d6", "#eb6834", "#9dbde8"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"],
    "font.size": 11, "axes.labelsize": 11,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.axisbelow": True, "figure.dpi": 220, "savefig.bbox": "tight",
})

BASE_LABEL = "softmax + basic (baseline)"
ARC_LABEL = "ArcFace + strong augmentation"


def tidy(ax, grid_axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.8)
    ax.grid(True, axis=grid_axis)
    ax.tick_params(length=3, width=0.8)


def slide_figures():
    cv = json.loads((ROOT / "analysis/artifacts/cv_report.json").read_text())
    BASE, ARC = cv["cv_softmax_basic"], cv["cv_arcface_strong"]

    # ---- CMC: the shortlist argument, with rank-5 marked ------------------
    k = np.arange(1, len(ARC["cmc"]) + 1)
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    ax.plot(k, BASE["cmc"], "-o", color=ORANGE, lw=2.2, ms=5.5, label=BASE_LABEL)
    ax.plot(k, ARC["cmc"], "-o", color=BLUE, lw=2.2, ms=5.5, label=ARC_LABEL)
    r1, r5 = ARC["cmc"][0], ARC["cmc"][4]
    ax.vlines(5, 0, r5, color=BLUE, lw=1.2, ls=(0, (4, 3)), zorder=2)
    ax.hlines(r5, 0.6, 5, color=BLUE, lw=1.2, ls=(0, (4, 3)), zorder=2)
    for x, v, dx, dy, va, txt in ((5, r5, 12, -6, "top", "five candidates"),
                                  (1, r1, 9, 4, "bottom", "one answer")):
        ax.scatter([x], [v], s=110, color=BLUE, edgecolors=SURFACE, linewidths=2, zorder=6)
        ax.annotate(f"{v:.3f}\n{txt}", (x, v), textcoords="offset points",
                    xytext=(dx, dy), fontsize=11.5, color=BLUE, fontweight="bold", va=va)
    ax.annotate(f"{BASE['cmc'][0]:.3f}", (1, BASE["cmc"][0]), textcoords="offset points",
                xytext=(8, -16), fontsize=10.5, color=ORANGE)
    ax.set_xticks(k)
    ax.set_xlim(0.6, len(k) + 0.9)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("rank k — number of candidates shown to the keeper")
    ax.set_ylabel("macro rank-k accuracy")
    ax.legend(frameon=False, loc="lower right", fontsize=10, labelcolor=INK2)
    tidy(ax)
    fig.savefig(OUT / "s07_cmc.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"  {'s07_cmc.png':46s} rank-1 {r1:.3f}  rank-5 {r5:.3f}")

    # ---- open set: genuine strangers against the simulated proxy ----------
    fig, ax = plt.subplots(figsize=(7.6, 4.1))
    for tag, colour in ((BASE, ORANGE), (ARC, BLUE)):
        c = tag["open_set"]["curve"]
        ax.plot(c["far"], c["dir"], "-", color=colour, lw=2.4)
    sim = ARC["open_set_simulated"]["curve"]
    ax.plot(sim["far"], sim["dir"], color=SIM, lw=2.0, ls=(0, (5, 3)))

    arc1 = ARC["open_set"]["at"]["DIR@FAR=1%"]
    sim1 = ARC["open_set_simulated"]["at"]["DIR@FAR=1%"]
    ax.scatter([sim1["far"]], [sim1["dir"]], s=130, color=SIM,
               edgecolors=SURFACE, linewidths=2, zorder=6)
    ax.annotate(f"{sim1['dir']:.3f}  simulated strangers\noverstates the real figure by 87%",
                xy=(sim1["far"], sim1["dir"]), xytext=(0.0045, 0.645), textcoords="data",
                fontsize=11.5, color="#5b83b8", va="center", ha="left",
                arrowprops=dict(arrowstyle="-", color=SIM, lw=1.2, shrinkA=2, shrinkB=7))
    ax.scatter([arc1["far"]], [arc1["dir"]], s=150, color=BLUE,
               edgecolors=SURFACE, linewidths=2, zorder=7)
    ax.annotate(f"{arc1['dir']:.3f}  real never-trained strangers",
                (arc1["far"], arc1["dir"]), textcoords="offset points", xytext=(20, -30),
                fontsize=13, color=BLUE, fontweight="bold", va="top",
                arrowprops=dict(arrowstyle="-", color=BLUE, lw=1.2, shrinkA=2, shrinkB=9))
    for name in ("DIR@FAR=5%", "DIR@FAR=10%"):
        pt = ARC["open_set"]["at"][name]
        ax.scatter([pt["far"]], [pt["dir"]], s=75, color=BLUE, alpha=0.85,
                   edgecolors=SURFACE, linewidths=1.6, zorder=5)
        ax.annotate(f"{pt['dir']:.3f}", (pt["far"], pt["dir"]),
                    textcoords="offset points", xytext=(5, 11), fontsize=10.5, color=BLUE)
    b1 = BASE["open_set"]["at"]["DIR@FAR=1%"]
    ax.scatter([b1["far"]], [b1["dir"]], s=75, color=ORANGE,
               edgecolors=SURFACE, linewidths=1.6, zorder=6)

    ax.text(0.1175, 0.385, ARC_LABEL, fontsize=11, color=BLUE,
            ha="right", va="center", fontweight="bold")
    ax.text(0.1175, 0.100, BASE_LABEL, fontsize=11, color=ORANGE, ha="right", va="center")

    ax.axhline(ARC["rank1"]["macro"], color=MUTED, lw=1.1, ls=(0, (2, 3)))
    ax.text(0.1175, ARC["rank1"]["macro"] + 0.012,
            f"closed-set rank-1 = {ARC['rank1']['macro']:.3f}   (no stranger may appear)",
            fontsize=10.5, color=MUTED, ha="right", va="bottom")
    ax.axvline(0.05, color=AXIS, lw=1, zorder=1)
    ax.text(0.0535, 0.475, "threshold 0.938 — shipped", fontsize=10.5,
            color=MUTED, ha="left", va="center")

    ax.set_xlim(0, 0.12)
    ax.set_ylim(0, 0.72)
    ax.set_xticks([0.0, 0.01, 0.05, 0.10])
    ax.set_xticklabels(["0", "1%", "5%", "10%"])
    ax.set_xlabel("false-accept rate on unenrolled birds")
    ax.set_ylabel("correctly identified and accepted")
    tidy(ax, grid_axis="both")
    fig.savefig(OUT / "s10_openset.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"  {'s10_openset.png':46s} real {arc1['dir']:.3f}  simulated {sim1['dir']:.3f}")


if __name__ == "__main__":
    print(f"writing to {OUT}")
    crop_figures()
    band_sheet()
    slide_figures()
