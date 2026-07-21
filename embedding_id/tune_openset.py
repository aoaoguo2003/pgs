# -*- coding: utf-8 -*-
"""
Tune the open-set rejection threshold used by `identify.py`.

The identifier must not only say *which* enrolled penguin a photo shows, it
must also say "I don't know this bird" -- only 44 of the ~81 colony members
have enough photos to be enrolled, so unenrolled birds will be queried.

We have no labelled "unknown penguin" set, so we simulate one by
leave-one-penguin-out: drop penguin P's prototype from the gallery, then query
with P's test photos. The best remaining score is what the system would report
for a genuinely unenrolled bird. Comparing that distribution against the
scores obtained with the full gallery gives a proper threshold sweep.

Reported per threshold:
  - known kept       (true positive rate): enrolled birds still identified
  - unknown rejected (true negative rate): unenrolled birds correctly refused
  - balanced accuracy: the mean of the two

Run:
  D:/Anaconda/python.exe embedding_id/tune_openset.py
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from embedder import Embedder, l2_normalize

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".JPG", ".JPEG", ".PNG"}


def list_split(data_dir: Path, split: str):
    """Return (paths, labels) for one split folder of class subdirs."""
    paths, labels = [], []
    for cls_dir in sorted(p for p in (data_dir / split).iterdir() if p.is_dir()):
        for f in sorted(cls_dir.iterdir()):
            if f.suffix in IMG_EXTS:
                paths.append(str(f))
                labels.append(cls_dir.name)
    return paths, labels


def roc_auc(pos: np.ndarray, neg: np.ndarray) -> float:
    """Rank-based AUC: P(score of a known > score of an unknown)."""
    scores = np.concatenate([pos, neg])
    order = np.argsort(scores)
    ranks = np.empty(len(scores), dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)
    n_pos, n_neg = len(pos), len(neg)
    return float((ranks[:n_pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="penguins_dataset_split")
    ap.add_argument("--checkpoint", default="runs/exp1_baseline/best_model.pt")
    ap.add_argument("--gallery-splits", nargs="+", default=["train", "val"])
    ap.add_argument("--query-split", default="test")
    ap.add_argument("--out-dir", default="embedding_id/artifacts")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent

    def resolve(p):
        return Path(p) if os.path.isabs(p) else root / p

    data_dir, ckpt, out_dir = map(resolve, (args.data_dir, args.checkpoint, args.out_dir))
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] Loading embedder from {ckpt} ...")
    embedder = Embedder(str(ckpt))

    g_paths, g_labels = [], []
    for sp in args.gallery_splits:
        p, l = list_split(data_dir, sp)
        g_paths += p; g_labels += l
    q_paths, q_labels = list_split(data_dir, args.query_split)
    print(f"[2/3] Embedding {len(g_paths)} gallery + {len(q_paths)} query images ...")
    g_emb = embedder.embed_paths(g_paths, verbose=False)
    q_emb = embedder.embed_paths(q_paths, verbose=False)
    g_labels = np.array(g_labels)
    q_labels = np.array(q_labels)

    names = sorted(set(g_labels.tolist()))
    protos = np.stack([
        l2_normalize(g_emb[g_labels == n].mean(0, keepdims=True))[0] for n in names
    ]).astype("float32")

    # ---- known: full gallery ----
    sims = q_emb @ protos.T
    known_best = sims.max(1)

    # ---- unknown: leave-the-query's-own-penguin-out ----
    unknown_best = np.array([
        (q_emb[i] @ protos[[j for j, n in enumerate(names) if n != lab]].T).max()
        for i, lab in enumerate(q_labels)
    ])

    print(f"\n[3/3] Score distributions (n={len(q_paths)})")
    print(f"{'percentile':<14}{'KNOWN':>10}{'UNKNOWN':>10}")
    for p in (1, 5, 10, 25, 50, 75, 90, 95, 99):
        print(f"  p{p:<11}{np.percentile(known_best, p):>10.3f}"
              f"{np.percentile(unknown_best, p):>10.3f}")
    print(f"  {'mean':<11}{known_best.mean():>10.3f}{unknown_best.mean():>10.3f}")

    auc = roc_auc(known_best, unknown_best)
    print(f"\n  AUC (known vs unknown separability) = {auc:.3f}   [0.5=random, 1.0=perfect]")

    print(f"\n{'threshold':>10}{'known kept':>13}{'unknown rej.':>15}{'balanced':>11}")
    sweep, best = [], None
    for thr in np.arange(0.40, 0.96, 0.05):
        tpr = float((known_best >= thr).mean())
        tnr = float((unknown_best < thr).mean())
        bal = (tpr + tnr) / 2
        sweep.append({"threshold": round(float(thr), 2), "known_kept": tpr,
                      "unknown_rejected": tnr, "balanced_accuracy": bal})
        if best is None or bal > best["balanced_accuracy"]:
            best = sweep[-1]
        print(f"{thr:>10.2f}{tpr:>13.1%}{tnr:>15.1%}{bal:>11.1%}")

    print(f"\n  best balanced threshold = {best['threshold']:.2f} "
          f"(balanced accuracy {best['balanced_accuracy']:.1%})")
    print("  NOTE: known-bird scores are optimistic -- train and test share photo "
          "sessions.\n        Re-run after a session-disjoint split is available.")

    report = {
        "n_query": len(q_paths), "n_enrolled_penguins": len(names),
        "auc_known_vs_unknown": auc,
        "known_score_mean": float(known_best.mean()),
        "unknown_score_mean": float(unknown_best.mean()),
        "sweep": sweep, "recommended_threshold": best["threshold"],
    }
    out = out_dir / "openset_threshold_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nSaved report -> {out}")


if __name__ == "__main__":
    main()
