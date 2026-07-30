# -*- coding: utf-8 -*-
"""
Single-image penguin identification against the enrolled gallery.

This is the core of the `identify_penguin(image)` agent tool: embed one
photo, search the vector store, and return ranked candidates plus an
open-set decision (confident / unsure -> ask to re-shoot / unknown).

Usage (CLI):
  D:/Anaconda/python.exe embedding_id/identify.py path/to/photo.jpg

Usage (as a module / agent tool):
  from identify import PenguinIdentifier
  ident = PenguinIdentifier()
  ident.identify("photo.jpg")   # -> dict
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from embedder import Embedder, VectorStore, l2_normalize

# Open-set thresholds on cosine similarity to the class prototypes.
# best score below CONFIDENT_SCORE -> unknown; margin below MARGIN -> ambiguous.
#
# Measured 2026-07-30 on the session-disjoint cross-validated ArcFace models,
# using the 564 photos of 46 colony members the models NEVER trained on as the
# stranger set (analysis/eval_cv.py). Operating points, macro over individuals:
#
#   threshold   strangers wrongly accepted   enrolled birds correctly named
#     0.974                 1%                          0.123
#     0.938                 5%                          0.237
#     0.908                10%                          0.312
#     0.800              29.7%                          (not an operating point)
#
# The previous value of 0.80 was tuned on the leaky random split by hiding a
# bird's own prototype and treating its runner-up as an "unknown". That
# simulation is far too easy -- the bird was in the training set and had been
# pushed away from every other identity -- so it overstated stranger rejection
# badly: it was documented as rejecting 96.6% of unenrolled birds, and actually
# accepts 29.7% of them. It also overstated DIR@FAR=1% by 87% (0.230 vs 0.123).
#
# 0.938 is shipped: refusing a real stranger 95 times in 100 while still naming
# roughly a quarter of enrolled birds. Raise towards 0.974 if a wrong name is
# more costly than a refusal; lower towards 0.908 for a keeper-facing tool where
# the human checks the answer anyway.
#
# TWO LIMITS TO STATE WHEN QUOTING THIS. (1) The figure is transferred from the
# cross-validated models; the deployed model trains on every colony member, so
# no in-colony bird is a genuine stranger for it and this cannot be re-measured
# without birds from outside the collection. (2) Once all 81 members are
# enrolled, the realistic "unknown" is no longer an unenrolled bird but a bad
# photo -- blurry, rear-facing, or not a penguin -- which this threshold has
# never been calibrated against.
CONFIDENT_SCORE = 0.938
AMBIGUOUS_MARGIN = 0.05


class PenguinIdentifier:
    def __init__(self,
                 checkpoint: str = "runs/deploy_arcface/model.pt",
                 gallery: str = "embedding_id/artifacts/gallery.npz",
                 root: str | None = None):
        base = Path(root) if root else Path(__file__).resolve().parent.parent
        self.embedder = Embedder(str(base / checkpoint))
        data = np.load(base / gallery, allow_pickle=True)
        self.store = VectorStore(data["embeddings"], list(data["labels"]), list(data["paths"]))
        self.proto_names = list(data["proto_names"])
        self.protos = data["protos"].astype("float32")

    def identify(self, image_path: str, k: int = 5) -> dict:
        q = self.embedder.embed_paths([image_path])          # (1, 512), normalized
        # prototype (class-level) ranking = robust top-1
        proto_sims = (q @ self.protos.T)[0]
        order = np.argsort(-proto_sims)
        candidates = [{"name": self.proto_names[j], "score": float(proto_sims[j])} for j in order[:k]]
        # nearest individual reference photos (for "here's a matching photo" UX)
        neighbors = self.store.identify(q[0], k=k)

        best = candidates[0]["score"]
        margin = candidates[0]["score"] - (candidates[1]["score"] if len(candidates) > 1 else 0.0)
        if best < CONFIDENT_SCORE:
            decision, message = "unknown", "No match among the enrolled penguins; please take a clearer front-facing, full-body photo."
        elif margin < AMBIGUOUS_MARGIN:
            decision, message = "ambiguous", "Several individuals look similar; please confirm, or take a clearer front-facing photo."
        else:
            decision, message = "confident", f"Matched {candidates[0]['name']}."

        return {
            "decision": decision,
            "message": message,
            "top1": candidates[0]["name"] if decision == "confident" else None,
            "candidates": candidates,
            "nearest_photos": [{"name": n, "score": s} for n, s in neighbors],
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()
    ident = PenguinIdentifier()
    print(json.dumps(ident.identify(args.image, k=args.k), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
