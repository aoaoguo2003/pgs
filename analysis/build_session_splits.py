# -*- coding: utf-8 -*-
"""
Build two train/val/test datasets over the SAME penguins and SAME images, so a
retrained model can be compared fairly:

  A. session-disjoint  -- whole capture sessions are assigned to exactly one of
     train/val/test, so test (and val) sessions are never seen during training.
  B. random-control    -- identical per-penguin train/val/test COUNTS as A, but
     images assigned at random (ignoring sessions), i.e. the current a.py style.

Any test-accuracy gap between a model trained on A and one trained on B is the
cost of cross-session generalisation, with class count and data volume held
fixed. Only penguins with >=3 sessions are included (need one session per split).

Output (gitignored):
  penguins_dataset_split_session_disjoint/{train,val,test}/<penguin>/*
  penguins_dataset_split_session_random/{train,val,test}/<penguin>/*

Run:
  D:/Anaconda/python.exe analysis/build_session_splits.py
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from collections import defaultdict
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def assign_sessions_3way(sessions, targets=(0.70, 0.15, 0.15)):
    """Assign whole sessions to (train, val, test) by greedy deficit; each split >=1 session."""
    n_total = sum(len(s) for s in sessions)
    order = sorted(range(len(sessions)), key=lambda s: -len(sessions[s]))
    buckets = {0: [], 1: [], 2: []}          # 0=train, 1=val, 2=test
    counts = {0: 0, 1: 0, 2: 0}
    for s in order:
        # split whose share is furthest below its target
        k = max((0, 1, 2), key=lambda b: targets[b] - counts[b] / n_total)
        buckets[k].append(s); counts[k] += len(sessions[s])
    # guarantee val and test each have at least one session
    for need in (1, 2):
        if not buckets[need]:
            donor = max((0, 1, 2), key=lambda b: len(buckets[b]))
            s = min(buckets[donor], key=lambda x: len(sessions[x]))
            buckets[donor].remove(s); buckets[need].append(s); counts[need] += len(sessions[s])
    return {name: [i for s in buckets[b] for i in sessions[s]]
            for name, b in (("train", 0), ("val", 1), ("test", 2))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="penguins_dataset_split")
    ap.add_argument("--session-gap", type=int, default=50)
    ap.add_argument("--min-sessions", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    src = root / args.src
    sys.path.insert(0, str(root / "analysis"))
    from session_disjoint_eval import cluster_sessions

    out_sd = root / "penguins_dataset_split_session_disjoint"
    out_rnd = root / "penguins_dataset_split_session_random"
    for out in (out_sd, out_rnd):
        if out.exists():
            shutil.rmtree(out)

    # pool every image per penguin
    per = defaultdict(list)
    for sp in ("train", "val", "test"):
        for cls_dir in sorted(p for p in (src / sp).iterdir() if p.is_dir()):
            for f in sorted(cls_dir.iterdir()):
                if f.suffix.lower() in IMG_EXTS:
                    per[cls_dir.name].append(f)

    rng = random.Random(args.seed)
    stats, totals = {}, defaultdict(lambda: defaultdict(int))
    included, excluded = [], []
    for pen, files in sorted(per.items()):
        names = [f.name for f in files]
        sessions = cluster_sessions(names, args.session_gap)
        if len(sessions) < args.min_sessions:
            excluded.append((pen, len(sessions)))
            continue
        included.append(pen)

        sd = assign_sessions_3way(sessions)
        n = {k: len(v) for k, v in sd.items()}

        # random-control: same counts, shuffled image assignment
        idx = list(range(len(files)))
        rng.shuffle(idx)
        rnd = {"train": idx[:n["train"]],
               "val": idx[n["train"]:n["train"] + n["val"]],
               "test": idx[n["train"] + n["val"]:]}

        for split in ("train", "val", "test"):
            for tag, out, sel in (("sd", out_sd, sd[split]), ("rnd", out_rnd, rnd[split])):
                dst = out / split / pen
                dst.mkdir(parents=True, exist_ok=True)
                for i in sel:
                    shutil.copy2(files[i], dst / files[i].name)
                totals[tag][split] += len(sel)
        stats[pen] = {"sessions": len(sessions), **n}

    print(f"included penguins (>= {args.min_sessions} sessions): {len(included)}")
    print(f"excluded: {len(excluded)} -> {', '.join(f'{p}({s})' for p, s in excluded)}")
    print(f"\n{'split':<8}{'session-disjoint':>18}{'random-control':>16}")
    for split in ("train", "val", "test"):
        print(f"{split:<8}{totals['sd'][split]:>18}{totals['rnd'][split]:>16}")
    tot = sum(totals["sd"].values())
    print(f"{'total':<8}{tot:>18}{sum(totals['rnd'].values()):>16}")
    print(f"\ntest fraction: {totals['sd']['test'] / tot:.1%}  "
          f"val fraction: {totals['sd']['val'] / tot:.1%}")

    report = {"included": included, "excluded": dict(excluded),
              "totals": {k: dict(v) for k, v in totals.items()},
              "per_penguin": stats}
    (root / "analysis" / "artifacts").mkdir(parents=True, exist_ok=True)
    (root / "analysis" / "artifacts" / "session_split_manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2))
    print("\nsaved manifest -> analysis/artifacts/session_split_manifest.json")
    print(f"datasets -> {out_sd.name} , {out_rnd.name}")


if __name__ == "__main__":
    main()
