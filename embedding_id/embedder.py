# -*- coding: utf-8 -*-
"""
Image -> embedding, and a small swappable vector store.

The embedding backbone reuses the trained exp1 ResNet18 (a CNN):
we drop the classification head (fc) and take the 512-d penultimate
feature (global-average-pooled conv features) as the identity embedding.

This is the "CNN route" for embedding-based re-identification: no new
training, we reuse the model that already reached 0.950 test accuracy and
turn it into a feature extractor for a vector database.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageFile
from torchvision import models, transforms

ImageFile.LOAD_TRUNCATED_IMAGES = True

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
EMBED_DIM = 512  # resnet18 penultimate features


def build_eval_transform(img_size: int = 224) -> transforms.Compose:
    """Must match train_experiment1.py eval transform for consistency."""
    return transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def build_tta_transforms(img_size: int = 224) -> list[transforms.Compose]:
    """
    Test-time augmentation views. Each returns a normalized tensor; we embed
    every view and average -> a more robust embedding. No training involved.
    Views: base resize, horizontal flip, resize+center-crop, and its flip.
    """
    norm = transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
    to_t = transforms.ToTensor()
    bigger = int(round(img_size * 256 / 224))
    hflip = transforms.RandomHorizontalFlip(p=1.0)
    return [
        transforms.Compose([transforms.Resize((img_size, img_size)), to_t, norm]),
        transforms.Compose([transforms.Resize((img_size, img_size)), hflip, to_t, norm]),
        transforms.Compose([transforms.Resize(bigger), transforms.CenterCrop(img_size), to_t, norm]),
        transforms.Compose([transforms.Resize(bigger), transforms.CenterCrop(img_size), hflip, to_t, norm]),
    ]


class Embedder:
    """Wraps the exp1 ResNet18 as a frozen 512-d feature extractor."""

    def __init__(self, checkpoint: str, device: str | None = None, img_size: int = 224,
                 num_classes: int | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tfm = build_eval_transform(img_size)
        self.tta_tfms = build_tta_transforms(img_size)

        ckpt = torch.load(checkpoint, map_location="cpu", weights_only=False)
        state = ckpt.get("model_state_dict", ckpt)

        model = models.resnet18(weights=None)
        in_features = model.fc.in_features  # 512
        # Rebuild the exact classification head used in training so the
        # state_dict loads, then replace it with Identity to expose the 512-d
        # feature. The head size is inferred from the checkpoint (saved fc
        # weight, else class_names) so a model with any number of classes loads;
        # pass num_classes to override.
        if num_classes is None:
            if "fc.weight" in state:
                num_classes = state["fc.weight"].shape[0]
            elif "class_names" in ckpt:
                num_classes = len(ckpt["class_names"])
            else:
                num_classes = 44  # legacy fallback
        model.fc = nn.Linear(in_features, num_classes)
        model.load_state_dict(state)
        model.fc = nn.Identity()  # now forward() returns the 512-d embedding
        model.eval().to(self.device)
        self.model = model

    @torch.no_grad()
    def embed_paths(self, paths: list[str], batch_size: int = 64,
                    normalize: bool = True, verbose: bool = False) -> np.ndarray:
        feats: list[np.ndarray] = []
        for i in range(0, len(paths), batch_size):
            batch_paths = paths[i:i + batch_size]
            imgs = []
            for p in batch_paths:
                img = Image.open(p).convert("RGB")
                imgs.append(self.tfm(img))
            x = torch.stack(imgs).to(self.device)
            f = self.model(x).cpu().numpy().astype("float32")
            feats.append(f)
            if verbose:
                print(f"  embedded {min(i + batch_size, len(paths))}/{len(paths)}", end="\r")
        if verbose:
            print()
        emb = np.concatenate(feats, axis=0)
        if normalize:
            emb = l2_normalize(emb)
        return emb

    @torch.no_grad()
    def embed_paths_tta(self, paths: list[str], batch_size: int = 64,
                        verbose: bool = False) -> np.ndarray:
        """Embed each image under several TTA views and average the vectors."""
        views = self.tta_tfms
        acc = np.zeros((len(paths), EMBED_DIM), dtype="float32")
        for v_i, tfm in enumerate(views):
            for i in range(0, len(paths), batch_size):
                batch = paths[i:i + batch_size]
                x = torch.stack([tfm(Image.open(p).convert("RGB")) for p in batch]).to(self.device)
                acc[i:i + len(batch)] += self.model(x).cpu().numpy().astype("float32")
            if verbose:
                print(f"  TTA view {v_i + 1}/{len(views)} done")
        acc /= len(views)              # average across views
        return l2_normalize(acc)       # normalize the averaged embedding


def l2_normalize(x: np.ndarray, eps: float = 1e-10) -> np.ndarray:
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(n, eps)


class VectorStore:
    """
    Minimal cosine-similarity vector store over the enrolled gallery.

    Uses FAISS (IndexFlatIP over L2-normalized vectors = cosine) when
    available, otherwise falls back to a numpy brute-force search. The
    interface is identical either way, so the backend is swappable
    (FAISS -> Qdrant/Milvus later) without touching call sites.
    """

    def __init__(self, embeddings: np.ndarray, labels: list[str], paths: list[str]):
        self.embeddings = embeddings.astype("float32")  # assumed L2-normalized
        self.labels = list(labels)
        self.paths = list(paths)
        self._faiss = None
        try:
            import faiss  # type: ignore
            index = faiss.IndexFlatIP(self.embeddings.shape[1])
            index.add(self.embeddings)
            self._faiss = index
            self.backend = "faiss"
        except Exception:
            self.backend = "numpy"

    def search(self, queries: np.ndarray, k: int = 5):
        """Return (scores, indices) of the top-k nearest gallery vectors."""
        q = queries.astype("float32")
        if self._faiss is not None:
            scores, idx = self._faiss.search(q, k)
            return scores, idx
        sims = q @ self.embeddings.T                 # cosine (both normalized)
        idx = np.argsort(-sims, axis=1)[:, :k]
        scores = np.take_along_axis(sims, idx, axis=1)
        return scores, idx

    def identify(self, query_vec: np.ndarray, k: int = 5):
        """Single-vector convenience: returns ranked (name, score) list."""
        scores, idx = self.search(query_vec.reshape(1, -1), k)
        return [(self.labels[j], float(s)) for s, j in zip(scores[0], idx[0])]
