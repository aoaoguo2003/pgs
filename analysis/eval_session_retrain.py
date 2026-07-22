# -*- coding: utf-8 -*-
"""
Compare the two retrained models (see build_session_splits.py):

  A. session-disjoint  -- trained and tested on session-disjoint splits
  B. random-control     -- same penguins/images/counts, random splits

Both are evaluated on their OWN matched test set. The gap is the honest cost of
end-to-end cross-session generalisation, with class count and data volume held
fixed. We report the softmax classifier (exp1 style) and the embedding
retrieval (exp3 style: 1-NN / prototype / top-5) for each.

Run (after training finishes):
  D:/Anaconda/python.exe analysis/eval_session_retrain.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageFile
from torchvision import models, transforms

ImageFile.LOAD_TRUNCATED_IMAGES = True
ROOT = Path(__file__).resolve().parent.parent
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

CASES = [
    ("session-disjoint", "penguins_dataset_split_session_disjoint", "runs/exp1b_session_disjoint"),
    ("random-control", "penguins_dataset_split_session_random", "runs/exp1b_random_control"),
]

TFM = transforms.Compose([
    transforms.Resize((224, 224)), transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])


def list_split(data_dir: Path, splits):
    paths, labels = [], []
    for sp in splits:
        for cls_dir in sorted(p for p in (data_dir / sp).iterdir() if p.is_dir()):
            for f in sorted(cls_dir.iterdir()):
                if f.suffix.lower() in IMG_EXTS:
                    paths.append(str(f)); labels.append(cls_dir.name)
    return paths, labels


def load_extractor(ckpt_path):
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    classes = ckpt["class_names"]
    state = ckpt["model_state_dict"]
    m = models.resnet18(weights=None)
    m.fc = nn.Linear(m.fc.in_features, len(classes))
    m.load_state_dict(state)
    m.fc = nn.Identity()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    return m.eval().to(dev), dev


@torch.no_grad()
def embed(model, dev, paths, bs=64):
    out = []
    for i in range(0, len(paths), bs):
        x = torch.stack([TFM(Image.open(p).convert("RGB")) for p in paths[i:i + bs]]).to(dev)
        out.append(model(x).cpu().numpy().astype("float32"))
    e = np.concatenate(out, 0)
    return e / np.maximum(np.linalg.norm(e, axis=1, keepdims=True), 1e-10)


def retrieval(model, dev, data_dir):
    gp, gl = list_split(data_dir, ["train", "val"])
    qp, ql = list_split(data_dir, ["test"])
    G, Q = embed(model, dev, gp), embed(model, dev, qp)
    gl, ql = np.array(gl), np.array(ql)
    sims = Q @ G.T
    knn = np.array([gl[j] for j in sims.argmax(1)])
    top5 = np.array([ql[i] in [gl[j] for j in np.argsort(-sims[i])[:5]] for i in range(len(ql))])
    names = sorted(set(gl.tolist()))
    protos = np.stack([(lambda v: v / max(np.linalg.norm(v), 1e-10))(G[gl == n].mean(0))
                       for n in names]).astype("float32")
    proto = np.array([names[j] for j in (Q @ protos.T).argmax(1)])
    return {"knn_top1": round(float((knn == ql).mean()), 4),
            "prototype_top1": round(float((proto == ql).mean()), 4),
            "top5": round(float(top5.mean()), 4), "n_test": int(len(ql))}


def main():
    results = {}
    for name, data, run in CASES:
        data_dir, run_dir = ROOT / data, ROOT / run
        fm = json.loads((run_dir / "final_metrics.json").read_text())
        model, dev = load_extractor(run_dir / "best_model.pt")
        ret = retrieval(model, dev, data_dir)
        results[name] = {"softmax_test_top1": round(fm["test_accuracy"], 4),
                         "best_val_top1": round(fm["best_val_accuracy"], 4),
                         "best_epoch": fm["best_epoch"], **ret}

    a, b = results["session-disjoint"], results["random-control"]
    print("End-to-end retrain: session-disjoint vs random-control")
    print("(same 35 penguins, same images, same per-penguin counts; only the "
          "split logic differs)\n")
    print(f"{'metric':<22}{'random(leaky)':>15}{'session(clean)':>16}{'gap':>9}")
    for key, label in [("softmax_test_top1", "softmax test top-1"),
                       ("prototype_top1", "retrieval proto top-1"),
                       ("knn_top1", "retrieval 1-NN top-1"),
                       ("top5", "retrieval top-5")]:
        print(f"{label:<22}{b[key]:>15.3f}{a[key]:>16.3f}{b[key] - a[key]:>+9.3f}")
    print(f"\n{'best val top-1':<22}{b['best_val_top1']:>15.3f}{a['best_val_top1']:>16.3f}")
    print(f"{'test images':<22}{b['n_test']:>15}{a['n_test']:>16}")
    print("\nrandom(leaky)  = train/test share sessions (10% near-dup test imgs)")
    print("session(clean) = session-disjoint (0% near-dup test imgs)")
    print("gap = the honest cost of cross-session generalisation")

    out = ROOT / "analysis" / "artifacts" / "session_retrain_report.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
