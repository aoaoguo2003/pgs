"""Capture-session census over the WHOLE 81-bird colony.

The cross-validation manifest only records sessions for the 44 birds that passed
the >=16-photograph filter. Objective 5 (a photographic standard for the
collection) needs the session count for every colony member, including the birds
that were never evaluable -- those are precisely the ones a collection standard
would have to fix.

Uses the same session rule as the evaluation (analysis/session_disjoint_eval.py:
same filename prefix, camera frame gap <= 50).
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from session_disjoint_eval import cluster_sessions  # noqa: E402

ROOT = "C:/Users/14773/Desktop/pgs"
SRC = os.path.join(ROOT, "penguins_data")
GAP = 50
TARGET = 4  # sessions per individual implied by the Results gradient

IMG = (".jpg", ".jpeg", ".png")

per_bird = {}
for bird in sorted(os.listdir(SRC)):
    d = os.path.join(SRC, bird)
    if not os.path.isdir(d):
        continue
    names = sorted(f for f in os.listdir(d) if f.lower().endswith(IMG))
    if not names:
        continue
    per_bird[bird] = (len(names), len(cluster_sessions(names, GAP)))

n_birds = len(per_bird)
n_photos = sum(p for p, _ in per_bird.values())
n_sessions = sum(s for _, s in per_bird.values())

print(f"colony: {n_birds} individuals, {n_photos} photographs, {n_sessions} capture sessions")
print()

dist = Counter(s for _, s in per_bird.values())
print("sessions per individual -> number of individuals")
cum = 0
for s in sorted(dist):
    cum += dist[s]
    print(f"  {s:2d} session(s): {dist[s]:2d} individuals   (cumulative {cum})")
print()

for thr in (1, 2, 3, 4, 7):
    n = sum(1 for _, s in per_bird.values() if s >= thr)
    print(f"individuals with >= {thr} sessions: {n:2d} of {n_birds}  ({100*n/n_birds:.0f}%)")
print()

deficit = {b: TARGET - s for b, (_, s) in per_bird.items() if s < TARGET}
print(f"To bring EVERY colony member to >= {TARGET} capture sessions:")
print(f"  individuals short of the target : {len(deficit)} of {n_birds}")
print(f"  additional capture occasions    : {sum(deficit.values())} individual-sessions")
print()

for per_day in (10, 15, 20):
    days = -(-sum(deficit.values()) // per_day)
    print(f"  at {per_day:2d} birds photographed per outing -> {days} separate outings")
print()
print("(Outings must fall on different days: the gradient is driven by variation")
print(" between encounters, which repeat visits on one day would not supply.)")
print()

short = sorted(deficit.items(), key=lambda kv: -kv[1])
print("Individuals needing the most new sessions (top 15):")
for b, d in short[:15]:
    ph, se = per_bird[b]
    print(f"  {b:16s} has {se} session(s), {ph:3d} photograph(s) -> needs {d} more")
