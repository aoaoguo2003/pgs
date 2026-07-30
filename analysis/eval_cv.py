# -*- coding: utf-8 -*-
"""
Aggregate session-wise K-fold CV results and compare configurations.

For each fold: the fold's images are the queries, every image outside the fold
is the gallery (exactly what that fold's model was trained on, which is also
what enrolment looks like in deployment). Predictions from all K rounds are
pooled, so every photo in the dataset contributes exactly one prediction made
by a model that never saw its capture session.

Every statistic is MACRO -- computed per penguin over all of that penguin's
photos, then averaged with equal weight. Micro is not computed anywhere; see
the metric policy in analysis/evaluate.py.

Metrics reported
  rank-1 / CMC    closed-set identification; CMC is rank-k for k = 1..10
  mAP             ranking quality over the image gallery, the conventional
                  re-ID companion to rank-1. Computed against the image
                  gallery, not prototypes: with one correct prototype per query
                  mAP would degenerate to mean reciprocal rank.
  DIR@FAR         open-set identification. Unknowns are simulated leave-one-
                  penguin-out: a query's impostor score is its best prototype
                  similarity with its OWN identity removed from the gallery.
                  DIR@FAR=x is the fraction of queries both correctly named and
                  confident enough, at the threshold where unenrolled birds are
                  wrongly accepted x of the time. Only 35 of the colony's 81
                  birds are enrolled, so this is the metric that matters in use.

Comparing two configurations uses a PAIRED bootstrap: both were evaluated on
the identical set of photos, so each resample applies the same image indices to
both and the statistic is the DIFFERENCE in macro. That is far more sensitive
than checking whether two independent CIs overlap.

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
CMC_MAX = 10
FAR_TARGETS = (0.01, 0.05, 0.10)
SEED = 0


# ----------------------------------------------------------------- per-fold work

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


def average_precision(relevant: np.ndarray) -> float:
    """AP for one query given gallery relevance sorted by descending similarity."""
    hits = np.flatnonzero(relevant)
    if hits.size == 0:
        return 0.0
    precision_at_hit = (np.arange(hits.size) + 1) / (hits + 1)
    return float(precision_at_hit.mean())


def predict_fold(model, dev, gp, gl, qp, ql):
    """Everything downstream needs, per query, for one CV round."""
    G, Q = embed(model, dev, gp), embed(model, dev, qp)
    gl_arr, ql_arr = np.array(gl), np.array(ql)

    names = np.array(sorted(set(gl)))
    protos = np.stack([
        (lambda v: v / max(np.linalg.norm(v), 1e-10))(G[gl_arr == n].mean(0))
        for n in names]).astype("float32")

    psims = Q @ protos.T                       # queries x identities
    isims = Q @ G.T                            # queries x gallery images
    true_col = np.array([int(np.flatnonzero(names == t)[0]) for t in ql_arr])

    # closed-set rank of the true identity among prototypes (1 = best)
    order = np.argsort(-psims, axis=1)
    rank = np.argmax(order == true_col[:, None], axis=1) + 1

    # open-set: best score overall, and best score once the true identity is hidden
    best_score = psims.max(axis=1)
    hidden = psims.copy()
    hidden[np.arange(len(ql_arr)), true_col] = -np.inf
    impostor_score = hidden.max(axis=1)

    img_order = np.argsort(-isims, axis=1)
    out = []
    for i in range(len(qp)):
        rel = gl_arr[img_order[i]] == ql_arr[i]
        out.append({
            "true": ql_arr[i],
            "rank": int(rank[i]),
            "ap": average_precision(rel),
            "knn_rank1": bool(rel[0]),
            "score": float(best_score[i]),
            "impostor": float(impostor_score[i]),
        })
    return out


def run_config(tag, manifest, classes):
    base = ROOT / "runs" / tag
    k = len(next(iter(manifest.values())))
    pooled = {}
    for fold in range(k):
        ckpt = base / f"fold{fold}" / "model.pt"
        if not ckpt.exists():
            raise FileNotFoundError(f"{ckpt} missing -- has {tag} finished training?")
        gp, gl, qp, ql = fold_split(manifest, classes, fold)
        model, dev, _ = load_extractor(ckpt)
        for path, rec in zip(qp, predict_fold(model, dev, gp, gl, qp, ql)):
            pooled[path] = rec
        print(f"  fold {fold}: {len(qp)} queries against {len(gp)} gallery imgs",
              flush=True)
    return pooled


# --------------------------------------------------------------------- aggregate

def group_by_class(pooled, order, fn):
    out = defaultdict(list)
    for path in order:
        rec = pooled[path]
        out[rec["true"]].append(float(fn(rec)))
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


def paired_diff(a_arrays, b_arrays, rng, n_boot=N_BOOTSTRAP):
    keys = list(a_arrays)
    point = float(np.mean([b_arrays[k].mean() - a_arrays[k].mean() for k in keys]))
    boot = np.zeros(n_boot)
    for k in keys:
        a, b = a_arrays[k], b_arrays[k]
        idx = rng.integers(0, len(a), size=(n_boot, len(a)))
        boot += b[idx].mean(axis=1) - a[idx].mean(axis=1)
    boot /= len(keys)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"diff": round(point, 4),
            "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "excludes_zero": bool(lo > 0 or hi < 0)}


def open_set_curve(pooled, order):
    """Macro DIR/FAR sweep. Both rates are averaged per penguin, not per photo."""
    per_class = defaultdict(list)
    for path in order:
        r = pooled[path]
        per_class[r["true"]].append((r["score"], r["rank"] == 1, r["impostor"]))

    thresholds = np.unique(np.concatenate([
        np.array([v[0] for vals in per_class.values() for v in vals]),
        np.array([v[2] for vals in per_class.values() for v in vals])]))
    thresholds = np.linspace(thresholds.min(), thresholds.max(), 400)

    dir_rates, far_rates = [], []
    packed = [(np.array([v[0] for v in vals]),
               np.array([v[1] for v in vals], dtype=bool),
               np.array([v[2] for v in vals])) for vals in per_class.values()]
    for t in thresholds:
        dir_rates.append(np.mean([np.mean(correct & (score >= t))
                                  for score, correct, _ in packed]))
        far_rates.append(np.mean([np.mean(imp >= t) for _, _, imp in packed]))

    dir_rates, far_rates = np.array(dir_rates), np.array(far_rates)
    at = {}
    for target in FAR_TARGETS:
        ok = np.flatnonzero(far_rates <= target)
        if ok.size:
            j = ok[int(np.argmax(dir_rates[ok]))]
            at[f"DIR@FAR={target:.0%}"] = {"dir": round(float(dir_rates[j]), 4),
                                           "far": round(float(far_rates[j]), 4),
                                           "threshold": round(float(thresholds[j]), 4)}
        else:
            at[f"DIR@FAR={target:.0%}"] = None
    return {"at": at,
            "curve": {"threshold": [round(float(v), 4) for v in thresholds],
                      "dir": [round(float(v), 4) for v in dir_rates],
                      "far": [round(float(v), 4) for v in far_rates]}}


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
        metrics = {"rank1": lambda r: r["rank"] == 1,
                   "rank5": lambda r: r["rank"] <= 5,
                   "mAP": lambda r: r["ap"],
                   "knn_rank1": lambda r: r["knn_rank1"]}
        for key, fn in metrics.items():
            arrays[tag][key] = group_by_class(pooled, order, fn)
            entry[key] = macro_ci(list(arrays[tag][key].values()), rng)

        entry["cmc"] = [round(float(np.mean([
            np.mean(np.asarray(v) <= k)
            for v in group_by_class(pooled, order, lambda r: r["rank"]).values()])), 4)
            for k in range(1, CMC_MAX + 1)]
        entry["open_set"] = open_set_curve(pooled, order)

        pc = arrays[tag]["rank1"]
        entry["per_class"] = {k: round(float(v.mean()), 4) for k, v in pc.items()}
        entry["n_images_per_class"] = {k: int(len(v)) for k, v in pc.items()}
        entry["never_correct"] = sorted(k for k, v in pc.items() if v.max() == 0)
        entry["n_images"] = len(order)
        report[tag] = entry

        print(f"\n=== {tag} ===   (MACRO, {len(order)} photos, {len(pc)} penguins)")
        for key, label in [("rank1", "rank-1"), ("rank5", "rank-5"),
                           ("mAP", "mAP"), ("knn_rank1", "1-NN rank-1")]:
            d = entry[key]
            print(f"  {label:<14}{d['macro']:>7.3f}   [{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}]")
        for name, v in entry["open_set"]["at"].items():
            print(f"  {name:<14}{v['dir']:>7.3f}   (threshold {v['threshold']:.3f})"
                  if v else f"  {name:<14}      -")
        nc = entry["never_correct"]
        print(f"  never recognised ({len(nc)}/{len(pc)}): {', '.join(nc) if nc else 'none'}")

    if len(args.tags) == 2:
        a, b = args.tags
        print(f"\n=== paired comparison: {b} minus {a} ===")
        report["_comparison"] = {"baseline": a, "candidate": b}
        for key, label in [("rank1", "rank-1"), ("rank5", "rank-5"),
                           ("mAP", "mAP"), ("knn_rank1", "1-NN rank-1")]:
            d = paired_diff(arrays[a][key], arrays[b][key], rng)
            verdict = "REAL (CI excludes 0)" if d["excludes_zero"] else "not distinguishable"
            print(f"  {label:<14}{d['diff']:>+7.3f}   "
                  f"[{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}]   {verdict}")
            report["_comparison"][key] = d

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
