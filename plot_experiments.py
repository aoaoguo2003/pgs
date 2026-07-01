# -*- coding: utf-8 -*-
"""
Generate experiment-record figures for the penguin ID project.
Reads the existing run logs and writes PNGs into figures/.
Run:  python plot_experiments.py
"""
import os
import json
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 130,
    "font.size": 11,
    "axes.grid": True,
    "grid.alpha": 0.3,
})


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def col(rows, key, cast=float):
    return [cast(r[key]) for r in rows]


# ------------------------------------------------------------------ #
# 1. Classifier training curves: exp1 (full body) vs exp2 (belly)
# ------------------------------------------------------------------ #
h1 = read_csv(os.path.join(ROOT, "runs/exp1_baseline/history.csv"))
h2 = read_csv(os.path.join(ROOT, "runs/exp2_belly_resnet18/history.csv"))

fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))

ax[0].plot(col(h1, "epoch"), col(h1, "val_accuracy"), "-o", ms=3,
           label="exp1 full-body val", color="#1f77b4")
ax[0].plot(col(h2, "epoch"), col(h2, "val_accuracy"), "-s", ms=3,
           label="exp2 belly-crop val", color="#d62728")
ax[0].axhline(0.95, ls="--", lw=1, color="#1f77b4", alpha=0.6)
ax[0].axhline(0.865, ls="--", lw=1, color="#d62728", alpha=0.6)
ax[0].set_title("Validation accuracy per epoch")
ax[0].set_xlabel("epoch"); ax[0].set_ylabel("val accuracy")
ax[0].set_ylim(0.2, 1.0); ax[0].legend()

ax[1].plot(col(h1, "epoch"), col(h1, "train_loss"), "-", label="exp1 train loss", color="#1f77b4")
ax[1].plot(col(h1, "epoch"), col(h1, "val_loss"), "--", label="exp1 val loss", color="#1f77b4", alpha=0.7)
ax[1].plot(col(h2, "epoch"), col(h2, "train_loss"), "-", label="exp2 train loss", color="#d62728")
ax[1].plot(col(h2, "epoch"), col(h2, "val_loss"), "--", label="exp2 val loss", color="#d62728", alpha=0.7)
ax[1].set_title("Train / val loss per epoch")
ax[1].set_xlabel("epoch"); ax[1].set_ylabel("loss"); ax[1].legend()

fig.suptitle("Classifier training curves — full body vs belly crop (ResNet18)", y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "01_classifier_training_curves.png"), bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ #
# 2. Final test-accuracy comparison bar
# ------------------------------------------------------------------ #
m1 = json.load(open(os.path.join(ROOT, "runs/exp1_baseline/final_metrics.json")))
m2 = json.load(open(os.path.join(ROOT, "runs/exp2_belly_resnet18/final_metrics.json")))

fig, ax = plt.subplots(figsize=(5.5, 4.5))
names = ["exp1\nfull body", "exp2\nbelly crop"]
vals = [m1["test_accuracy"], m2["test_accuracy"]]
bars = ax.bar(names, vals, color=["#1f77b4", "#d62728"], width=0.55)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.3f}",
            ha="center", va="bottom", fontweight="bold")
ax.set_ylim(0, 1.05); ax.set_ylabel("test accuracy")
ax.set_title("Final 44-class test accuracy")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "02_test_accuracy_comparison.png"), bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ #
# 3. Belly detector (YOLOv8s) mAP curves
# ------------------------------------------------------------------ #
d = read_csv(os.path.join(ROOT, "runs/detect/runs/belly_detector/exp1/results.csv"))
ep = col(d, "epoch")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(ep, col(d, "metrics/mAP50(B)"), "-", label="mAP@50", color="#2ca02c")
ax.plot(ep, col(d, "metrics/mAP50-95(B)"), "-", label="mAP@50-95", color="#ff7f0e")
ax.plot(ep, col(d, "metrics/precision(B)"), ":", label="precision", color="#7f7f7f", alpha=0.8)
ax.plot(ep, col(d, "metrics/recall(B)"), "--", label="recall", color="#9467bd", alpha=0.8)
ax.set_ylim(0, 1.02); ax.set_xlabel("epoch"); ax.set_ylabel("metric")
ax.set_title("Belly detector (YOLOv8s) — validation metrics per epoch")
ax.legend(loc="lower right")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "03_belly_detector_map.png"), bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ #
# 4. exp1 per-class test accuracy (sorted)
# ------------------------------------------------------------------ #
pc = read_csv(os.path.join(ROOT, "runs/exp1_baseline/per_class_test_metrics.csv"))
pc.sort(key=lambda r: float(r["accuracy"]))
cls = [r["class_name"] for r in pc]
acc = [float(r["accuracy"]) for r in pc]
sup = [int(r["support"]) for r in pc]
colors = ["#d62728" if a < 0.8 else ("#ff7f0e" if a < 1.0 else "#2ca02c") for a in acc]

fig, ax = plt.subplots(figsize=(9, 11))
y = np.arange(len(cls))
ax.barh(y, acc, color=colors)
ax.set_yticks(y)
ax.set_yticklabels([f"{c} (n={s})" for c, s in zip(cls, sup)], fontsize=8)
ax.set_xlim(0, 1.05); ax.set_xlabel("test accuracy")
ax.set_title("exp1 per-class test accuracy (green=1.0, orange=partial, red<0.8)")
for yi, a in zip(y, acc):
    ax.text(a + 0.01, yi, f"{a:.2f}", va="center", fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "04_exp1_per_class_accuracy.png"), bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ #
# 5. Dataset class-imbalance distribution (all 82, cutoff at selected)
# ------------------------------------------------------------------ #
rows = read_csv(os.path.join(ROOT, "penguin_image_count_summary.csv"))
rows.sort(key=lambda r: int(r["num_images"]), reverse=True)
counts = [int(r["num_images"]) for r in rows]
sel = [r["selected"].strip().lower() == "true" for r in rows]
x = np.arange(len(counts))
bar_colors = ["#1f77b4" if s else "#cccccc" for s in sel]

fig, ax = plt.subplots(figsize=(13, 4.5))
ax.bar(x, counts, color=bar_colors, width=0.9)
n_sel = sum(sel)
ax.axvline(n_sel - 0.5, ls="--", color="#d62728", lw=1.3)
ax.text(n_sel + 0.5, max(counts) * 0.7,
        f"cutoff: {n_sel} individuals kept (>=16 imgs)\n{len(counts)-n_sel} dropped",
        color="#d62728", fontsize=10)
ax.set_xlabel("individual (sorted by image count)")
ax.set_ylabel("num images")
ax.set_title("Per-individual image counts — blue = selected (trainable), grey = dropped")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "05_dataset_distribution.png"), bbox_inches="tight")
plt.close(fig)

print("Saved figures to:", FIG)
for f in sorted(os.listdir(FIG)):
    print("  -", f)
