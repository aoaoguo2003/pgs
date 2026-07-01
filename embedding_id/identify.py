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

# Open-set thresholds on cosine similarity (tune on a held-out set).
# best score below LOW  -> unknown; margin below MARGIN -> ambiguous.
CONFIDENT_SCORE = 0.55
AMBIGUOUS_MARGIN = 0.05


class PenguinIdentifier:
    def __init__(self,
                 checkpoint: str = "runs/exp1_baseline/best_model.pt",
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
            decision, message = "unknown", "未能匹配到已登记的企鹅，请拍一张更清晰的正面全身照。"
        elif margin < AMBIGUOUS_MARGIN:
            decision, message = "ambiguous", "有几只很像，请确认或换一张更清晰的正面照。"
        else:
            decision, message = "confident", f"匹配到 {candidates[0]['name']}。"

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
