# -*- coding: utf-8 -*-
"""
Enrol the deployment gallery: every colony member, every photo.

This is the vector database the shipped identifier searches. It is deliberately
NOT the same thing as an evaluation split:

  * Every one of the colony's individuals is enrolled, including the ones with
    too few photos or too few capture sessions to be evaluated. A bird that is
    not in the gallery can never be identified -- it can only be refused as
    unknown -- so leaving it out guarantees failure, while enrolling it on two
    photographs merely makes success unlikely. Enrolment needs no session
    diversity; only honest *evaluation* does.
  * Every photo is enrolled. Nothing is held out, because cross validation has
    already produced the performance estimate (analysis/artifacts/cv_report.json)
    and withholding data now would only weaken the deployed system.

This also exercises the property that motivated the retrieval design in the
first place: adding an individual is an enrolment, not a retraining. Birds the
extractor never trained on still get a prototype here.

Run:
  D:/Anaconda/python.exe embedding_id/build_gallery.py
  D:/Anaconda/python.exe embedding_id/build_gallery.py --checkpoint runs/cv_arcface_strong/fold0/model.pt
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from embedder import Embedder, l2_normalize

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="penguins_data",
                    help="one directory per individual, all photos inside")
    ap.add_argument("--checkpoint", default="runs/deploy_arcface/model.pt")
    ap.add_argument("--out", default="embedding_id/artifacts/gallery.npz")
    ap.add_argument("--min-photos", type=int, default=1)
    args = ap.parse_args()

    src = ROOT / args.src
    paths, labels = [], []
    for d in sorted(p for p in src.iterdir() if p.is_dir()):
        imgs = [f for f in sorted(d.iterdir()) if f.suffix.lower() in IMG_EXTS]
        if len(imgs) < args.min_photos:
            print(f"  skip {d.name}: {len(imgs)} photos")
            continue
        paths += [str(f) for f in imgs]
        labels += [d.name] * len(imgs)

    ckpt = ROOT / args.checkpoint
    if not ckpt.exists():
        raise SystemExit(f"{ckpt} not found -- train it with "
                         f"'train_metric.py --loss arcface --aug strong --deploy'")
    print(f"embedding {len(paths)} photos of {len(set(labels))} individuals "
          f"with {args.checkpoint} ...")
    emb = Embedder(str(ckpt)).embed_paths(paths, verbose=True)

    names = sorted(set(labels))
    lab = np.array(labels)
    protos = np.stack([
        l2_normalize(emb[lab == n].mean(0, keepdims=True))[0] for n in names
    ]).astype("float32")

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, embeddings=emb, labels=lab, paths=np.array(paths),
             proto_names=np.array(names), protos=protos)

    counts = Counter(labels)
    thin = sorted((c, n) for n, c in counts.items())[:6]
    meta = {"checkpoint": args.checkpoint, "src": args.src,
            "n_individuals": len(names), "n_photos": len(paths),
            "embed_dim": int(emb.shape[1]),
            "photos_per_individual": {n: counts[n] for n in names}}
    (out.parent / "gallery_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nenrolled {len(names)} individuals, {len(paths)} photos, dim {emb.shape[1]}")
    print(f"  thinnest enrolments: " +
          ", ".join(f"{n} ({c})" for c, n in thin))
    print(f"  -> {out}")
    print("These prototypes are only as good as the photos behind them; the ones "
          "enrolled on a handful of images from a single shoot will be recognised "
          "poorly, which is a data limit and not a threshold to tune around.")


if __name__ == "__main__":
    main()
