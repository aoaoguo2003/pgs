# -*- coding: utf-8 -*-
"""
Train the penguin re-ID feature extractor under session-wise K-fold CV.

Protocol (pre-registered 2026-07-30 -- do not tune per config):
  * folds come from analysis/build_cv_folds.py; test = one fold, train = the rest
  * NO validation split and NO early stopping. Every run trains for a fixed
    epoch budget on a cosine schedule annealed to zero and the FINAL epoch is
    kept. This keeps 80% of the data in train (a val split would drop it to
    ~68%) and removes checkpoint selection as a source of bias -- the previous
    round of experiments selected checkpoints on per-image val accuracy, which
    silently optimised for the few heavily-photographed birds.
  * identical settings for every loss/augmentation config being compared.

Losses:
  softmax  -- plain cross-entropy over a linear head (baseline)
  arcface  -- additive angular margin; the head is used for training only, the
              deployed artefact is the 512-d backbone embedding either way

Run:
  D:/Anaconda/python.exe train_metric.py --loss arcface --aug strong --all-folds
  D:/Anaconda/python.exe train_metric.py --loss softmax --aug basic --fold 0
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageFile
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

ImageFile.LOAD_TRUNCATED_IMAGES = True
ROOT = Path(__file__).resolve().parent
FOLDS_JSON = ROOT / "analysis" / "artifacts" / "cv_folds.json"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]


# ------------------------------------------------------------------------ data

def build_transform(aug: str, train: bool):
    if not train or aug == "none":
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD)])
    if aug == "basic":
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD)])
    if aug == "strong":
        return transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.RandomResizedCrop(224, scale=(0.65, 1.0), ratio=(0.75, 1.33)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.3, contrast=0.3,
                                   saturation=0.3, hue=0.05),
            transforms.RandomRotation(12),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD),
            transforms.RandomErasing(p=0.4, scale=(0.02, 0.18))])
    raise ValueError(f"unknown aug {aug!r}")


class PenguinSet(Dataset):
    def __init__(self, paths, labels, tfm):
        self.paths, self.labels, self.tfm = paths, labels, tfm

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        img = Image.open(ROOT / self.paths[i]).convert("RGB")
        return self.tfm(img), self.labels[i]


def collect_extra(src: Path, exclude: set, min_photos: int):
    """Colony members too sparse to EVALUATE, usable as extra TRAINING identities.

    A bird needs >=16 photos and >=3 capture sessions to enter the cross-validated
    evaluation; 46 of the 81 do not qualify. Nothing stops their photos being extra
    classes for the metric-learning objective, which never sees the test set. They
    are added to train in every fold and never to test or the gallery, so the
    reported numbers stay comparable to runs without them.
    """
    out = {}
    for d in sorted(p for p in src.iterdir() if p.is_dir()):
        if d.name in exclude:
            continue
        imgs = [f for f in sorted(d.iterdir()) if f.suffix.lower() in IMG_EXTS]
        if len(imgs) >= min_photos:
            out[d.name] = [str(f.relative_to(ROOT)) for f in imgs]
    return out


def collect_all(src: Path, min_photos: int):
    """Every colony member with enough photos, all photos, for the deploy model."""
    out = {}
    for d in sorted(p for p in src.iterdir() if p.is_dir()):
        imgs = [f for f in sorted(d.iterdir()) if f.suffix.lower() in IMG_EXTS]
        if len(imgs) >= min_photos:
            out[d.name] = [[str(f.relative_to(ROOT)) for f in imgs]]   # one group
    return out


def load_fold(manifest, fold, classes, extra=None):
    """Return (train_paths, train_labels, n_test) for one CV round.

    fold=None is deploy mode: no group index ever matches, so every photo goes to
    train and nothing is held out. That is correct for the shipped model -- cross
    validation has already produced the performance estimate, and holding data
    back now would only make the deployed extractor worse than the one measured.
    """
    extra = extra or {}
    tr_p, tr_y, n_test = [], [], 0
    for ci, pen in enumerate(classes):
        if pen in manifest:
            for gi, group in enumerate(manifest[pen]):
                if gi == fold:
                    n_test += len(group)
                else:
                    tr_p.extend(group)
                    tr_y.extend([ci] * len(group))
        else:                                   # extra identity: always train-only
            tr_p.extend(extra[pen])
            tr_y.extend([ci] * len(extra[pen]))
    return tr_p, tr_y, n_test


# ------------------------------------------------------------------------ head

class ArcFaceHead(nn.Module):
    """Additive angular margin head. Margin is warmed up so early training is
    plain cosine softmax -- a full margin from step 0 destabilises small data."""

    def __init__(self, dim, n_classes, scale=30.0, margin=0.3):
        super().__init__()
        self.W = nn.Parameter(torch.empty(n_classes, dim))
        nn.init.xavier_normal_(self.W)
        self.scale, self.margin = scale, margin

    def forward(self, feat, labels, margin_scale=1.0):
        cos = F.normalize(feat) @ F.normalize(self.W).t()
        cos = cos.clamp(-1 + 1e-7, 1 - 1e-7)
        m = self.margin * margin_scale
        if m > 0:
            theta = torch.acos(cos)
            onehot = torch.zeros_like(cos).scatter_(1, labels.view(-1, 1), 1.0)
            cos = torch.cos(theta + m * onehot)
        return self.scale * cos


def build_model(loss: str, n_classes: int, device):
    net = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    dim = net.fc.in_features
    if loss == "softmax":
        net.fc = nn.Linear(dim, n_classes)
        head = None
    else:
        net.fc = nn.Identity()
        head = ArcFaceHead(dim, n_classes).to(device)
    return net.to(device), head


# --------------------------------------------------------------------- training

def train_one_fold(args, manifest, classes, fold, out_dir, device, extra=None):
    tr_p, tr_y, n_test = load_fold(manifest, fold, classes, extra)
    ds = PenguinSet(tr_p, tr_y, build_transform(args.aug, train=True))
    # persistent_workers matters enormously on Windows: without it the loader
    # respawns every worker process each epoch, and each respawn re-imports
    # torch. Measured cost of leaving it off here was ~5x wall-clock.
    dl = DataLoader(ds, batch_size=args.batch_size, shuffle=True,
                    num_workers=args.num_workers, pin_memory=True, drop_last=False,
                    persistent_workers=args.num_workers > 0,
                    prefetch_factor=4 if args.num_workers > 0 else None)

    net, head = build_model(args.loss, len(classes), device)
    params = list(net.parameters()) + (list(head.parameters()) if head else [])
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=args.weight_decay)
    crit = nn.CrossEntropyLoss(label_smoothing=args.label_smoothing)

    steps = max(1, len(dl))
    total = args.epochs * steps
    warm = args.warmup_epochs * steps

    def lr_at(step):
        if step < warm:
            return step / max(1, warm)
        p = (step - warm) / max(1, total - warm)
        return 0.5 * (1 + math.cos(math.pi * p))

    sched = torch.optim.lr_scheduler.LambdaLR(opt, lr_at)
    scaler = torch.amp.GradScaler("cuda", enabled=(device == "cuda"))

    out_dir.mkdir(parents=True, exist_ok=True)
    hist = open(out_dir / "history.csv", "w", newline="", encoding="utf-8")
    wr = csv.writer(hist)
    wr.writerow(["epoch", "train_loss", "train_acc", "lr", "margin_scale"])

    t0 = time.time()
    for ep in range(1, args.epochs + 1):
        net.train()
        if head:
            head.train()
        ms = min(1.0, ep / max(1, args.margin_warmup_epochs))
        tot_loss = tot_ok = tot_n = 0
        for x, y in dl:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=(device == "cuda")):
                feat = net(x)
                logits = head(feat, y, ms) if head else feat
                loss = crit(logits, y)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            sched.step()
            tot_loss += loss.item() * y.size(0)
            tot_ok += (logits.argmax(1) == y).sum().item()
            tot_n += y.size(0)
        wr.writerow([ep, tot_loss / tot_n, tot_ok / tot_n,
                     opt.param_groups[0]["lr"], ms])
        if ep % 10 == 0 or ep == 1 or ep == args.epochs:
            print(f"    epoch {ep:>3}/{args.epochs}  loss {tot_loss / tot_n:.4f}  "
                  f"train_acc {tot_ok / tot_n:.3f}", flush=True)
    hist.close()

    # fc is dropped at inference; save the backbone exactly as evaluate.py loads it
    torch.save({"arch": "resnet18",
                "class_names": classes,
                "model_state_dict": net.state_dict(),
                "fold": fold,
                "config": vars(args)},
               out_dir / "model.pt")
    mins = (time.time() - t0) / 60
    print(f"    fold {fold}: {len(tr_p)} train imgs, {n_test} test imgs, "
          f"{mins:.1f} min -> {out_dir/'model.pt'}", flush=True)
    return {"fold": fold, "n_train": len(tr_p), "n_test": n_test,
            "final_train_acc": round(tot_ok / tot_n, 4), "minutes": round(mins, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loss", choices=["softmax", "arcface"], required=True)
    ap.add_argument("--aug", choices=["none", "basic", "strong"], default="basic")
    ap.add_argument("--fold", type=int)
    ap.add_argument("--all-folds", action="store_true")
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--label-smoothing", type=float, default=0.0)
    ap.add_argument("--warmup-epochs", type=int, default=3)
    ap.add_argument("--margin-warmup-epochs", type=int, default=5)
    ap.add_argument("--num-workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--tag")
    ap.add_argument("--extra-identities", action="store_true",
                    help="add colony members too sparse to evaluate as extra "
                         "TRAINING classes (test set and gallery are unchanged)")
    ap.add_argument("--extra-src", default="penguins_data")
    ap.add_argument("--extra-min-photos", type=int, default=5)
    ap.add_argument("--deploy", action="store_true",
                    help="train the shipped model: every colony member, every "
                         "photo, no held-out set, same recipe as the CV arms")
    ap.add_argument("--deploy-min-photos", type=int, default=3)
    args = ap.parse_args()

    if not args.deploy and args.fold is None and not args.all_folds:
        ap.error("pass --fold N, --all-folds, or --deploy")

    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if args.deploy:
        manifest = collect_all(ROOT / args.extra_src, args.deploy_min_photos)
        classes = sorted(manifest)
        n_photos = sum(len(g[0]) for g in manifest.values())
        tag = args.tag or f"deploy_{args.loss}_{args.aug}"
        base = ROOT / "runs" / tag
        print(f"{tag}: DEPLOY model -- {len(classes)} individuals, {n_photos} photos, "
              f"no held-out set, {args.epochs} epochs, device={device}", flush=True)
        summary = [train_one_fold(args, manifest, classes, None, base, device)]
        base.mkdir(parents=True, exist_ok=True)
        (base / "summary.json").write_text(json.dumps(
            {"tag": tag, "deploy": True, "n_individuals": len(classes),
             "n_photos": n_photos, "config": vars(args), "runs": summary},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\ndone -> {base/'model.pt'}", flush=True)
        print("Performance estimate for this model is the cross-validated figure "
              "in analysis/artifacts/cv_report.json; it is conservative, since each "
              "fold trained on 80% of the data and this model used 100%.", flush=True)
        return

    data = json.loads(FOLDS_JSON.read_text(encoding="utf-8"))
    manifest, k = data["folds"], data["k"]
    eval_classes = sorted(manifest)

    extra = {}
    if args.extra_identities:
        extra = collect_extra(ROOT / args.extra_src, set(eval_classes),
                              args.extra_min_photos)
    classes = eval_classes + sorted(extra)

    tag = args.tag or f"cv_{args.loss}_{args.aug}"
    base = ROOT / "runs" / tag
    folds = range(k) if args.all_folds else [args.fold]

    print(f"{tag}: {len(eval_classes)} evaluated penguins"
          + (f" + {len(extra)} train-only identities ({sum(len(v) for v in extra.values())} photos)"
             if extra else "")
          + f", {k}-fold, {args.epochs} epochs, device={device}", flush=True)
    summary = []
    for f in folds:
        print(f"  --- fold {f} ---", flush=True)
        summary.append(train_one_fold(args, manifest, classes, f,
                                      base / f"fold{f}", device, extra))

    base.mkdir(parents=True, exist_ok=True)
    (base / "summary.json").write_text(json.dumps(
        {"tag": tag, "config": vars(args), "folds": summary},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\ndone -> {base/'summary.json'}", flush=True)


if __name__ == "__main__":
    main()
