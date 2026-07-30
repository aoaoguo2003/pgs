# Penguin Individual Re-Identification

**English** | [中文](README.zh-CN.md)

Given a photo of a **Humboldt penguin**, identify **which individual** it is (individual identity, not species). The end goal: a visitor takes one photo and instantly learns which specific penguin it is, plus that penguin's name, traits, and habits. All individuals in this project are Humboldt penguins from a single colony.

The project is evolving from a **classification baseline** into an **embedding-retrieval + RAG** system — turning each photo into a vector, matching it against a vector database, and using an LLM to generate a grounded description of the identified penguin. A **data-leakage audit** ([§5](#5-data-leakage-audit--cross-session-evaluation)) found the original headline inflated by same-session camera bursts shared between train and test. Under session-wise cross-validation ([§6](#6-cross-validated-metric-learning)) the current identification accuracy is **macro top-1 0.559** using ArcFace metric learning, against **0.390** for the softmax baseline. All accuracies in this document are **macro** — each individual weighted equally, regardless of how many photos it has. The profile/RAG layer and a conversational UI are the remaining work.

---

## Table of Contents
- [1. Dataset](#1-dataset)
- [2. Completed Experiments](#2-completed-experiments)
- [3. Experiment Record Figures](#3-experiment-record-figures)
- [4. Key Findings](#4-key-findings)
- [5. Data Leakage Audit & Cross-Session Evaluation](#5-data-leakage-audit--cross-session-evaluation)
- [6. Cross-Validated Metric Learning](#6-cross-validated-metric-learning)
- [7. Flagship Plan: Embedding Retrieval + RAG](#7-flagship-plan-embedding-retrieval--rag)
- [8. Repo Structure](#8-repo-structure)
- [9. Reproduce](#9-reproduce)

---

## 1. Dataset

- Raw data `penguins_data/`: **81 individuals, 2307 photos**, image counts ranging from 1 to 291 per bird — a **severe long-tail imbalance**.
- Filtered to the **44 individuals with ≥ 16 images** (`penguin_image_count_summary.csv`, `selected=True`); the remaining 37 (≤15 images) are too sparse to train and are held out for now.
- Of those 44, **35 have ≥ 3 distinct capture sessions** and are the individuals used in every session-disjoint evaluation ([§5](#5-data-leakage-audit--cross-session-evaluation), [§6](#6-cross-validated-metric-learning)). A session is a burst of frames from one shoot, detected from filename prefix and frame numbering.
- Split per individual into train / val / test: `penguins_dataset_split/`.
- Belly-crop variant (produced by the belly detector): `penguins_dataset_split_belly_by_yoloV8/`.

> Even within the selected 44, counts run from 291 (Medici) down to ~16 — an ~18× max/min gap. This imbalance is the root cause of most downstream difficulty. See [Figure 05](#3-experiment-record-figures).
>
> **Coverage is the harder limit than accuracy:** 37 of the colony's 81 birds are not in the system at all, and cannot be identified at any accuracy until they are photographed.

## 2. Completed Experiments

| Experiment | Input | Model | Epochs | best val acc | **test acc** |
|---|---|---|---|---|---|
| **exp1 baseline** | full body | ResNet18 (transfer) | 29 (early-stop, cap 30) | 0.907 | **0.950** |
| **exp2 belly** | belly crop | ResNet18 (transfer) | 39 (early-stop, cap 50) | 0.867 | 0.866 |
| **belly detector** | full body | YOLOv8s detection | 98 | mAP@50 ≈ 0.98 | mAP@50-95 ≈ 0.60 |
| **exp3 embedding retrieval** | full body | ResNet18 features + FAISS (no training) | — | — | **0.959** (prototype) / 0.947 (1-NN) / 0.978 (top-5) |

> ⚠️ **Leakage caveat:** the exp1 (0.950) and exp3 (0.959) accuracies above use a **random split** and are **per-image**. A later audit found same-session camera bursts leak into the test set, inflating these numbers. Under a session-disjoint split the same pipeline scores **macro top-1 0.389** ([§5](#5-data-leakage-audit--cross-session-evaluation)); with ArcFace metric learning and 5-fold cross-validation it reaches **0.559** ([§6](#6-cross-validated-metric-learning)). Treat this section as a historical record, not as current performance.

Shared pipeline:
- `torchvision.datasets.ImageFolder` loading
- Transfer learning (ImageNet-pretrained ResNet18)
- Imbalance handling: `WeightedRandomSampler` + class-weighted `CrossEntropyLoss`
- Best checkpoint by val accuracy; final test evaluation with prediction CSV export

**exp1 (full body)** — test accuracy **0.950**, best val 0.907 (epoch 21). Per-class results ([Figure 04](#3-experiment-record-figures)) show high-support individuals (Cooper n=20, Ron_burgundy n=29, Medici n=44) near-perfect; errors concentrate on classes with only 3–5 test samples.

**exp2 (belly crop)** — test accuracy **0.866**, clearly **below** the full-body 0.950. Its val loss stays consistently higher ([Figure 01](#3-experiment-record-figures), right) — worse generalization.

**belly detector (YOLOv8s)** — 98 epochs, val **mAP@50 ≈ 0.98 / mAP@50-95 ≈ 0.60**, precision/recall ~0.95 ([Figure 03](#3-experiment-record-figures)). Weights: `runs/detect/runs/belly_detector/exp1/weights/best.pt`. Detection is good, but cropping **discards identity cues** (face, chest band, body proportions) and detector errors propagate downstream — which explains why exp2 is worse.

**exp3 (embedding retrieval — the CNN route of the flagship plan)** — reuse the exp1 ResNet18 as a **frozen 512-d feature extractor** (drop the classification head), enroll all train+val images into a **FAISS** vector store, and identify test photos by nearest-neighbor / class-prototype search. **No new training.** Result: prototype (class-mean) top-1 **0.959**, 1-NN top-1 0.947, top-5 0.978 — i.e. retrieval **matches/slightly beats** the softmax classifier (0.950) while giving an enrollable vector DB (new individuals just get added, no retraining). Code: `embedding_id/` (`embedder.py`, `build_and_eval.py`, `identify.py`). This is the working core of the `identify_penguin` agent tool.

## 3. Experiment Record Figures

Figures 01–05 cover the classification experiments and are regenerated from each run's logs by `plot_experiments.py`. Figures **06–11** cover the leakage audit and the cross-validated evaluation; they are regenerated from the JSON artifacts by `analysis/plot_figures.py` and appear inline in [§5](#5-data-leakage-audit--cross-session-evaluation) and [§6](#6-cross-validated-metric-learning). Both scripts write to `figures/`.

**Fig 01 — Classifier training curves (full body vs belly)**
![training curves](figures/01_classifier_training_curves.png)

**Fig 02 — Final 44-class test accuracy**
![accuracy comparison](figures/02_test_accuracy_comparison.png)

**Fig 03 — Belly detector (YOLOv8s) validation metrics**
![detector metrics](figures/03_belly_detector_map.png)

**Fig 04 — exp1 per-class test accuracy (sorted; n = support samples)**
![per-class accuracy](figures/04_exp1_per_class_accuracy.png)

**Fig 05 — Per-individual image counts (blue = selected/trainable, grey = dropped)**
![dataset distribution](figures/05_dataset_distribution.png)

## 4. Key Findings

1. **Full body > belly crop (0.950 vs 0.866).** Identity signal is not only in the belly — face pattern, chest band, and body proportions all carry information. Cropping too tightly discards it, and detector error adds noise.
2. **Training/collection standard = full-body frontal photos.** No need to force a clean, complete belly.
3. **Front only.** A penguin's back is a large, uniform dark region, nearly identical across individuals; mixing front+back inflates intra-class variance. A production system should ask the visitor to re-shoot "non-frontal" photos rather than force an identity.
4. **Data is the binding constraint — in two distinct ways.**
   - **Coverage.** Only 44 of the colony's 81 individuals have enough photos to train on, and 35 have enough capture sessions to evaluate. The other 37 are absent from the system entirely; no algorithm addresses that.
   - **Session diversity.** Among the 35, accuracy tracks *capture sessions per bird* rather than photo count: 0.19 for birds with 3 sessions versus 0.72 for birds with 7+ ([§6](#6-cross-validated-metric-learning)). Extra frames from the same burst do not help; photographs on a new day, in new light, do.
   
   The model side is nevertheless **not exhausted**: on birds that already have ≥4 sessions, changing only the training objective (softmax → ArcFace) moved accuracy from 0.481 to 0.669. Data and method are complementary levers, not alternatives.

## 5. Data Leakage Audit & Cross-Session Evaluation

The dataset contains many **burst sequences** — same camera, same moment, consecutive frames (e.g. `DSC_2743…2749`). Because `a.py` splits each individual's photos **at random**, near-duplicate frames from one burst can land in train and test at the same time; the model is then scored on photos it has effectively already seen, inflating accuracy.

**Audit** (`analysis/leakage_audit.py`) — using signals independent of the model (perceptual hash, pixel correlation, EXIF capture time, filename frame numbers):
- **13.8%** of test images have a near-duplicate in the train+val gallery;
- **97.8%** share a capture **session** with a gallery image;
- of images with EXIF, ~29% are within 1 second of their nearest train image.

**Honest re-evaluation.** We re-split by whole **session** (no burst spans train and test) and **retrain from scratch**, against a **random-split control on the same 35 birds / 1743 images / identical per-bird counts** — so any gap is due to the split alone, not to less data. The session-disjoint test set has **0%** near-duplicates vs **10%** for the control.

![leakage: random versus session-disjoint](figures/06_leakage_random_vs_session.png)

All figures below are **macro** (each individual weighted equally), computed by `analysis/evaluate.py`:

| macro metric | random split (leaky) | session-disjoint (honest) | gap |
|---|---|---|---|
| retrieval prototype top-1 | 0.920 | **0.389** | +0.531 |
| retrieval prototype top-5 | 0.984 | **0.726** | +0.258 |
| retrieval 1-NN top-1 | 0.902 | **0.384** | +0.518 |

The control **reproduces the ~0.92 headline**, so the drop is cleanly attributable to the split. The softmax classification head collapsed in exactly the same way; it is not tabulated here because the identification interface is retrieval, and the head's accuracy exists only per-image. The discriminative power lived in a feature extractor that had seen every session — the earlier 0.95/0.959 mainly measured *same-session* recognition and overstated *cross-session* (different day / lighting) generalization.

> **Two evaluation choices worth stating.** (1) *Macro, not micro.* The test set is dominated by a few heavily photographed birds (Medici 291 photos, Beau 19); per-image accuracy silently adopts that as a prior over which penguin gets photographed, which nothing justifies. (2) *Prototype top-5 means the five nearest class prototypes*, i.e. five distinct candidate individuals — not the five nearest gallery photos, which can all belong to the same bird and so overstate how much a shortlist helps a keeper.

**Open-set threshold** (`embedding_id/tune_openset.py`) — the identifier must also answer "I don't know this bird" (only 44 of ~81 colony members are enrolled). Simulating unknowns by leave-one-penguin-out, known vs unknown separability is **AUC 0.991**; the confidence threshold was raised **0.55 → 0.80** (keeps 91.9% of enrolled birds, rejects 96.6% of unenrolled ones), so an unenrolled penguin is refused rather than misnamed.

**Implication.** Cross-session generalization — not same-session accuracy — is the real challenge, and it is data-limited: 10 of the 44 enrolled birds have only one or two photo sessions. This motivated the two levers pursued in [§6](#6-cross-validated-metric-learning): **ArcFace metric learning** and **more multi-session photos per individual**.

**Known limitation of this single split.** Whole sessions are assigned to train/val/test, so per-bird test size is whatever a session happens to contain — from **1 photo (Beau, Spider, Not Tiki) to 43 (Medici)**, i.e. an actual test share ranging from 2.7% to 42% against a nominal 15% target. Statistics for the smallest birds are near-meaningless here; [§6](#6-cross-validated-metric-learning) removes this limitation by cross-validating.

Scripts: `analysis/leakage_audit.py`, `analysis/build_session_splits.py`, `analysis/session_disjoint_eval.py`, `analysis/evaluate.py`, `embedding_id/tune_openset.py`.

## 6. Cross-Validated Metric Learning

§5 gives an honest but fragile estimate: with whole sessions assigned to one split, several individuals are judged on one or two photographs. This section replaces that single draw with cross-validation and uses it to measure metric learning.

**Protocol** — pre-registered before any run, identical for every configuration compared.

- **Session-wise 5-fold CV** (`analysis/build_cv_folds.py`). *Sessions*, never individual photos, are dealt into folds. Each session goes to the fold minimising (that bird's images already there, then all birds' images already there); the second key matters, because balancing per bird alone piles every bird's largest session into fold 0 and leaves it training on 59% of the data instead of 80%. Result: all five folds get **~80% train / ~350 test**.
- **Every one of the 1743 photos is tested exactly once**, by a model that never saw its capture session — against 261 tested photos under a single split. A bird such as Beau is judged on all 19 of its photos rather than 1.
- **Fixed 80-epoch cosine schedule, no validation split, no early stopping**, final epoch kept (`train_metric.py`). This keeps training data at 80% and removes checkpoint selection as a bias source.
- Configurations are compared by a **paired bootstrap** on the macro difference — the same resampled images applied to both — which is considerably more sensitive than asking whether two independent confidence intervals overlap.

![evaluation coverage per individual](figures/11_evaluation_coverage.png)

**Result** (`analysis/eval_cv.py`, macro, 1743 photos, 35 individuals):

| macro metric | softmax + basic | **ArcFace + strong** | paired difference |
|---|---|---|---|
| rank-1 | 0.390 [0.367, 0.411] | **0.559** [0.535, 0.583] | **+0.169** [+0.145, +0.193] |
| rank-5 | 0.746 [0.724, 0.769] | **0.782** [0.759, 0.804] | +0.036 [+0.012, +0.058] |
| **mAP** | 0.420 [0.403, 0.438] | **0.581** [0.558, 0.603] | **+0.161** [+0.141, +0.181] |
| 1-NN rank-1 | 0.387 [0.365, 0.410] | **0.561** [0.537, 0.586] | +0.174 [+0.151, +0.200] |

The baseline's cross-validated **0.390 reproduces the single-split 0.389** of §5, so cross-validation introduces no bias and the ArcFace gain is measured against a verified baseline. Every difference interval excludes zero. Intervals also tighten from ±0.05 to ±0.022, because 1743 photos are scored instead of 261.

![cumulative matching characteristic](figures/07_cmc_curve.png)

mAP rises with rank-1 rather than lagging it, so the gain is a genuinely better ranking and not a lucky first place. The CMC curve is also what justifies a shortlist interface: showing a keeper five candidates contains the right bird **78%** of the time against **56%** for a single answer.

**Accuracy is governed by capture sessions per individual, not by photo count:**

| capture sessions | individuals | softmax + basic | ArcFace + strong |
|---|---|---|---|
| 3 | 8 | 0.081 | **0.186** |
| 4–6 | 13 | 0.423 | **0.618** |
| 7+ | 14 | 0.535 | **0.717** |

![accuracy versus capture sessions](figures/08_accuracy_vs_sessions.png)

Metric learning lifts every bucket, but **cannot rescue the 3-session birds**: they stay unusable at 0.186, and one individual (Greyjoy) is never identified under either configuration. Excluding those 8, the remaining 27 individuals reach **0.669**. The levers are therefore complementary — ArcFace exploits session diversity that already exists, and only re-photographing creates it.

![per-individual change](figures/09_per_individual_change.png)

> **Correction to an earlier reading.** "12 of 35 individuals are never correctly identified" was an artifact of one- and two-photo test sets under the single split. Evaluated over every photo, the baseline has 2 such individuals and ArcFace has 1.

### Open-set identification

Rank-1 assumes the bird in front of the camera is already enrolled. Only **35 of the colony's 81 individuals** are, so in use the identifier is asked about strangers constantly, and it must refuse them rather than pick the nearest name. Unknowns are simulated leave-one-individual-out: a query's impostor score is its best prototype similarity with its own identity removed from the gallery.

| operating point | softmax + basic | **ArcFace + strong** |
|---|---|---|
| DIR @ FAR = 1% | 0.112 | **0.229** |
| DIR @ FAR = 5% | 0.176 | **0.360** |
| DIR @ FAR = 10% | 0.222 | **0.431** |

![open-set DIR against FAR](figures/10_open_set_dir_far.png)

DIR@FAR=x is the fraction of enrolled birds both correctly named *and* confident enough to be accepted, at the threshold where unenrolled birds are wrongly accepted x of the time. **Closed-set rank-1 of 0.559 falls to 0.229** once unenrolled birds must be refused 99% of the time — that gap is the price of being able to say "I don't know", and it is the number that describes deployment readiness. ArcFace roughly doubles it at every operating point, so metric learning improves the confidence ordering and not only the ranking.

**Not yet done:** the deployment model retrained on all 1743 photos — for which 0.559 is the conservative estimate, since each fold trains on 80% of the data while the deployment model would use 100%.

## 7. Flagship Plan: Embedding Retrieval + RAG

The centerpiece direction: turn the classifier into a **multimodal retrieval + Retrieval-Augmented Generation** application.

### Pipeline
```
Visitor photo
   │
   ▼
[Detect + frontal filter]  ── not frontal / not a penguin ──▶ "please re-shoot"
   │
   ▼
[Image embedding model]  (ArcFace-trained backbone, or CLIP / DINOv2)
   │  photo → vector
   ▼
[Vector DB: penguin gallery]  (FAISS / Qdrant / Milvus / pgvector)
   │  ANN search top-k enrolled vectors
   ▼
[Match + open-set threshold]  ── distance too large ──▶ "unknown individual"
   │  identity = Cooper
   ▼
[Knowledge retrieval — RAG]
   ├─ structured profile of "Cooper" (name, age, sex, band colors, personality, habits, keeper notes)
   └─ general penguin knowledge chunks (species biology, colony, conservation)
   │
   ▼
[LLM generation, grounded on retrieved docs]  → name, traits, habits, answer to visitor's question
```

### Two RAG roles (both used together)
1. **Profile-grounded generation** — after identity retrieval, fetch that individual's profile document and have the LLM generate a natural-language description. Grounding prevents the model from **hallucinating facts about a real, named animal** — a concrete, defensible reason to use RAG here.
2. **Open-domain Q&A** — a knowledge base (penguin biology, the colony, care, conservation) chunked + embedded; free-form visitor questions retrieve relevant chunks → grounded answers with citations.

### Optional agentic layer
An LLM agent orchestrating tools: `identify_penguin(image)`, `get_profile(name)`, `search_knowledge(query)` — the model decides which to call. This showcases **AI agent + multimodal retrieval + RAG** in one system.

### Product form: a conversational Humboldt penguin expert
The user-facing wrapper is a chat window. On entry (QR scan / app open) the bot greets the visitor:

> 🐧 Hi! I'm the resident **Humboldt penguin expert**. Send me a **front-facing, full-body** photo of a penguin and I'll tell you which individual it is — its name, birthday, personality and story. Ask me anything about penguins too!

- **Persona** = the agent's system prompt (a warm, concise keeper).
- **Photo → identity**: a penguin photo triggers `identify_penguin`, then `get_profile` to describe that individual.
- **Question → knowledge**: a general penguin question triggers `search_knowledge`.
- **Conversation memory**: the identified individual is kept in session state, so follow-ups ("how old is it?") need no photo re-upload.
- **Graceful uncertainty**: on low confidence / non-frontal photos, the bot asks for a clearer front-facing shot instead of guessing.
- **Grounding**: facts about a specific penguin come only from `get_profile`; if a field is missing the bot says so rather than inventing it — the core anti-hallucination guarantee.

### Suggested stack
- **Image embeddings**: currently the exp1 ResNet18 as a frozen feature extractor (exp3); planned ArcFace-trained backbone, benchmarked against off-the-shelf **DINOv2 / CLIP**.
- **Vector DB**: FAISS (simple/local) → **Qdrant** (production feel) for the demo.
- **Text embeddings**: open-source `bge` / `e5` for the knowledge base.
- **LLM**: a **self-hosted open-source model** (e.g. Qwen / Llama), optionally **LoRA-fine-tuned** on penguin data — local deployment rather than a paid API — for grounded generation + citations.
- **Serving**: FastAPI backend + Streamlit/Gradio demo UI.
- **Evaluation**: retrieval hit-rate (top-k), answer **faithfulness/groundedness**, and open-set reject precision.

### Technical scope
This direction combines fine-grained computer vision, **metric learning**, a **vector database**, **multimodal RAG**, **grounded LLM generation with anti-hallucination guardrails**, and **RAG evaluation**, applied to a real-world dataset.

### Current status & next steps
**Done** — the CNN retrieval route (exp3): a working **FAISS vector database** with **incremental enrollment** (add a new penguin by storing its features — no retraining) and **open-set rejection** (threshold tuned to **0.80** by leave-one-penguin-out, AUC 0.991; blurry / unenrolled → refuse rather than misname). A **data-leakage audit** ([§5](#5-data-leakage-audit--cross-session-evaluation)) established the honest baseline, and **ArcFace metric learning under 5-fold cross-validation** ([§6](#6-cross-validated-metric-learning)) raised cross-session identification from **macro 0.390 to 0.559**. The classifier route is kept only as a baseline; **retrieval is the identification method** going forward.

**Next**
1. **Photograph the under-covered birds (priority).** Two gaps, both only closable with a camera: the **37 individuals not in the system at all**, and the **8 enrolled birds with only 3 capture sessions** that metric learning leaves at 0.186. What is needed is photographs on *new days, in new light* — additional frames from an existing burst add nothing.
2. **Finish the evaluation suite** — mAP and CMC alongside macro rank-1, plus open-set **TAR@FAR** for the "is this bird even enrolled?" question that closed-set accuracy does not measure.
3. **Train and ship the deployment model** — one ArcFace model on all 1743 photos, reported with the §6 cross-validated estimate.
4. **Build a clean penguin profile database** — one structured record per individual (name, date of birth, personality, features, habits, band colors) to ground `get_profile`.
5. **Wire the agent loop** — orchestrate `identify_penguin` / `get_profile` / `search_knowledge` via the LLM's function-calling / tool-use, with conversation memory.
6. **Conversational Humboldt penguin expert UI** — a chat window with the welcome message and session memory described above.

## 8. Repo Structure

```text
pgs/
├─ README.md / README.zh-CN.md       # bilingual docs
├─ plot_experiments.py               # regenerates figures/ from run logs
├─ figures/                          # experiment record figures (PNG)
├─ penguin_image_count_summary.csv   # per-individual counts & selection
├─ make_doc.py                       # generates the photo-collection .docx
│
├─ a.py                              # per-individual train/val/test split
├─ train_experiment1.py              # classifier training (exp1/exp2, and the §5 retrains)
├─ train_metric.py                   # §6 softmax/ArcFace training under K-fold CV
├─ eval_checkpoint.py                # checkpoint evaluation
├─ crop_penguin_belly_yolo.py        # crop bellies with YOLO
├─ prepare_belly_yolo_dataset.py     # prepare belly-detection dataset
├─ train_belly_detector.py           # train belly detector
├─ annotate_belly.py                 # belly annotation tool
│
├─ embedding_id/                     # retrieval core: embedder, vector store, identify, open-set tuning
├─ analysis/                         # evaluation & audits
│  ├─ leakage_audit.py               #   §5 burst/session leakage audit
│  ├─ build_session_splits.py        #   §5 session-disjoint + random-control splits
│  ├─ session_disjoint_eval.py       #   §5 session clustering + re-evaluation
│  ├─ evaluate.py                    #   canonical macro-only evaluation of one model
│  ├─ build_cv_folds.py              #   §6 session-wise K-fold folds
│  ├─ eval_cv.py                     #   §6 fold aggregation, mAP/CMC/open-set, paired bootstrap
│  ├─ plot_figures.py                #   regenerates figures 06-11 from the artifacts
│  └─ artifacts/                     #   JSON/CSV results for every analysis above
│
├─ penguins_data/                    # raw data
├─ penguins_dataset_split/           # full-body train/val/test (exp1)
├─ penguins_dataset_split_belly_by_yoloV8/  # belly-crop split (exp2)
│
└─ runs/
   ├─ exp1_baseline/                 # full-body classification results
   ├─ exp2_belly_resnet18/           # belly-crop classification results
   ├─ exp1b_session_disjoint/        # §5 honest cross-session retrain
   ├─ exp1b_random_control/          # §5 random-split control
   ├─ cv_softmax_basic/fold0..4/     # §6 baseline, one model per fold
   ├─ cv_arcface_strong/fold0..4/    # §6 ArcFace + strong augmentation
   └─ detect/…/belly_detector/exp1/  # belly detector results
```

## 9. Reproduce

Install dependencies (CUDA PyTorch for an RTX 4060):
```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install numpy pillow ultralytics matplotlib python-docx
```

Train classifiers:
```powershell
# exp1: full body
python train_experiment1.py --data-dir penguins_dataset_split --epochs 30 --batch-size 32
# exp2: belly crop
python train_experiment1.py --data-dir penguins_dataset_split_belly_by_yoloV8 --epochs 50 --batch-size 32
```

Data-leakage audit & honest cross-session evaluation (§5):
```powershell
# quantify burst/session leakage in the current split
python analysis/leakage_audit.py
# build session-disjoint + random-control splits, then retrain and compare
python analysis/build_session_splits.py
python train_experiment1.py --data-dir penguins_dataset_split_session_disjoint --output-dir runs/exp1b_session_disjoint
python train_experiment1.py --data-dir penguins_dataset_split_session_random  --output-dir runs/exp1b_random_control
# macro evaluation of both retrains
python analysis/evaluate.py
# tune the open-set rejection threshold (leave-one-penguin-out)
python embedding_id/tune_openset.py
```

Cross-validated metric learning (§6) — about 11 min per fold on an RTX 4060, ~1 h 50 m in total:
```powershell
# deal capture sessions into 5 balanced folds (writes analysis/artifacts/cv_folds.json)
python analysis/build_cv_folds.py
# baseline and ArcFace, 5 folds each, fixed 80 epochs, no early stopping
python train_metric.py --loss softmax --aug basic  --all-folds
python train_metric.py --loss arcface --aug strong --all-folds
# pool folds; macro rank-1/rank-5/mAP/CMC/open-set + paired bootstrap comparison
python analysis/eval_cv.py cv_softmax_basic cv_arcface_strong
# redraw figures 06-11 from the JSON artifacts
python analysis/plot_figures.py
```

Regenerate figures / photo list:
```powershell
python plot_experiments.py
python make_doc.py
```
