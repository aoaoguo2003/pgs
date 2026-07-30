# Results — 35 individuals, session-wise 5-fold cross-validation

1743 photographs, 35 individuals. Every photo is tested exactly once by a model that never saw its capture session.

All figures are **macro**: per-individual accuracy averaged with equal weight, so a bird with 18 photos counts as much as one with 291. Intervals are 95% bootstrap, resampling **capture sessions** within each bird (photos inside a burst are near-duplicates, so resampling photos would report an interval that is too narrow).

## 1. Closed-set identification (35 candidates)

| configuration | rank-1 | rank-5 | mAP | 1-NN rank-1 | |
|---|---|---|---|---|---|
| softmax + basic | 0.390 [0.359, 0.434] | 0.746 [0.709, 0.787] | 0.420 [0.394, 0.463] | 0.387 [0.355, 0.429] | baseline |
| softmax + strong | 0.530 [0.490, 0.585] | 0.809 [0.775, 0.842] | 0.533 [0.501, 0.585] | 0.510 [0.472, 0.565] |  |
| ArcFace + basic | 0.486 [0.447, 0.543] | 0.734 [0.706, 0.784] | 0.509 [0.475, 0.563] | 0.482 [0.444, 0.537] |  |
| ArcFace + strong | 0.559 [0.517, 0.610] | 0.782 [0.751, 0.823] | 0.581 [0.543, 0.636] | 0.561 [0.521, 0.612] | best |

*rank-1* = the single best-matching individual is correct. *rank-5* = the correct individual is among the five best-matching individuals (five distinct birds, not five photos). *mAP* = quality of the whole ranking over the 1394-photo gallery, the conventional re-ID companion to rank-1. *1-NN* = nearest single gallery photo rather than the class prototype.

## 2. CMC — how many candidates you must show

| rank k | softmax + basic | softmax + strong | ArcFace + basic | ArcFace + strong |
|---|---|---|---|---|
| 1 | 0.390 | 0.530 | 0.486 | 0.559 |
| 2 | 0.548 | 0.656 | 0.586 | 0.650 |
| 3 | 0.630 | 0.731 | 0.665 | 0.702 |
| 4 | 0.689 | 0.775 | 0.706 | 0.748 |
| 5 | 0.746 | 0.809 | 0.734 | 0.782 |
| 6 | 0.777 | 0.838 | 0.763 | 0.803 |
| 7 | 0.805 | 0.859 | 0.791 | 0.821 |
| 8 | 0.829 | 0.877 | 0.805 | 0.836 |
| 9 | 0.848 | 0.885 | 0.814 | 0.851 |
| 10 | 0.864 | 0.894 | 0.831 | 0.860 |

A five-candidate shortlist contains the right bird 78.2% of the time against 55.9% for a single answer — the basis for showing a keeper a shortlist rather than one name.

## 3. Colony-scale ranking (81 candidates)

| configuration | rank-1 (35 candidates) | rank-1 (81 candidates) | drop |
|---|---|---|---|
| softmax + basic | 0.390 | 0.224 | -0.166 |
| softmax + strong | 0.530 | 0.361 | -0.169 |
| ArcFace + basic | 0.486 | 0.364 | -0.122 |
| ArcFace + strong | 0.559 | 0.477 | -0.082 |

The queries are the same 1743 photos of the same 35 birds; only the candidate list grows, with the 46 unevaluable colony members added as distractors. **ArcFace degrades least** as the gallery grows, which is the regime a real colony is in.

## 4. Open-set — when the bird may not be enrolled

| configuration | DIR@FAR=1% | DIR@FAR=5% | DIR@FAR=10% |
|---|---|---|---|
| softmax + basic | 0.076 | 0.134 | 0.163 |
| softmax + strong | 0.086 | 0.195 | 0.252 |
| ArcFace + basic | 0.097 | 0.171 | 0.237 |
| ArcFace + strong | 0.123 | 0.237 | 0.312 |

Strangers are the 564 photographs of 46 colony members the models never trained on. DIR@FAR=x is the fraction of enrolled birds both correctly named *and* confident enough to be accepted, at the threshold where strangers are wrongly accepted x of the time. **Closed-set rank-1 of 0.559 falls to 0.123** — this is the figure that describes deployment readiness.

## 5. Attribution — which change did the work

| effect | rank-1 (35) | rank-1 (81) | mAP |
|---|---|---|---|
| augmentation alone | +0.141 [+0.105, +0.179] | +0.137 [+0.103, +0.174] | +0.113 [+0.087, +0.141] |
| ArcFace alone | +0.096 [+0.061, +0.139] | +0.140 [+0.110, +0.173] | +0.088 [+0.057, +0.124] |
| ArcFace given strong aug | +0.029 [-0.005, +0.060] **(n.s.)** | +0.116 [+0.082, +0.148] | +0.048 [+0.019, +0.072] |

**(n.s.)** = interval includes zero. Augmentation is the larger single lever; ArcFace's marginal contribution on top of it is invisible at 35 candidates but clear at 81 and on mAP, because metric learning shapes the embedding geometry rather than the top-1 call.

## 6. Accuracy by capture sessions per individual

| sessions | individuals | softmax + basic | softmax + strong | ArcFace + basic | ArcFace + strong |
|---|---|---|---|---|---|
| 3 | 8 | 0.081 | 0.195 | 0.135 | 0.186 |
| 4–6 | 13 | 0.423 | 0.547 | 0.503 | 0.618 |
| 7+ | 14 | 0.535 | 0.706 | 0.670 | 0.717 |

Excluding the 8 individuals with only 3 sessions, the remaining 27 reach 0.669. Metric learning lifts every bucket but cannot rescue the 3-session birds — that gap needs a camera, not a loss function.

## 7. Models behind these numbers

| purpose | location | trained on |
|---|---|---|
| softmax + basic | `runs/cv_softmax_basic/fold0..4/model.pt` | 5 models, ~80% of 1743 photos each |
| softmax + strong | `runs/cv_softmax_strong/fold0..4/model.pt` | 5 models, ~80% of 1743 photos each |
| ArcFace + basic | `runs/cv_arcface_basic/fold0..4/model.pt` | 5 models, ~80% of 1743 photos each |
| ArcFace + strong | `runs/cv_arcface_strong/fold0..4/model.pt` | 5 models, ~80% of 1743 photos each |
| **deployed** | `runs/deploy_arcface/model.pt` | 1 model, 79 individuals, 2304 photos, nothing held out |

The cross-validated figures estimate the *method*; the deployed model is retrained with the identical recipe on everything, and those figures are its conservative estimate (each fold saw 80% of the data, the deployed model 100%). Model weights are gitignored; training curves and every result JSON are tracked, so all of the above is reproducible.
