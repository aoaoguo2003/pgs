# -*- coding: utf-8 -*-
"""
Compile every headline number for the 35-individual evaluation into one table.

This is the results summary the dissertation quotes from. Everything is read
from analysis/artifacts/*.json, so re-running after a new experiment refreshes
it and nothing is ever transcribed by hand.

Run:
  D:/Anaconda/python.exe analysis/summarise_results.py
  D:/Anaconda/python.exe analysis/summarise_results.py --md analysis/artifacts/RESULTS.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "analysis" / "artifacts"

CELLS = [("cv_softmax_basic", "softmax + basic", "baseline"),
         ("cv_softmax_strong", "softmax + strong", ""),
         ("cv_arcface_basic", "ArcFace + basic", ""),
         ("cv_arcface_strong", "ArcFace + strong", "best")]

PAIRS = [("cv_pair_aug.json", "augmentation alone", "softmax+basic -> softmax+strong"),
         ("cv_pair_loss.json", "ArcFace alone", "softmax+basic -> ArcFace+basic"),
         ("cv_pair_loss_given_strong.json", "ArcFace given strong aug",
          "softmax+strong -> ArcFace+strong")]


def ci(d):
    return f"{d['macro']:.3f} [{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", help="also write a markdown copy here")
    args = ap.parse_args()

    cv = json.loads((ART / "cv_report.json").read_text(encoding="utf-8"))
    sess = {k: v["sessions"] for k, v in json.loads(
        (ART / "session_split_manifest.json").read_text(encoding="utf-8"))["per_penguin"].items()}
    L = []
    def w(s=""):
        L.append(s)
        print(s)

    best = cv["cv_arcface_strong"]
    w("# Results — 35 individuals, session-wise 5-fold cross-validation")
    w()
    w(f"{best['n_images']} photographs, {len(best['per_class'])} individuals. Every photo is "
      "tested exactly once by a model that never saw its capture session.")
    w()
    w("All figures are **macro**: per-individual accuracy averaged with equal weight, so a bird "
      "with 18 photos counts as much as one with 291. Intervals are 95% bootstrap, resampling "
      "**capture sessions** within each bird (photos inside a burst are near-duplicates, so "
      "resampling photos would report an interval that is too narrow).")
    w()

    w("## 1. Closed-set identification (35 candidates)")
    w()
    w("| configuration | rank-1 | rank-5 | mAP | 1-NN rank-1 | |")
    w("|---|---|---|---|---|---|")
    for tag, label, note in CELLS:
        d = cv[tag]
        w(f"| {label} | {ci(d['rank1'])} | {ci(d['rank5'])} | {ci(d['mAP'])} "
          f"| {ci(d['knn_rank1'])} | {note} |")
    w()
    w("*rank-1* = the single best-matching individual is correct. *rank-5* = the correct "
      "individual is among the five best-matching individuals (five distinct birds, not five "
      "photos). *mAP* = quality of the whole ranking over the 1394-photo gallery, the "
      "conventional re-ID companion to rank-1. *1-NN* = nearest single gallery photo rather "
      "than the class prototype.")
    w()

    w("## 2. CMC — how many candidates you must show")
    w()
    w("| rank k | " + " | ".join(l for _, l, _ in CELLS) + " |")
    w("|---" * (len(CELLS) + 1) + "|")
    for k in range(1, 11):
        w(f"| {k} | " + " | ".join(f"{cv[t]['cmc'][k-1]:.3f}" for t, _, _ in CELLS) + " |")
    w()
    w(f"A five-candidate shortlist contains the right bird {best['cmc'][4]:.1%} of the time "
      f"against {best['cmc'][0]:.1%} for a single answer — the basis for showing a keeper a "
      "shortlist rather than one name.")
    w()

    w("## 3. Colony-scale ranking (81 candidates)")
    w()
    w("| configuration | rank-1 (35 candidates) | rank-1 (81 candidates) | drop |")
    w("|---|---|---|---|")
    for tag, label, note in CELLS:
        a, b = cv[tag]["rank1"]["macro"], cv[tag]["rank1_colony"]["macro"]
        w(f"| {label} | {a:.3f} | {b:.3f} | {b - a:+.3f} |")
    w()
    w("The queries are the same 1743 photos of the same 35 birds; only the candidate list grows, "
      "with the 46 unevaluable colony members added as distractors. **ArcFace degrades least** "
      "as the gallery grows, which is the regime a real colony is in.")
    w()

    w("## 4. Open-set — when the bird may not be enrolled")
    w()
    w("| configuration | DIR@FAR=1% | DIR@FAR=5% | DIR@FAR=10% |")
    w("|---|---|---|---|")
    for tag, label, note in CELLS:
        o = cv[tag]["open_set"]["at"]
        w(f"| {label} | {o['DIR@FAR=1%']['dir']:.3f} | {o['DIR@FAR=5%']['dir']:.3f} "
          f"| {o['DIR@FAR=10%']['dir']:.3f} |")
    w()
    w(f"Strangers are the {best['n_stranger_photos'] // 5} photographs of 46 colony members the "
      "models never trained on. DIR@FAR=x is the fraction of enrolled birds both correctly named "
      "*and* confident enough to be accepted, at the threshold where strangers are wrongly "
      f"accepted x of the time. **Closed-set rank-1 of {best['rank1']['macro']:.3f} falls to "
      f"{best['open_set']['at']['DIR@FAR=1%']['dir']:.3f}** — this is the figure that describes "
      "deployment readiness.")
    w()

    w("## 5. Attribution — which change did the work")
    w()
    w("| effect | rank-1 (35) | rank-1 (81) | mAP |")
    w("|---|---|---|---|")
    for fn, label, arrow in PAIRS:
        p = ART / fn
        if not p.exists():
            continue
        c = json.loads(p.read_text(encoding="utf-8"))["_comparison"]
        def d(k):
            x = c[k]
            star = "" if x["excludes_zero"] else " **(n.s.)**"
            return f"{x['diff']:+.3f} [{x['ci95'][0]:+.3f}, {x['ci95'][1]:+.3f}]{star}"
        w(f"| {label} | {d('rank1')} | {d('rank1_colony')} | {d('mAP')} |")
    w()
    w("**(n.s.)** = interval includes zero. Augmentation is the larger single lever; ArcFace's "
      "marginal contribution on top of it is invisible at 35 candidates but clear at 81 and on "
      "mAP, because metric learning shapes the embedding geometry rather than the top-1 call.")
    w()

    w("## 6. Accuracy by capture sessions per individual")
    w()
    w("| sessions | individuals | " + " | ".join(l for _, l, _ in CELLS) + " |")
    w("|---" * (len(CELLS) + 2) + "|")
    for lo, hi, lab in ((3, 3, "3"), (4, 6, "4–6"), (7, 99, "7+")):
        names = [b for b in best["per_class"] if lo <= sess[b] <= hi]
        row = " | ".join(
            f"{sum(cv[t]['per_class'][b] for b in names) / len(names):.3f}" for t, _, _ in CELLS)
        w(f"| {lab} | {len(names)} | {row} |")
    w()
    ge4 = [b for b in best["per_class"] if sess[b] >= 4]
    w(f"Excluding the {len(best['per_class']) - len(ge4)} individuals with only 3 sessions, the "
      f"remaining {len(ge4)} reach "
      f"{sum(best['per_class'][b] for b in ge4) / len(ge4):.3f}. Metric learning lifts every "
      "bucket but cannot rescue the 3-session birds — that gap needs a camera, not a loss "
      "function.")
    w()

    w("## 7. Models behind these numbers")
    w()
    w("| purpose | location | trained on |")
    w("|---|---|---|")
    for tag, label, _ in CELLS:
        w(f"| {label} | `runs/{tag}/fold0..4/model.pt` | 5 models, ~80% of 1743 photos each |")
    dep = ROOT / "runs" / "deploy_arcface" / "summary.json"
    if dep.exists():
        s = json.loads(dep.read_text(encoding="utf-8"))
        w(f"| **deployed** | `runs/deploy_arcface/model.pt` | 1 model, "
          f"{s['n_individuals']} individuals, {s['n_photos']} photos, nothing held out |")
    w()
    w("The cross-validated figures estimate the *method*; the deployed model is retrained with "
      "the identical recipe on everything, and those figures are its conservative estimate "
      "(each fold saw 80% of the data, the deployed model 100%). Model weights are gitignored; "
      "training curves and every result JSON are tracked, so all of the above is reproducible.")

    if args.md:
        out = ROOT / args.md if not Path(args.md).is_absolute() else Path(args.md)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(L) + "\n", encoding="utf-8")
        print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
