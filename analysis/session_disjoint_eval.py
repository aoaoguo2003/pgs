# -*- coding: utf-8 -*-
"""
Session-disjoint re-evaluation of the embedding retrieval pipeline (exp3).

The reported retrieval accuracy (prototype top-1 0.959) uses a random photo
split, but 97.8% of test images share a capture SESSION with a gallery image
(see leakage_audit.py). That number therefore measures same-session recall, not
"recognise this bird on a different day".

This script re-partitions each penguin's photos by whole session -- every shot
from one shoot goes entirely to the gallery OR entirely to the query, never
both -- and recomputes 1-NN / prototype / top-5 accuracy. The gap against the
random split, measured on the SAME penguins, is the honest cost of cross-session
generalisation.

A session needs >=2 sessions per bird to be evaluable, so only penguins with at
least two sessions are included; the rest are reported as excluded.

Caveat: the ResNet18 feature extractor was trained (exp1) on the random split,
so it has seen every individual. This measures gallery/query (enrolment)
generalisation, not fully end-to-end session generalisation; the latter needs
retraining exp1 on session-disjoint data.

Run:
  D:/Anaconda/python.exe analysis/session_disjoint_eval.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
FRAME_RE = re.compile(r"^(.*?)(\d+)")
CROP_SUFFIX_RE = re.compile(r"(_box\d+|\s*copy)$", re.I)


def session_key(filename: str):
    stem = CROP_SUFFIX_RE.sub("", Path(filename).stem)
    m = FRAME_RE.match(stem)
    return (m.group(1).lower(), int(m.group(2))) if m else (stem.lower(), None)


def cluster_sessions(names, gap: int):
    """Group a penguin's filenames into sessions: same prefix + frame gap <= gap."""
    def sort_key(i):
        prefix, num = session_key(names[i])
        return (prefix, num if num is not None else -1)

    keyed = sorted(range(len(names)), key=sort_key)
    sessions, cur, last = [], [], None
    for i in keyed:
        prefix, num = session_key(names[i])
        if last is None or prefix != last[0] or num is None or last[1] is None \
                or num - last[1] > gap:
            if cur:
                sessions.append(cur)
            cur = [i]
        else:
            cur.append(i)
        last = (prefix, num)
    if cur:
        sessions.append(cur)
    return sessions


def assign_sessions(sessions, test_frac):
    """Largest session always to gallery; fill query with whole sessions up to test_frac."""
    order = sorted(range(len(sessions)), key=lambda s: -len(sessions[s]))
    n_total = sum(len(s) for s in sessions)
    gallery_s = {order[0]}                    # largest -> gallery
    query_s, q_count = set(), 0
    for s in order[1:]:
        if q_count < test_frac * n_total:
            query_s.add(s); q_count += len(sessions[s])
        else:
            gallery_s.add(s)
    g_idx = [i for s in gallery_s for i in sessions[s]]
    q_idx = [i for s in query_s for i in sessions[s]]
    return g_idx, q_idx, len(gallery_s), len(query_s)


def metrics(G, g_lab, Q, q_lab, names, l2n):
    """1-NN top1, prototype top1, top5 for a gallery/query embedding set."""
    g_lab, q_lab = np.array(g_lab), np.array(q_lab)
    sims = Q @ G.T
    knn = np.array([g_lab[j] for j in sims.argmax(1)])
    top5 = np.array([q_lab[i] in [g_lab[j] for j in np.argsort(-sims[i])[:5]]
                     for i in range(len(q_lab))])
    protos = np.stack([l2n(G[g_lab == n].mean(0, keepdims=True))[0] for n in names]).astype("float32")
    proto = np.array([names[j] for j in (Q @ protos.T).argmax(1)])
    return {
        "knn_top1": round(float((knn == q_lab).mean()), 4),
        "prototype_top1": round(float((proto == q_lab).mean()), 4),
        "top5": round(float(top5.mean()), 4),
        "n_query": int(len(q_lab)),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default="penguins_dataset_split")
    ap.add_argument("--checkpoint", default="runs/exp1_baseline/best_model.pt")
    ap.add_argument("--out-dir", default="analysis/artifacts")
    ap.add_argument("--session-gap", type=int, default=50)
    ap.add_argument("--test-frac", type=float, default=0.30)
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent

    def resolve(p):
        return Path(p) if os.path.isabs(p) else root / p

    data_dir, ckpt, out_dir = map(resolve, (args.data_dir, args.checkpoint, args.out_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root / "embedding_id"))
    from embedder import Embedder, l2_normalize

    # ---- pool every photo per penguin, remembering its original split folder ----
    per = defaultdict(list)   # penguin -> list of (path, orig_split)
    for sp in ("train", "val", "test"):
        for cls_dir in sorted(p for p in (data_dir / sp).iterdir() if p.is_dir()):
            for f in sorted(cls_dir.iterdir()):
                if f.suffix.lower() in IMG_EXTS:
                    per[cls_dir.name].append((f, sp))

    # ---- build session-disjoint and random assignments over the SAME penguin subset ----
    qualifying, excluded = [], []
    for pen, items in per.items():
        names = [f.name for f, _ in items]
        sessions = cluster_sessions(names, args.session_gap)
        if len(sessions) < 2:
            excluded.append((pen, len(sessions)))
        else:
            qualifying.append(pen)
    qualifying.sort()

    print(f"penguins total (with >=1 photo): {len(per)}")
    print(f"qualifying (>=2 sessions): {len(qualifying)}")
    print(f"excluded (<2 sessions): {len(excluded)} -> "
          f"{', '.join(f'{p}({s})' for p, s in sorted(excluded))}")

    # embed every photo of every qualifying penguin once
    all_paths, all_pen = [], []
    span = {}
    for pen in qualifying:
        start = len(all_paths)
        for f, sp in per[pen]:
            all_paths.append(str(f)); all_pen.append(pen)
        span[pen] = (start, len(all_paths))

    print(f"\nEmbedding {len(all_paths)} images from {len(qualifying)} penguins ...", flush=True)
    emb = Embedder(str(ckpt))
    E = emb.embed_paths(all_paths, verbose=False)

    # session-disjoint split
    sd_g, sd_gl, sd_q, sd_ql = [], [], [], []
    # random-split (original folders) restricted to the same subset
    rnd_g, rnd_gl, rnd_q, rnd_ql = [], [], [], []
    split_stats = {}
    for pen in qualifying:
        s, e = span[pen]
        items = per[pen]
        names = [f.name for f, _ in items]
        sessions = cluster_sessions(names, args.session_gap)
        g_local, q_local, ng, nq = assign_sessions(sessions, args.test_frac)
        for i in g_local:
            sd_g.append(E[s + i]); sd_gl.append(pen)
        for i in q_local:
            sd_q.append(E[s + i]); sd_ql.append(pen)
        # random baseline from original folders
        for i, (f, sp) in enumerate(items):
            if sp in ("train", "val"):
                rnd_g.append(E[s + i]); rnd_gl.append(pen)
            else:
                rnd_q.append(E[s + i]); rnd_ql.append(pen)
        split_stats[pen] = {"sessions": len(sessions), "gallery_sessions": ng,
                            "query_sessions": nq, "images": len(items)}

    sd_G, sd_Q = np.stack(sd_g), np.stack(sd_q)
    rnd_G, rnd_Q = np.stack(rnd_g), np.stack(rnd_q)

    sd = metrics(sd_G, sd_gl, sd_Q, sd_ql, qualifying, l2_normalize)
    rnd = metrics(rnd_G, rnd_gl, rnd_Q, rnd_ql, qualifying, l2_normalize)

    print(f"\n=== Retrieval accuracy on the SAME {len(qualifying)} penguins ===")
    print(f"{'metric':<18}{'RANDOM split':>15}{'SESSION-disjoint':>19}{'drop':>9}")
    for k in ("prototype_top1", "knn_top1", "top5"):
        print(f"{k:<18}{rnd[k]:>15.3f}{sd[k]:>19.3f}{rnd[k] - sd[k]:>+9.3f}")
    print(f"{'n_query images':<18}{rnd['n_query']:>15}{sd['n_query']:>19}")
    print("\n  RANDOM = original folders (same-session leakage present).")
    print("  SESSION = whole sessions held out; frozen exp1 extractor (see caveat in header).")

    report = {
        "config": {"session_gap": args.session_gap, "test_frac": args.test_frac,
                   "checkpoint": str(ckpt)},
        "penguins_total": len(per),
        "penguins_qualifying": len(qualifying),
        "penguins_excluded": [{"penguin": p, "sessions": s} for p, s in sorted(excluded)],
        "random_split": rnd,
        "session_disjoint": sd,
        "drop": {k: round(rnd[k] - sd[k], 4) for k in ("prototype_top1", "knn_top1", "top5")},
        "per_penguin_split": split_stats,
        "caveat": "Frozen exp1 extractor trained on the random split; measures "
                  "enrolment (gallery/query) generalisation, not end-to-end.",
    }
    out = out_dir / "session_disjoint_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nSaved report -> {out}")


if __name__ == "__main__":
    main()
