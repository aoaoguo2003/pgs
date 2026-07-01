# -*- coding: utf-8 -*-
"""
Embedding-based penguin re-identification (CNN route).

Pipeline:
  1. Enroll a gallery: embed every train (+val) image with the exp1
     ResNet18 feature extractor -> the "vector database".
  2. Query with test images: nearest-neighbor search in the gallery.
  3. Report top-1 / top-5 retrieval accuracy, plus a prototype
     (class-mean) classifier, and per-class top-1.

This validates whether retrieval-based ID matches the exp1 softmax
classifier (test acc 0.950) while giving us a vector DB we can later
plug into the identify_penguin agent tool.

Run:
  D:/Anaconda/python.exe embedding_id/build_and_eval.py
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np

from embedder import Embedder, VectorStore, l2_normalize

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".JPG", ".JPEG", ".PNG"}


def list_split(data_dir: Path, split: str):
    """Return (paths, labels) for one split folder of class subdirs."""
    paths, labels = [], []
    root = data_dir / split
    for cls_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for f in sorted(cls_dir.iterdir()):
            if f.suffix in IMG_EXTS:
                paths.append(str(f))
                labels.append(cls_dir.name)
    return paths, labels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="penguins_dataset_split")
    ap.add_argument("--checkpoint", default="runs/exp1_baseline/best_model.pt")
    ap.add_argument("--gallery-splits", nargs="+", default=["train", "val"],
                    help="splits used as the enrolled reference gallery")
    ap.add_argument("--query-split", default="test")
    ap.add_argument("--out-dir", default="embedding_id/artifacts")
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    data_dir = (root / args.data_dir) if not os.path.isabs(args.data_dir) else Path(args.data_dir)
    ckpt = (root / args.checkpoint) if not os.path.isabs(args.checkpoint) else Path(args.checkpoint)
    out_dir = (root / args.out_dir) if not os.path.isabs(args.out_dir) else Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] Loading embedder from {ckpt} ...")
    embedder = Embedder(str(ckpt))
    print(f"      device={embedder.device}")

    # ---- enroll gallery ----
    g_paths, g_labels = [], []
    for sp in args.gallery_splits:
        p, l = list_split(data_dir, sp)
        g_paths += p; g_labels += l
    print(f"[2/4] Enrolling gallery: {len(g_paths)} images from {args.gallery_splits}")
    g_emb = embedder.embed_paths(g_paths, verbose=True)
    store = VectorStore(g_emb, g_labels, g_paths)
    print(f"      vector store backend = {store.backend}, dim = {g_emb.shape[1]}")

    # class prototypes (mean embedding per penguin), L2-normalized
    proto_names = sorted(set(g_labels))
    protos = np.stack([
        l2_normalize(g_emb[[i for i, l in enumerate(g_labels) if l == n]].mean(0, keepdims=True))[0]
        for n in proto_names
    ]).astype("float32")

    # ---- query ----
    q_paths, q_labels = list_split(data_dir, args.query_split)
    print(f"[3/4] Querying with {len(q_paths)} '{args.query_split}' images")
    q_emb = embedder.embed_paths(q_paths, verbose=True)

    scores, idx = store.search(q_emb, k=args.k)
    knn_pred = [store.labels[idx[i, 0]] for i in range(len(q_paths))]           # 1-NN
    topk_hit = [q_labels[i] in [store.labels[j] for j in idx[i]] for i in range(len(q_paths))]

    proto_sims = q_emb @ protos.T
    proto_pred = [proto_names[j] for j in proto_sims.argmax(1)]

    # ---- metrics ----
    n = len(q_paths)
    top1 = np.mean([knn_pred[i] == q_labels[i] for i in range(n)])
    top5 = np.mean(topk_hit)
    proto_top1 = np.mean([proto_pred[i] == q_labels[i] for i in range(n)])

    per_class = defaultdict(lambda: [0, 0])
    for i in range(n):
        per_class[q_labels[i]][1] += 1
        if knn_pred[i] == q_labels[i]:
            per_class[q_labels[i]][0] += 1

    print(f"\n[4/4] Results on '{args.query_split}' (n={n})")
    print(f"      1-NN   top-1 accuracy : {top1:.4f}")
    print(f"      1-NN   top-{args.k} accuracy : {top5:.4f}")
    print(f"      prototype top-1       : {proto_top1:.4f}")
    print(f"      (exp1 softmax baseline: 0.950)")

    worst = sorted(((c/t, name, c, t) for name, (c, t) in per_class.items()))[:8]
    print("\n      lowest per-class top-1:")
    for acc, name, c, t in worst:
        print(f"        {name:<14} {acc:.2f}  ({c}/{t})")

    # ---- persist gallery + report ----
    np.savez(out_dir / "gallery.npz",
             embeddings=g_emb, labels=np.array(g_labels), paths=np.array(g_paths),
             proto_names=np.array(proto_names), protos=protos)
    report = {
        "gallery_splits": args.gallery_splits,
        "query_split": args.query_split,
        "gallery_size": len(g_paths),
        "query_size": n,
        "embed_dim": int(g_emb.shape[1]),
        "backend": store.backend,
        "knn_top1": float(top1),
        f"knn_top{args.k}": float(top5),
        "prototype_top1": float(proto_top1),
        "exp1_softmax_top1": 0.950,
        "per_class_top1": {name: c / t for name, (c, t) in per_class.items()},
    }
    (out_dir / "retrieval_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nSaved gallery -> {out_dir/'gallery.npz'}")
    print(f"Saved report  -> {out_dir/'retrieval_report.json'}")


if __name__ == "__main__":
    main()
