"""Is accuracy driven by capture SESSIONS or just by photo COUNT?

Both are per-individual properties and they are correlated, so the Results claim
"accuracy tracks sessions" needs a partial correlation, not a bucket table.
Reads only tracked artifacts; no model is loaded.
"""
import json, math, os
from collections import defaultdict

ROOT = "C:/Users/14773/Desktop/pgs"
folds = json.load(open(os.path.join(ROOT, "analysis/artifacts/cv_folds.json")))
sop = folds["session_of_photo"]
report = json.load(open(os.path.join(ROOT, "analysis/artifacts/cv_report.json")))

sess = defaultdict(set)
for path, s in sop.items():
    bird = path.replace(os.sep, "/").replace("\\", "/").split("/")[-2]
    sess[bird].add(s)


def pearson(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def rankify(v):
    """Average ranks, ties shared -> Spearman via Pearson on ranks."""
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def partial(r_xy, r_xz, r_yz):
    return (r_xy - r_xz * r_yz) / math.sqrt((1 - r_xz ** 2) * (1 - r_yz ** 2))


def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 300, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        c = 1 + aa / c
        if abs(d) < FPMIN:
            d = FPMIN
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        c = 1 + aa / c
        if abs(d) < FPMIN:
            d = FPMIN
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1 / d
        de = d * c
        h *= de
        if abs(de - 1) < EPS:
            break
    return h


def betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lb = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(a * math.log(x) + b * math.log(1 - x) - lb)
    if x < (a + 1) / (a + b + 2):
        return front * betacf(a, b, x) / a
    return 1 - math.exp(b * math.log(1 - x) + a * math.log(x) - lb) * betacf(b, a, 1 - x) / b


def p_two_sided(r, n, n_controls):
    df = n - 2 - n_controls
    if abs(r) >= 1:
        return 0.0
    t = r * math.sqrt(df / (1 - r * r))
    return betai(df / 2, 0.5, df / (df + t * t))


for cfg in ["cv_softmax_basic", "cv_arcface_strong"]:
    rep = report[cfg]
    acc, nimg = rep["per_class"], rep["n_images_per_class"]
    birds = sorted(acc)
    n = len(birds)
    A = rankify([acc[b] for b in birds])
    S = rankify([len(sess[b]) for b in birds])
    P = rankify([nimg[b] for b in birds])

    r_AS, r_AP, r_SP = pearson(A, S), pearson(A, P), pearson(S, P)
    pAS = partial(r_AS, r_AP, r_SP)
    pAP = partial(r_AP, r_AS, r_SP)

    print(f"\n=== {cfg}   (n = {n} individuals) ===")
    print(f"  Spearman  accuracy ~ sessions        {r_AS:+.3f}  (p = {p_two_sided(r_AS, n, 0):.4f})")
    print(f"  Spearman  accuracy ~ photographs     {r_AP:+.3f}  (p = {p_two_sided(r_AP, n, 0):.4f})")
    print(f"  Spearman  sessions ~ photographs     {r_SP:+.3f}")
    print(f"  PARTIAL   accuracy ~ sessions | photos     {pAS:+.3f}  (p = {p_two_sided(pAS, n, 1):.4f})")
    print(f"  PARTIAL   accuracy ~ photos | sessions     {pAP:+.3f}  (p = {p_two_sided(pAP, n, 1):.4f})")

rep = report["cv_arcface_strong"]
acc, nimg = rep["per_class"], rep["n_images_per_class"]
print("\nFew sessions despite many photographs (the cases that separate the two):")
for b in sorted(acc, key=lambda b: (len(sess[b]), -nimg[b]))[:10]:
    print(f"  {b:14s} sessions={len(sess[b]):2d}  photos={nimg[b]:3d}  acc={acc[b]:.3f}")
print("\nMany sessions, few photographs:")
for b in sorted(acc, key=lambda b: (-len(sess[b]), nimg[b]))[:6]:
    print(f"  {b:14s} sessions={len(sess[b]):2d}  photos={nimg[b]:3d}  acc={acc[b]:.3f}")
