# -*- coding: utf-8 -*-
"""
Data-leakage audit for the penguin re-identification split.

`a.py` splits each penguin's photos by a plain random shuffle. Because most
photos come from burst sequences (DSC_2743...DSC_2749), near-identical frames
can land in train and test at the same time -- the model is then tested on
pictures it has effectively already seen, and the reported accuracy is
optimistic. This script measures how bad that is, in three passes:

  1. NEAR-DUPLICATES  For each test image, find the most similar gallery image
     of the same penguin using signals that are independent of the model:
     dHash Hamming distance, 32x32 pixel correlation (NCC), EXIF capture-time
     gap, and filename frame-number gap.

  2. SESSIONS  Pixel similarity only catches burst frames, not "same afternoon,
     same pool, different pose". A session is approximated as
     (filename prefix, run of frame numbers within --session-gap); we then ask
     how many test images share a session with a gallery image.

  3. IMPACT  Split the test set into LEAKY vs CLEAN and report exp1 softmax,
     exp3 1-NN and exp3 prototype accuracy on each half. The gap between the
     two halves is the inflation attributable to near-duplicates.

Run:
  D:/Anaconda/python.exe analysis/leakage_audit.py
  D:/Anaconda/python.exe analysis/leakage_audit.py --no-impact   # no torch needed
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
FRAME_RE = re.compile(r"^(.*?)(\d+)")
CROP_SUFFIX_RE = re.compile(r"(_box\d+|\s*copy)$", re.I)


# --------------------------------------------------------------------------
# signatures
# --------------------------------------------------------------------------
def dhash(img: Image.Image, size: int = 8) -> np.ndarray:
    """64-bit difference hash: True where a pixel is brighter than its right neighbour."""
    grey = img.convert("L").resize((size + 1, size), Image.LANCZOS)
    a = np.asarray(grey, dtype=np.int16)
    return (a[:, 1:] > a[:, :-1]).flatten()


def thumbnail_vector(img: Image.Image, size: int = 32) -> np.ndarray:
    """Mean-centred, unit-norm 32x32 greyscale vector; dot product = pixel NCC."""
    v = np.asarray(img.convert("L").resize((size, size), Image.LANCZOS), dtype=np.float32).flatten()
    v -= v.mean()
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def exif_datetime(img: Image.Image):
    """DateTimeOriginal / DateTimeDigitized / DateTime, whichever is present."""
    try:
        exif = img.getexif()
        for tag in (36867, 36868, 306):
            if tag in exif:
                return datetime.strptime(str(exif[tag]).strip(), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def session_key(filename: str):
    """(camera prefix, frame number) with crop suffixes stripped: IMG_0829_box1 -> ('img_', 829)."""
    stem = CROP_SUFFIX_RE.sub("", Path(filename).stem)
    m = FRAME_RE.match(stem)
    return (m.group(1).lower(), int(m.group(2))) if m else (stem.lower(), None)


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def list_split(data_dir: Path, splits):
    paths, labels = [], []
    for sp in splits:
        for cls_dir in sorted(p for p in (data_dir / sp).iterdir() if p.is_dir()):
            for f in sorted(cls_dir.iterdir()):
                if f.suffix.lower() in IMG_EXTS:
                    paths.append(f)
                    labels.append(cls_dir.name)
    return paths, labels


def signatures(paths):
    hashes, thumbs, times = [], [], []
    for p in paths:
        with Image.open(p) as im:
            im.load()
            hashes.append(dhash(im))
            thumbs.append(thumbnail_vector(im))
            times.append(exif_datetime(im))
    return np.stack(hashes), np.stack(thumbs), times


def percentiles(a, ps):
    return {f"p{p}": round(float(np.percentile(a, p)), 3) for p in ps}


# --------------------------------------------------------------------------
# pass 1 + 2
# --------------------------------------------------------------------------
def audit_duplicates(g_paths, g_labels, gH, gT, g_times,
                     q_paths, q_labels, qH, qT, q_times, args):
    by_class = defaultdict(list)
    for i, lab in enumerate(g_labels):
        by_class[lab].append(i)

    g_keys = defaultdict(list)
    for i, lab in enumerate(g_labels):
        g_keys[lab].append(session_key(g_paths[i].name))

    rows = []
    for i, (path, lab) in enumerate(zip(q_paths, q_labels)):
        idx = by_class.get(lab)
        if not idx:
            continue
        ham = (gH[idx] != qH[i]).sum(axis=1)
        ncc = gT[idx] @ qT[i]
        j_ham, j_ncc = int(np.argmin(ham)), int(np.argmax(ncc))
        nearest = idx[j_ham]

        time_gap = None
        if q_times[i] and g_times[nearest]:
            time_gap = abs((q_times[i] - g_times[nearest]).total_seconds())

        prefix, num = session_key(path.name)
        same_prefix = any(gp == prefix for gp, _ in g_keys[lab])
        frame_gaps = [abs(gn - num) for gp, gn in g_keys[lab]
                      if gp == prefix and gn is not None and num is not None]
        min_frame_gap = min(frame_gaps) if frame_gaps else None
        same_session = min_frame_gap is not None and min_frame_gap <= args.session_gap

        rows.append({
            "penguin": lab,
            "test_image": path.name,
            "min_hamming": int(ham.min()),
            "max_ncc": round(float(ncc.max()), 3),
            "nearest_by_hash": g_paths[nearest].name,
            "nearest_by_ncc": g_paths[idx[j_ncc]].name,
            "exif_time_gap_s": time_gap,
            "min_frame_gap": min_frame_gap,
            "same_camera_prefix": same_prefix,
            "same_session": same_session,
            "leaky": bool(ham.min() <= args.ham_thr or ncc.max() >= args.ncc_thr),
        })
    return rows


def sessions_per_penguin(g_paths, g_labels, q_paths, q_labels, gap):
    pooled = defaultdict(list)
    for p, lab in list(zip(g_paths, g_labels)) + list(zip(q_paths, q_labels)):
        pooled[lab].append(session_key(p.name))
    counts = {}
    for lab, keys in pooled.items():
        keys = sorted(k for k in keys if k[1] is not None)
        n, last = 0, None
        for prefix, num in keys:
            if last is None or prefix != last[0] or num - last[1] > gap:
                n += 1
            last = (prefix, num)
        counts[lab] = n
    return counts


# --------------------------------------------------------------------------
# pass 3
# --------------------------------------------------------------------------
def measure_impact(root, ckpt, g_paths, g_labels, q_paths, q_labels, leaky):
    """Accuracy of exp1 softmax / exp3 1-NN / exp3 prototype on leaky vs clean halves."""
    import torch
    import torch.nn as nn
    from torchvision import models, transforms

    sys.path.insert(0, str(root / "embedding_id"))
    from embedder import Embedder, l2_normalize

    embedder = Embedder(str(ckpt))
    G = embedder.embed_paths([str(p) for p in g_paths], verbose=False)
    Q = embedder.embed_paths([str(p) for p in q_paths], verbose=False)
    g_arr, q_arr = np.array(g_labels), np.array(q_labels)

    sims = Q @ G.T
    knn_pred = np.array([g_labels[j] for j in sims.argmax(1)])
    top5 = np.array([q_labels[i] in [g_labels[j] for j in np.argsort(-sims[i])[:5]]
                     for i in range(len(q_paths))])

    names = sorted(set(g_labels))
    protos = np.stack([l2_normalize(G[g_arr == n].mean(0, keepdims=True))[0]
                       for n in names]).astype("float32")
    proto_pred = np.array([names[j] for j in (Q @ protos.T).argmax(1)])

    ck = torch.load(ckpt, map_location="cpu", weights_only=False)
    classes = ck.get("class_names") or ck.get("classes") or names
    state = ck.get("model_state_dict") or ck.get("state_dict") or ck
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(classes))
    model.load_state_dict(state)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()
    tf = transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    softmax_pred = []
    with torch.no_grad():
        for k in range(0, len(q_paths), 32):
            batch = torch.stack([tf(Image.open(p).convert("RGB"))
                                 for p in q_paths[k:k + 32]]).to(device)
            softmax_pred += [classes[j] for j in model(batch).argmax(1).cpu().numpy()]
    softmax_pred = np.array(softmax_pred)

    clean = ~leaky

    def acc(mask, correct):
        return round(float(correct[mask].mean()), 4) if mask.sum() else None

    out = {}
    for name, correct in [("exp1_softmax_top1", softmax_pred == q_arr),
                          ("exp3_knn_top1", knn_pred == q_arr),
                          ("exp3_prototype_top1", proto_pred == q_arr),
                          ("exp3_knn_top5", top5)]:
        out[name] = {"all": acc(np.ones_like(leaky), correct),
                     "leaky": acc(leaky, correct),
                     "clean": acc(clean, correct)}
    return out, knn_pred


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default="penguins_dataset_split")
    ap.add_argument("--checkpoint", default="runs/exp1_baseline/best_model.pt")
    ap.add_argument("--gallery-splits", nargs="+", default=["train", "val"],
                    help="splits the model was fitted on / enrolled from")
    ap.add_argument("--query-split", default="test")
    ap.add_argument("--out-dir", default="analysis/artifacts")
    ap.add_argument("--ham-thr", type=int, default=10,
                    help="dHash Hamming distance at or below which images count as near-duplicates")
    ap.add_argument("--ncc-thr", type=float, default=0.85,
                    help="32x32 pixel correlation at or above which images count as near-duplicates")
    ap.add_argument("--session-gap", type=int, default=50,
                    help="frame-number distance within which two shots count as one session")
    ap.add_argument("--no-impact", action="store_true",
                    help="skip pass 3 (skips the torch dependency)")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent

    def resolve(p):
        return Path(p) if os.path.isabs(p) else root / p

    data_dir, ckpt, out_dir = map(resolve, (args.data_dir, args.checkpoint, args.out_dir))
    out_dir.mkdir(parents=True, exist_ok=True)

    g_paths, g_labels = list_split(data_dir, args.gallery_splits)
    q_paths, q_labels = list_split(data_dir, [args.query_split])
    print(f"gallery ({'+'.join(args.gallery_splits)}) = {len(g_paths)} images, "
          f"{len(set(g_labels))} penguins")
    print(f"query   ({args.query_split}) = {len(q_paths)} images")

    print("\nComputing image signatures ...", flush=True)
    gH, gT, g_times = signatures(g_paths)
    qH, qT, q_times = signatures(q_paths)
    exif_n = sum(1 for t in list(g_times) + list(q_times) if t)
    print(f"  EXIF timestamp coverage: {exif_n}/{len(g_times) + len(q_times)}")

    rows = audit_duplicates(g_paths, g_labels, gH, gT, g_times,
                            q_paths, q_labels, qH, qT, q_times, args)
    leaky = np.array([r["leaky"] for r in rows])
    ham = np.array([r["min_hamming"] for r in rows])
    ncc = np.array([r["max_ncc"] for r in rows])
    n = len(rows)

    print(f"\n=== 1. NEAR-DUPLICATES (n={n} test images) ===")
    print(f"  leaky (dHash<={args.ham_thr} or NCC>={args.ncc_thr}): "
          f"{int(leaky.sum())} ({leaky.mean():.1%})")
    print("  min-Hamming to nearest same-penguin gallery image "
          "(0=identical, 64=unrelated):")
    print("   ", percentiles(ham, (1, 5, 10, 25, 50, 75, 90)))
    print("  max pixel-NCC (1.0=identical):")
    print("   ", percentiles(ncc, (50, 75, 90, 95, 99)))

    gaps = [r["exif_time_gap_s"] for r in rows if r["exif_time_gap_s"] is not None]
    time_summary = {}
    if gaps:
        gaps = np.array(gaps)
        time_summary = {f"within_{t}s": round(float((gaps <= t).mean()), 3)
                        for t in (1, 3, 10, 60, 300)}
        print(f"  capture-time gap to nearest gallery image (n={len(gaps)} with EXIF): "
              f"{time_summary}")

    same_session = np.array([r["same_session"] for r in rows])
    same_prefix = np.array([r["same_camera_prefix"] for r in rows])
    sess_counts = sessions_per_penguin(g_paths, g_labels, q_paths, q_labels, args.session_gap)
    single = sorted(k for k, v in sess_counts.items() if v <= 2)

    print(f"\n=== 2. SESSION OVERLAP (session = prefix + frames within {args.session_gap}) ===")
    print(f"  test images sharing a camera prefix with the gallery: {same_prefix.mean():.1%}")
    print(f"  test images sharing a SESSION with the gallery      : {same_session.mean():.1%}")
    print(f"  median sessions per penguin: {statistics.median(sess_counts.values())}")
    print(f"  penguins with only 1-2 sessions ({len(single)}/{len(sess_counts)}): "
          f"{', '.join(single)}")
    print("  -> a session-disjoint split is impossible for those birds without new photos")

    impact = None
    if not args.no_impact:
        print("\nEmbedding + classifying for impact analysis ...", flush=True)
        impact, knn_pred = measure_impact(root, ckpt, g_paths, g_labels,
                                          q_paths, q_labels, leaky)
        for r, pred in zip(rows, knn_pred):
            r["knn_correct"] = bool(pred == r["penguin"])

        print(f"\n=== 3. IMPACT ON ACCURACY ===")
        print(f"{'':<24}{'ALL':>8}{'LEAKY':>9}{'CLEAN':>9}{'gap':>9}")
        print(f"{'n':<24}{n:>8}{int(leaky.sum()):>9}{int((~leaky).sum()):>9}")
        for name, v in impact.items():
            gap = v["leaky"] - v["clean"] if None not in (v["leaky"], v["clean"]) else float("nan")
            print(f"{name:<24}{v['all']:>8.3f}{v['leaky']:>9.3f}{v['clean']:>9.3f}{gap:>+9.3f}")
        print("\n  CLEAN is the honest same-session number; note from pass 2 that even it "
              "does\n  not measure cross-session (different day / lighting) generalisation.")

    csv_path = out_dir / "leakage_per_image.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    report = {
        "config": {"data_dir": str(data_dir), "gallery_splits": args.gallery_splits,
                   "query_split": args.query_split, "ham_thr": args.ham_thr,
                   "ncc_thr": args.ncc_thr, "session_gap": args.session_gap},
        "counts": {"gallery_images": len(g_paths), "query_images": n,
                   "penguins": len(set(g_labels)), "exif_coverage": exif_n},
        "near_duplicates": {
            "leaky_images": int(leaky.sum()), "leaky_fraction": round(float(leaky.mean()), 4),
            "min_hamming_percentiles": percentiles(ham, (1, 5, 10, 25, 50, 75, 90)),
            "max_ncc_percentiles": percentiles(ncc, (50, 75, 90, 95, 99)),
            "capture_time_gap": time_summary,
        },
        "sessions": {
            "same_prefix_fraction": round(float(same_prefix.mean()), 4),
            "same_session_fraction": round(float(same_session.mean()), 4),
            "median_sessions_per_penguin": statistics.median(sess_counts.values()),
            "penguins_with_le_2_sessions": single,
            "sessions_per_penguin": sess_counts,
        },
        "impact": impact,
    }
    json_path = out_dir / "leakage_report.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nSaved per-image CSV -> {csv_path}")
    print(f"Saved report        -> {json_path}")


if __name__ == "__main__":
    main()
