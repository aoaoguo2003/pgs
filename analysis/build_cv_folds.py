# -*- coding: utf-8 -*-
"""
Build session-wise K-fold cross-validation folds for the penguin re-ID dataset.

The unit dealt into folds is a capture SESSION, never a single photo, so a burst
is never split across train and test. Each penguin's sessions are dealt
independently: largest session first, always into whichever fold currently holds
the fewest of that penguin's images. Across the K rounds every photo is used as
a test query exactly once, by a model that never saw its session.

A penguin with fewer than K sessions simply leaves some folds empty; in those
rounds all of its photos sit in train. That costs nothing, because per-penguin
accuracy is computed once at the end over the pooled predictions from all rounds.

No images are copied. The manifest lists source paths, and the training script
reads it directly -- K physical dataset copies would cost ~3 GB for nothing.

Run:
  D:/Anaconda/python.exe analysis/build_cv_folds.py            # build + print table
  D:/Anaconda/python.exe analysis/build_cv_folds.py --k 3
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def deal_all(per_sessions, k):
    """Deal every penguin's sessions into k folds, balancing on two levels.

    Per session, pick the fold minimising (images this penguin already has there,
    then images ALL penguins have there). The primary key spreads each bird
    across folds so it is tested in as many rounds as it has sessions; the
    secondary key stops every bird's largest session from piling into fold 0,
    which would leave that fold with far less training data than the others.

    Penguins are processed largest-total first so the lumpy birds -- the ones
    with a single dominant burst -- get first pick of the emptiest folds.
    """
    global_sizes = [0] * k
    out = {}
    for pen in sorted(per_sessions, key=lambda p: -sum(len(s) for s in per_sessions[p])):
        folds = [[] for _ in range(k)]
        pen_sizes = [0] * k
        for s in sorted(per_sessions[pen], key=len, reverse=True):
            j = min(range(k), key=lambda i: (pen_sizes[i], global_sizes[i]))
            folds[j].extend(s)
            pen_sizes[j] += len(s)
            global_sizes[j] += len(s)
        out[pen] = folds
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="penguins_dataset_split")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--session-gap", type=int, default=50)
    ap.add_argument("--min-sessions", type=int, default=3)
    ap.add_argument("--out", default="analysis/artifacts/cv_folds.json")
    args = ap.parse_args()

    from session_disjoint_eval import cluster_sessions

    src = ROOT / args.src
    per = defaultdict(list)
    for sp in ("train", "val", "test"):
        for cls_dir in sorted(p for p in (src / sp).iterdir() if p.is_dir()):
            for f in sorted(cls_dir.iterdir()):
                if f.suffix.lower() in IMG_EXTS:
                    per[cls_dir.name].append(f)

    per_sessions, excluded = {}, []
    for pen, files in sorted(per.items()):
        sessions = cluster_sessions([f.name for f in files], args.session_gap)
        if len(sessions) < args.min_sessions:
            excluded.append((pen, len(sessions)))
            continue
        per_sessions[pen] = sessions

    dealt = deal_all(per_sessions, args.k)
    manifest, rows, sess_of = {}, [], {}
    for pen, folds in sorted(dealt.items()):
        files = per[pen]
        manifest[pen] = [[str(files[i].relative_to(ROOT)) for i in fold] for fold in folds]
        rows.append((pen, len(per_sessions[pen]), len(files), [len(f) for f in folds]))
        # Which session each photo came from. Confidence intervals must resample
        # SESSIONS, not photos: photos inside one burst are near-duplicates, so
        # photo-level resampling treats correlated samples as independent and
        # reports an interval that is too narrow.
        for si, sess in enumerate(per_sessions[pen]):
            for i in sess:
                sess_of[str(files[i].relative_to(ROOT))] = f"{pen}#{si}"

    # ---- table -----------------------------------------------------------
    k = args.k
    head = "".join(f"{'F'+str(i+1):>6}" for i in range(k))
    print(f"Session-wise {k}-fold split  "
          f"(F{'/'.join(str(i+1) for i in range(k))} = images tested in that round)\n")
    print(f"{'penguin':<14}{'sess':>5}{'total':>7}{head}{'test range':>13}")
    print("-" * (14 + 5 + 7 + 6 * k + 13))
    for pen, ns, tot, sz in sorted(rows, key=lambda r: r[2]):
        cells = "".join(f"{v:>6}" for v in sz)
        print(f"{pen:<14}{ns:>5}{tot:>7}{cells}{f'{min(sz)}-{max(sz)}':>13}")

    print("-" * (14 + 5 + 7 + 6 * k + 13))
    totals = [sum(r[3][i] for r in rows) for i in range(k)]
    grand = sum(totals)
    print(f"{'TEST imgs':<14}{'':>5}{grand:>7}" + "".join(f"{v:>6}" for v in totals))
    print(f"{'TRAIN imgs':<14}{'':>5}{'':>7}" + "".join(f"{grand - v:>6}" for v in totals))
    print(f"{'train share':<14}{'':>5}{'':>7}"
          + "".join(f"{(grand - v) / grand:>6.0%}" for v in totals))

    n_empty = sum(1 for r in rows for v in r[3] if v == 0)
    print(f"\npenguins: {len(rows)} included, {len(excluded)} excluded "
          f"(<{args.min_sessions} sessions): {', '.join(p for p, _ in excluded)}")
    print(f"every photo is tested exactly once: {grand} total")
    print(f"empty cells (penguin has fewer than {k} sessions): {n_empty} "
          f"-- those rounds keep all of that bird's photos in train")

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"k": k, "session_gap": args.session_gap, "min_sessions": args.min_sessions,
         "src": args.src, "folds": manifest, "session_of_photo": sess_of},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved -> {out}")


if __name__ == "__main__":
    main()
