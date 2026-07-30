# -*- coding: utf-8 -*-
"""
Canonical evaluation for the penguin re-ID retrieval pipeline.

METRIC POLICY (decided 2026-07-30): every reported number is MACRO -- the mean
of per-penguin accuracies, each penguin weighted equally. Per-image (micro)
accuracy is deliberately NOT computed or reported.

Rationale: the test set is heavily imbalanced (Medici 43 images, Beau 1). That
imbalance records which birds happened to be easy to photograph during data
collection; it is not a model of deployment. Micro accuracy silently adopts it
as a prior over "which penguin gets photographed", which nothing justifies. A
visitor or keeper points the camera at whichever bird they care about, so every
individual carries equal weight.

Because macro gives a bird with 1 test image the same 1/K weight as a bird with
43, a single photo can move the headline by 1/K (2.9 points at K=35). Every
macro number therefore ships with a bootstrap 95% CI, and no two configurations
should be called different unless their intervals separate.

Run:
  D:/Anaconda/python.exe analysis/evaluate.py                      # registered runs
  D:/Anaconda/python.exe analysis/evaluate.py --run runs/foo \
      --data penguins_dataset_split_session_disjoint --tag "foo"   # ad-hoc run
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageFile
from torchvision import models, transforms

ImageFile.LOAD_TRUNCATED_IMAGES = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Runs evaluated when no --run is given. (tag, run_dir, data_dir)
REGISTERED = [
    ("exp1b session-disjoint", "runs/exp1b_session_disjoint",
     "penguins_dataset_split_session_disjoint"),
    ("exp1b random-control", "runs/exp1b_random_control",
     "penguins_dataset_split_session_random"),
]

REPORT = ROOT / "analysis" / "artifacts" / "eval_report.json"
STABLE_MIN_IMAGES = 4   # secondary subset: birds with enough test images to be stable
N_BOOTSTRAP = 2000
SEED = 0


# --------------------------------------------------------------------------- data

def list_split(data_dir: Path, splits):
    paths, labels = [], []
    for sp in splits:
        for cls_dir in sorted(p for p in (data_dir / sp).iterdir() if p.is_dir()):
            for f in sorted(cls_dir.iterdir()):
                if f.suffix.lower() in IMG_EXTS:
                    paths.append(str(f))
                    labels.append(cls_dir.name)
    return paths, labels


def test_sessions_per_class(data_dir: Path, gap: int = 50):
    """How many distinct capture sessions each penguin contributes to the test set."""
    from session_disjoint_eval import cluster_sessions
    out = {}
    test_dir = data_dir / "test"
    for cls_dir in sorted(p for p in test_dir.iterdir() if p.is_dir()):
        names = [f.name for f in sorted(cls_dir.iterdir()) if f.suffix.lower() in IMG_EXTS]
        out[cls_dir.name] = len(cluster_sessions(names, gap)) if names else 0
    return out


# ---------------------------------------------------------------------- extractor

TFM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def load_extractor(ckpt_path: Path):
    """Load a checkpoint and return it as a bare feature extractor (fc stripped).

    Accepts both softmax-head checkpoints (fc.weight present) and metric-learning
    checkpoints where the classification weights live outside the backbone.
    """
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    classes = ckpt.get("class_names") or ckpt.get("classes")
    state = ckpt["model_state_dict"]

    arch = ckpt.get("arch", "resnet18")
    if arch != "resnet18":
        raise ValueError(f"unsupported arch {arch!r}; extend load_extractor()")
    m = models.resnet18(weights=None)

    if "fc.weight" in state:
        m.fc = nn.Linear(m.fc.in_features, state["fc.weight"].shape[0])
        m.load_state_dict(state)
        m.fc = nn.Identity()
    else:
        m.fc = nn.Identity()
        missing, unexpected = m.load_state_dict(state, strict=False)
        if unexpected:
            print(f"  note: ignored {len(unexpected)} non-backbone keys "
                  f"(e.g. {unexpected[0]})")
        if missing:
            raise ValueError(f"checkpoint is missing backbone weights: {missing[:3]}")

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    return m.eval().to(dev), dev, classes


@torch.no_grad()
def embed(model, dev, paths, bs=64):
    out = []
    for i in range(0, len(paths), bs):
        x = torch.stack([TFM(Image.open(p).convert("RGB")) for p in paths[i:i + bs]]).to(dev)
        out.append(model(x).cpu().numpy().astype("float32"))
    e = np.concatenate(out, 0)
    return e / np.maximum(np.linalg.norm(e, axis=1, keepdims=True), 1e-10)


# ------------------------------------------------------------------------- macro

def per_class_hits(hit: np.ndarray, ql: np.ndarray):
    """Split a boolean per-query hit vector into one array per true class."""
    by_class = defaultdict(list)
    for h, lab in zip(hit, ql):
        by_class[lab].append(bool(h))
    return {k: np.asarray(v, dtype=np.float64) for k, v in sorted(by_class.items())}


def macro_with_ci(by_class, rng, n_boot=N_BOOTSTRAP, alpha=0.05):
    """Macro accuracy + bootstrap CI, resampling test images within each penguin.

    Caveat, state it when quoting: images of one bird often come from a single
    burst and are highly correlated, so the effective sample size is below the
    image count and this interval is optimistic (too narrow), never pessimistic.
    """
    arrays = list(by_class.values())
    point = float(np.mean([a.mean() for a in arrays]))
    boot = np.zeros(n_boot)
    for a in arrays:
        idx = rng.integers(0, len(a), size=(n_boot, len(a)))
        boot += a[idx].mean(axis=1)
    boot /= len(arrays)
    lo, hi = np.percentile(boot, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"macro": round(point, 4),
            "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "se": round(float(boot.std(ddof=1)), 4),
            "n_classes": len(arrays)}


def summarise(hit, ql, rng, stable_classes):
    by_class = per_class_hits(hit, ql)
    out = macro_with_ci(by_class, rng)
    stable = {k: v for k, v in by_class.items() if k in stable_classes}
    out["macro_stable_subset"] = macro_with_ci(stable, rng)["macro"] if stable else None
    out["per_class"] = {k: round(float(v.mean()), 4) for k, v in by_class.items()}
    out["never_correct"] = sorted(k for k, v in by_class.items() if v.max() == 0)
    return out


# ---------------------------------------------------------------------- retrieval

def evaluate(model, dev, data_dir: Path, rng):
    gp, gl = list_split(data_dir, ["train", "val"])   # gallery = enrolled photos
    qp, ql = list_split(data_dir, ["test"])           # query = held-out photos
    G, Q = embed(model, dev, gp), embed(model, dev, qp)
    gl, ql = np.array(gl), np.array(ql)

    n_test = defaultdict(int)
    for lab in ql:
        n_test[lab] += 1
    stable_classes = {k for k, v in n_test.items() if v >= STABLE_MIN_IMAGES}

    sims = Q @ G.T                                    # cosine: both sides L2-normalised
    order = np.argsort(-sims, axis=1)

    names = sorted(set(gl.tolist()))
    protos = np.stack([
        (lambda v: v / max(np.linalg.norm(v), 1e-10))(G[gl == n].mean(0))
        for n in names]).astype("float32")
    psims = Q @ protos.T
    porder = np.argsort(-psims, axis=1)
    pnames = np.array(names)

    res = {
        "prototype_top1": summarise(pnames[porder[:, 0]] == ql, ql, rng, stable_classes),
        "prototype_top5": summarise(
            np.array([ql[i] in pnames[porder[i, :5]] for i in range(len(ql))]),
            ql, rng, stable_classes),
        "knn_top1": summarise(gl[order[:, 0]] == ql, ql, rng, stable_classes),
        "knn_top5": summarise(
            np.array([ql[i] in gl[order[i, :5]] for i in range(len(ql))]),
            ql, rng, stable_classes),
    }
    res["n_test_per_class"] = dict(sorted(n_test.items()))
    res["n_gallery"] = len(gp)
    res["n_query"] = len(qp)
    res["stable_subset"] = {"min_test_images": STABLE_MIN_IMAGES,
                            "n_classes": len(stable_classes),
                            "n_images": int(sum(n_test[c] for c in stable_classes))}
    try:
        res["test_sessions_per_class"] = test_sessions_per_class(data_dir)
    except Exception as exc:                                   # non-fatal extra context
        print(f"  note: could not cluster test sessions ({exc})")
    return res


# ------------------------------------------------------------------------- report

def print_run(tag, res):
    ss = res["stable_subset"]
    n_cls = res["prototype_top1"]["n_classes"]
    subset_header = f">={ss['min_test_images']} imgs ({ss['n_classes']})"

    print(f"\n=== {tag} ===")
    print(f"  gallery {res['n_gallery']} imgs   query {res['n_query']} imgs   "
          f"{n_cls} penguins")
    print(f"  {'metric (MACRO)':<20}{'value':>8}{'95% CI':>18}{subset_header:>18}")

    for key, label in [("prototype_top1", "prototype top-1"),
                       ("prototype_top5", "prototype top-5"),
                       ("knn_top1", "1-NN top-1"),
                       ("knn_top5", "1-NN top-5")]:
        d = res[key]
        lo, hi = d["ci95"]
        ci = f"[{lo:.3f}, {hi:.3f}]"
        sub = "-" if d["macro_stable_subset"] is None else f"{d['macro_stable_subset']:.3f}"
        print(f"  {label:<20}{d['macro']:>8.3f}{ci:>18}{sub:>18}")

    nc = res["prototype_top1"]["never_correct"]
    print(f"  never recognised ({len(nc)}/{n_cls}): {', '.join(nc) if nc else 'none'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="checkpoint dir containing best_model.pt")
    ap.add_argument("--data", help="dataset dir with train/val/test")
    ap.add_argument("--tag", help="name for this run in the report")
    ap.add_argument("--out", default=str(REPORT))
    args = ap.parse_args()

    if args.run:
        if not (args.data and args.tag):
            ap.error("--run requires --data and --tag")
        cases = [(args.tag, args.run, args.data)]
    else:
        cases = REGISTERED

    out_path = Path(args.out)
    report = {}
    if out_path.exists():
        report = json.loads(out_path.read_text(encoding="utf-8"))

    for tag, run, data in cases:
        run_dir, data_dir = ROOT / run, ROOT / data
        ckpt = run_dir / "best_model.pt"
        if not ckpt.exists():
            print(f"skip {tag}: no {ckpt}")
            continue
        print(f"\nevaluating {tag} ...")
        model, dev, _ = load_extractor(ckpt)
        rng = np.random.default_rng(SEED)
        res = evaluate(model, dev, data_dir, rng)
        res["run_dir"], res["data_dir"] = run, data
        report[tag] = res
        print_run(tag, res)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nAll numbers above are MACRO (per-penguin, equal weight). "
          f"Micro is not computed by design.")
    print(f"CIs resample images within each penguin; burst correlation makes them "
          f"optimistic -- do not call two configs different on overlapping CIs.")
    print(f"saved -> {out_path}")


if __name__ == "__main__":
    main()
