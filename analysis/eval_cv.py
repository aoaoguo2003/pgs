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


def collect_strangers(enrolled: set, src="penguins_data", min_photos=1):
    """Colony members absent from the folds -- genuine never-trained unknowns.

    These are the honest impostors. The simulated impostor used previously (hide
    the query's own column, take the next-best prototype) is far too easy: that
    bird WAS in the model's training set and was explicitly pushed away from
    every other identity, so its runner-up score understates how close a real
    stranger sits.
    """
    out = {}
    for d in sorted(p for p in (ROOT / src).iterdir() if p.is_dir()):
        if d.name in enrolled:
            continue
        imgs = [str(f.relative_to(ROOT)) for f in sorted(d.iterdir())
                if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}]
        if len(imgs) >= min_photos:
            out[d.name] = imgs
    return out


def prototypes(G, labels):
    names = np.array(sorted(set(labels.tolist())))
    P = np.stack([
        (lambda v: v / max(np.linalg.norm(v), 1e-10))(G[labels == n].mean(0))
        for n in names]).astype("float32")
    return names, P


def predict_fold(model, dev, gp, gl, qp, ql, strangers=None):
    """Everything downstream needs, per query, for one CV round."""
    G, Q = embed(model, dev, gp), embed(model, dev, qp)
    gl_arr, ql_arr = np.array(gl), np.array(ql)

    names, protos = prototypes(G, gl_arr)

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

    # Colony-scale arm: rank the same queries against ALL 81 identities, not just
    # the 35 evaluable ones. In use a keeper photographs any bird in the colony,
    # so a 35-way ranking is an optimistic framing of the real problem.
    rank81 = None
    stranger_scores = []
    if strangers:
        s_names, s_paths = zip(*sorted(strangers.items()))
        flat = [p for ps in s_paths for p in ps]
        owner = np.array([n for n, ps in zip(s_names, s_paths) for _ in ps])
        S = embed(model, dev, flat)
        _, s_protos = prototypes(S, owner)
        # honest impostor score: a stranger's best similarity to the ENROLLED gallery
        stranger_scores = (S @ protos.T).max(axis=1).tolist()

        all_names = np.concatenate([names, np.array(sorted(strangers))])
        all_protos = np.concatenate([protos, s_protos], axis=0)
        asims = Q @ all_protos.T
        acol = np.array([int(np.flatnonzero(all_names == t)[0]) for t in ql_arr])
        aorder = np.argsort(-asims, axis=1)
        rank81 = (np.argmax(aorder == acol[:, None], axis=1) + 1).tolist()

    img_order = np.argsort(-isims, axis=1)
    out = []
    for i in range(len(qp)):
        rel = gl_arr[img_order[i]] == ql_arr[i]
        out.append({
            "true": ql_arr[i],
            "rank": int(rank[i]),
            "rank_colony": int(rank81[i]) if rank81 is not None else None,
            "ap": average_precision(rel),
            "knn_rank1": bool(rel[0]),
            "score": float(best_score[i]),
            "impostor": float(impostor_score[i]),
        })
    return out, stranger_scores


def run_config(tag, manifest, classes, strangers=None):
    base = ROOT / "runs" / tag
    k = len(next(iter(manifest.values())))
    pooled, stranger_by_fold = {}, []
    for fold in range(k):
        ckpt = base / f"fold{fold}" / "model.pt"
        if not ckpt.exists():
            raise FileNotFoundError(f"{ckpt} missing -- has {tag} finished training?")
        gp, gl, qp, ql = fold_split(manifest, classes, fold)
        model, dev, _ = load_extractor(ckpt)
        recs, s_scores = predict_fold(model, dev, gp, gl, qp, ql, strangers)
        for path, rec in zip(qp, recs):
            pooled[path] = rec
        stranger_by_fold.append(s_scores)
        print(f"  fold {fold}: {len(qp)} queries vs {len(gp)} gallery imgs"
              + (f", {len(s_scores)} stranger photos" if s_scores else ""), flush=True)
    return pooled, stranger_by_fold


# --------------------------------------------------------------------- aggregate

def group_by_class(pooled, order, fn):
    out = defaultdict(list)
    for path in order:
        rec = pooled[path]
        out[rec["true"]].append(float(fn(rec)))
    return {k: np.asarray(v) for k, v in sorted(out.items())}


def group_by_class_session(pooled, order, fn, session_of):
    """{bird: [array_of_outcomes_per_session, ...]} -- the cluster bootstrap unit."""
    nested = defaultdict(lambda: defaultdict(list))
    for path in order:
        rec = pooled[path]
        nested[rec["true"]][session_of[path]].append(float(fn(rec)))
    return {b: [np.asarray(v) for v in sess.values()]
            for b, sess in sorted(nested.items())}


def _cluster_draw(clusters, rng, n_boot):
    """Bootstrap a per-bird mean by resampling SESSIONS, not photos.

    Photos inside one burst are near-duplicates, so resampling photos treats
    correlated samples as independent and returns an interval that is too narrow.
    Each draw picks len(clusters) sessions with replacement and averages the
    photos inside the drawn sessions -- the standard cluster bootstrap.
    """
    sums = np.array([c.sum() for c in clusters], dtype=np.float64)
    lens = np.array([len(c) for c in clusters], dtype=np.float64)
    idx = rng.integers(0, len(clusters), size=(n_boot, len(clusters)))
    return sums[idx].sum(axis=1) / np.maximum(lens[idx].sum(axis=1), 1e-9)


def macro_ci(by_bird_clusters, rng, n_boot=N_BOOTSTRAP):
    """by_bird_clusters: {bird: [array_per_session, ...]}"""
    point = float(np.mean([
        np.concatenate(cs).mean() for cs in by_bird_clusters.values()]))
    boot = np.zeros(n_boot)
    for cs in by_bird_clusters.values():
        boot += _cluster_draw(cs, rng, n_boot)
    boot /= len(by_bird_clusters)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"macro": round(point, 4), "ci95": [round(float(lo), 4), round(float(hi), 4)]}


def paired_diff(a_clusters, b_clusters, rng, n_boot=N_BOOTSTRAP):
    """Paired cluster bootstrap: the SAME resampled sessions are applied to both."""
    keys = list(a_clusters)
    point = float(np.mean([
        np.concatenate(b_clusters[k]).mean() - np.concatenate(a_clusters[k]).mean()
        for k in keys]))
    boot = np.zeros(n_boot)
    for k in keys:
        ca, cb = a_clusters[k], b_clusters[k]
        sa = np.array([c.sum() for c in ca]); la = np.array([len(c) for c in ca], dtype=float)
        sb = np.array([c.sum() for c in cb]); lb = np.array([len(c) for c in cb], dtype=float)
        idx = rng.integers(0, len(ca), size=(n_boot, len(ca)))
        boot += (sb[idx].sum(axis=1) / np.maximum(lb[idx].sum(axis=1), 1e-9)
                 - sa[idx].sum(axis=1) / np.maximum(la[idx].sum(axis=1), 1e-9))
    boot /= len(keys)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"diff": round(point, 4),
            "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "excludes_zero": bool(lo > 0 or hi < 0)}


def open_set_curve(pooled, order, real_impostor=None):
    """Macro DIR/FAR sweep. Both rates are averaged per penguin, not per photo.

    real_impostor: scores of photos of birds the model NEVER trained on. When
    given, these are the FAR numerator -- the honest measurement. The simulated
    fallback (hide the query's own prototype) sits far too low, because that bird
    was trained on and pushed away from every other identity, so it overstates DIR.
    """
    per_class = defaultdict(list)
    for path in order:
        r = pooled[path]
        per_class[r["true"]].append((r["score"], r["rank"] == 1, r["impostor"]))

    packed = [(np.array([v[0] for v in vals]),
               np.array([v[1] for v in vals], dtype=bool),
               np.array([v[2] for v in vals])) for vals in per_class.values()]

    if real_impostor is not None and len(real_impostor):
        imp_groups = [np.asarray(real_impostor)]
        pool = np.asarray(real_impostor)
    else:
        imp_groups = [g[2] for g in packed]
        pool = np.concatenate(imp_groups)

    lo = min(pool.min(), min(g[0].min() for g in packed))
    hi = max(pool.max(), max(g[0].max() for g in packed))
    thresholds = np.linspace(lo, hi, 2000)

    dir_rates, far_rates = [], []
    for t in thresholds:
        dir_rates.append(np.mean([np.mean(correct & (score >= t))
                                  for score, correct, _ in packed]))
        far_rates.append(np.mean([np.mean(g >= t) for g in imp_groups]))

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
    session_of = data.get("session_of_photo")
    if not session_of:
        raise SystemExit("cv_folds.json has no session_of_photo -- rerun "
                         "analysis/build_cv_folds.py so intervals can cluster on sessions")
    strangers = collect_strangers(set(classes))
    print(f"stranger set: {len(strangers)} never-trained birds, "
          f"{sum(len(v) for v in strangers.values())} photos", flush=True)

    rng = np.random.default_rng(SEED)
    report, arrays = {}, {}
    for tag in args.tags:
        print(f"\nevaluating {tag} ...", flush=True)
        pooled, stranger_by_fold = run_config(tag, manifest, classes, strangers)
        assert len(pooled) == len(order), f"{len(pooled)} predictions vs {len(order)} images"
        real_imp = [s for fold in stranger_by_fold for s in fold]

        entry, arrays[tag] = {}, {}
        metrics = {"rank1": lambda r: r["rank"] == 1,
                   "rank5": lambda r: r["rank"] <= 5,
                   "mAP": lambda r: r["ap"],
                   "knn_rank1": lambda r: r["knn_rank1"],
                   "rank1_colony": lambda r: r["rank_colony"] == 1}
        for key, fn in metrics.items():
            arrays[tag][key] = group_by_class_session(pooled, order, fn, session_of)
            entry[key] = macro_ci(arrays[tag][key], rng)

        entry["cmc"] = [round(float(np.mean([
            np.mean(np.asarray(v) <= k)
            for v in group_by_class(pooled, order, lambda r: r["rank"]).values()])), 4)
            for k in range(1, CMC_MAX + 1)]
        entry["open_set"] = open_set_curve(pooled, order, real_imp)
        entry["open_set_simulated"] = open_set_curve(pooled, order, None)
        entry["n_stranger_photos"] = len(real_imp)

        flat = group_by_class(pooled, order, lambda r: r["rank"] == 1)
        entry["per_class"] = {k: round(float(v.mean()), 4) for k, v in flat.items()}
        entry["n_images_per_class"] = {k: int(len(v)) for k, v in flat.items()}
        entry["never_correct"] = sorted(k for k, v in flat.items() if v.max() == 0)
        entry["n_images"] = len(order)
        report[tag] = entry

        print(f"\n=== {tag} ===   (MACRO, {len(order)} photos, {len(flat)} penguins,"
              f" session-clustered CIs)")
        for key, label in [("rank1", "rank-1 (35-way)"), ("rank5", "rank-5"),
                           ("mAP", "mAP"), ("knn_rank1", "1-NN rank-1"),
                           ("rank1_colony", "rank-1 (81-way)")]:
            d = entry[key]
            print(f"  {label:<18}{d['macro']:>7.3f}   [{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}]")
        print("  -- open set, REAL never-trained strangers --")
        for name, v in entry["open_set"]["at"].items():
            sim = entry["open_set_simulated"]["at"].get(name)
            extra = f"   (simulated said {sim['dir']:.3f})" if sim else ""
            print(f"  {name:<18}{v['dir']:>7.3f}   thr {v['threshold']:.3f}{extra}"
                  if v else f"  {name:<18}      -")
        nc = entry["never_correct"]
        print(f"  never recognised ({len(nc)}/{len(flat)}): {', '.join(nc) if nc else 'none'}")

    if len(args.tags) == 2:
        a, b = args.tags
        print(f"\n=== paired comparison: {b} minus {a} ===")
        report["_comparison"] = {"baseline": a, "candidate": b}
        for key, label in [("rank1", "rank-1"), ("rank5", "rank-5"),
                           ("mAP", "mAP"), ("knn_rank1", "1-NN rank-1"),
                           ("rank1_colony", "rank-1 (81-way)")]:
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
