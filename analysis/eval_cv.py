# -*- coding: utf-8 -*-
"""
Aggregate session-wise K-fold CV results and compare configurations.

For each fold: the fold's images are the queries, every image outside the fold
is the gallery (exactly what that fold's model was trained on, which is also
what enrolment looks like in deployment). Predictions from all K rounds are
pooled, so every photo in the dataset contributes exactly one prediction made
by a model that never saw its capture session.

Accuracy is then computed per penguin over ALL of that penguin's photos and
averaged with equal weight (MACRO). Micro is not computed -- see the metric
policy in analysis/evaluate.py.

Comparing two configurations uses a PAIRED bootstrap: both were evaluated on
the identical set of photos, so each resample applies the same image indices to
both and the statistic is the DIFFERENCE in macro. That is far more sensitive
than checking whether two independent CIs overlap, which is the conservative
test that made the previous round of experiments inconclusive.

Run:
  D:/Anaconda/python.exe analysis/eval_cv.py cv_softmax_basic cv_arcface_strong
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))

from evaluate import embed, load_extractor          # noqa: E402

FOLDS_JSON = ROOT / "analysis" / "artifacts" / "cv_folds.json"
REPORT = ROOT / "analysis" / "artifacts" / "cv_report.json"
N_BOOTSTRAP = 2000
SEED = 0


def fold_split(manifest, classes, fold):
    """(gallery_paths, gallery_labels, query_paths, query_labels) for one round."""
    gp, gl, qp, ql = [], [], [], []
    for pen in classes:
        for gi, group in enumerate(manifest[pen]):
            if gi == fold:
                qp.extend(group)
                ql.extend([pen] * len(group))
            else:
                gp.extend(group)
                gl.extend([pen] * len(group))
    return gp, gl, qp, ql


def predict_fold(model, dev, gp, gl, qp):
    """Prototype and 1-NN predictions plus top-5 hit flags for one round."""
    G, Q = embed(model, dev, gp), embed(model, dev, qp)
    gl = np.array(gl)

    names = sorted(set(gl.tolist()))
    protos = np.stack([
        (lambda v: v / max(np.linalg.norm(v), 1e-10))(G[gl == n].mean(0))
        for n in names]).astype("float32")
    porder = np.argsort(-(Q @ protos.T), axis=1)
    pnames = np.array(names)

    order = np.argsort(-(Q @ G.T), axis=1)
    return {
        "proto_top1": pnames[porder[:, 0]].tolist(),
        "proto_top5": [pnames[porder[i, :5]].tolist() for i in range(len(qp))],
        "knn_top1": gl[order[:, 0]].tolist(),
        "knn_top5": [gl[order[i, :5]].tolist() for i in range(len(qp))],
    }


def run_config(tag, manifest, classes):
    """Pool predictions over all folds. Returns {path: {...}} keyed by image."""
    base = ROOT / "runs" / tag
    k = len(next(iter(manifest.values())))
    pooled = {}
    for fold in range(k):
        ckpt = base / f"fold{fold}" / "model.pt"
        if not ckpt.exists():
            raise FileNotFoundError(f"{ckpt} missing -- has {tag} finished training?")
        gp, gl, qp, ql = fold_split(manifest, classes, fold)
        model, dev, _ = load_extractor(ckpt)
        pred = predict_fold(model, dev, gp, gl, qp)
        for i, path in enumerate(qp):
            pooled[path] = {
                "true": ql[i],
                "proto_top1": pred["proto_top1"][i] == ql[i],
                "proto_top5": ql[i] in pred["proto_top5"][i],
                "knn_top1": pred["knn_top1"][i] == ql[i],
                "knn_top5": ql[i] in pred["knn_top5"][i],
                "pred": pred["proto_top1"][i],
            }
        print(f"  fold {fold}: {len(qp)} queries against {len(gp)} gallery imgs",
              flush=True)
    return pooled


def by_class(pooled, key, order):
    """Correctness arrays per penguin, in a fixed image order so two configs align."""
    out = defaultdict(list)
    for path in order:
        r = pooled[path]
        out[r["true"]].append(float(r[key]))
    return {k: np.asarray(v) for k, v in sorted(out.items())}


def macro_ci(arrays, rng, n_boot=N_BOOTSTRAP):
    point = float(np.mean([a.mean() for a in arrays]))
    boot = np.zeros(n_boot)
    for a in arrays:
        idx = rng.integers(0, len(a), size=(n_boot, len(a)))
        boot += a[idx].mean(axis=1)
    boot /= len(arrays)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"macro": round(point, 4), "ci95": [round(float(lo), 4), round(float(hi), 4)]}


def paired_diff(arrays_a, arrays_b, rng, n_boot=N_BOOTSTRAP):
    """Bootstrap the DIFFERENCE in macro, resampling the same images for both."""
    keys = list(arrays_a)
    point = float(np.mean([arrays_b[k].mean() - arrays_a[k].mean() for k in keys]))
    boot = np.zeros(n_boot)
    for k in keys:
        a, b = arrays_a[k], arrays_b[k]
        idx = rng.integers(0, len(a), size=(n_boot, len(a)))
        boot += b[idx].mean(axis=1) - a[idx].mean(axis=1)
    boot /= len(keys)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"diff": round(point, 4),
            "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "excludes_zero": bool(lo > 0 or hi < 0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tags", nargs="+", help="run tags under runs/, e.g. cv_arcface_strong")
    ap.add_argument("--out", default=str(REPORT))
    args = ap.parse_args()

    data = json.loads(FOLDS_JSON.read_text(encoding="utf-8"))
    manifest = data["folds"]
    classes = sorted(manifest)
    order = sorted(p for pen in classes for g in manifest[pen] for p in g)

    rng = np.random.default_rng(SEED)
    report, arrays = {}, {}
    for tag in args.tags:
        print(f"\nevaluating {tag} ...", flush=True)
        pooled = run_config(tag, manifest, classes)
        assert len(pooled) == len(order), f"{len(pooled)} predictions vs {len(order)} images"

        entry, arrays[tag] = {}, {}
        for key in ("proto_top1", "proto_top5", "knn_top1", "knn_top5"):
            arrays[tag][key] = by_class(pooled, key, order)
            entry[key] = macro_ci(list(arrays[tag][key].values()), rng)
        pc = arrays[tag]["proto_top1"]
        entry["per_class"] = {k: round(float(v.mean()), 4) for k, v in pc.items()}
        entry["n_images_per_class"] = {k: int(len(v)) for k, v in pc.items()}
        entry["never_correct"] = sorted(k for k, v in pc.items() if v.max() == 0)
        entry["n_images"] = len(order)
        report[tag] = entry

        print(f"\n=== {tag} ===   (MACRO, {len(order)} photos, "
              f"{len(pc)} penguins)")
        for key, label in [("proto_top1", "prototype top-1"),
                           ("proto_top5", "prototype top-5"),
                           ("knn_top1", "1-NN top-1"),
                           ("knn_top5", "1-NN top-5")]:
            d = entry[key]
            print(f"  {label:<18}{d['macro']:>7.3f}   "
                  f"[{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}]")
        nc = entry["never_correct"]
        print(f"  never recognised ({len(nc)}/{len(pc)}): "
              f"{', '.join(nc) if nc else 'none'}")

    if len(args.tags) == 2:
        a, b = args.tags
        print(f"\n=== paired comparison: {b} minus {a} ===")
        report["_comparison"] = {"baseline": a, "candidate": b}
        for key, label in [("proto_top1", "prototype top-1"),
                           ("proto_top5", "prototype top-5"),
                           ("knn_top1", "1-NN top-1")]:
            d = paired_diff(arrays[a][key], arrays[b][key], rng)
            verdict = "REAL (CI excludes 0)" if d["excludes_zero"] else "not distinguishable"
            print(f"  {label:<18}{d['diff']:>+7.3f}   "
                  f"[{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}]   {verdict}")
            report["_comparison"][key] = d

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
