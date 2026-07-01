# Penguin Individual Re-Identification

**English** | [中文](README.zh-CN.md)

Given a photo of a penguin, identify **which individual** it is (individual identity, not species). The end goal: a visitor takes one photo and instantly learns which specific penguin it is, plus that penguin's name, traits, and habits.

The project is evolving from a **classification baseline** into an **embedding-retrieval + RAG** system — turning each photo into a vector, matching it against a vector database, and using an LLM to generate a grounded description of the identified penguin.

---

## Table of Contents
- [1. Dataset](#1-dataset)
- [2. Completed Experiments](#2-completed-experiments)
- [3. Experiment Record Figures](#3-experiment-record-figures)
- [4. Key Findings](#4-key-findings)
- [5. Roadmap](#5-roadmap)
- [6. Flagship Plan: Embedding Retrieval + RAG](#6-flagship-plan-embedding-retrieval--rag)
- [7. Repo Structure](#7-repo-structure)
- [8. Reproduce](#8-reproduce)

---

## 1. Dataset

- Raw data `penguins_data/`: **82 individuals**, image counts ranging from 1 to 291 per bird — a **severe long-tail imbalance**.
- Filtered to the **44 individuals with ≥ 16 images** (`penguin_image_count_summary.csv`, `selected=True`); the remaining 37 (≤15 images) are too sparse to train and are held out for now.
- Split per individual into train / val / test: `penguins_dataset_split/`.
- Belly-crop variant (produced by the belly detector): `penguins_dataset_split_belly_by_yoloV8/`.

> Even within the selected 44, counts run from 291 (Medici) down to ~16 — an ~18× max/min gap. This imbalance is the root cause of most downstream difficulty. See [Figure 05](#3-experiment-record-figures).

## 2. Completed Experiments

| Experiment | Input | Model | Epochs | best val acc | **test acc** |
|---|---|---|---|---|---|
| **exp1 baseline** | full body | ResNet18 (transfer) | 29 (early-stop, cap 30) | 0.907 | **0.950** |
| **exp2 belly** | belly crop | ResNet18 (transfer) | 39 (early-stop, cap 50) | 0.867 | 0.866 |
| **belly detector** | full body | YOLOv8s detection | 98 | mAP@50 ≈ 0.98 | mAP@50-95 ≈ 0.60 |

Shared pipeline:
- `torchvision.datasets.ImageFolder` loading
- Transfer learning (ImageNet-pretrained ResNet18)
- Imbalance handling: `WeightedRandomSampler` + class-weighted `CrossEntropyLoss`
- Best checkpoint by val accuracy; final test evaluation with prediction CSV export

**exp1 (full body)** — test accuracy **0.950**, best val 0.907 (epoch 21). Per-class results ([Figure 04](#3-experiment-record-figures)) show high-support individuals (Cooper n=20, Ron_burgundy n=29, Medici n=44) near-perfect; errors concentrate on classes with only 3–5 test samples.

**exp2 (belly crop)** — test accuracy **0.866**, clearly **below** the full-body 0.950. Its val loss stays consistently higher ([Figure 01](#3-experiment-record-figures), right) — worse generalization.

**belly detector (YOLOv8s)** — 98 epochs, val **mAP@50 ≈ 0.98 / mAP@50-95 ≈ 0.60**, precision/recall ~0.95 ([Figure 03](#3-experiment-record-figures)). Weights: `runs/detect/runs/belly_detector/exp1/weights/best.pt`. Detection is good, but cropping **discards identity cues** (face, chest band, body proportions) and detector errors propagate downstream — which explains why exp2 is worse.

## 3. Experiment Record Figures

All figures are regenerated from each run's logs by `plot_experiments.py`, written to `figures/`.

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
4. **The bottleneck is data, not the model.** Errors fall almost entirely on classes with ≤5 samples; high-support individuals are near-perfect. Raising the ceiling depends on **more data + few-shot / metric-learning methods**, not merely a bigger backbone.

## 5. Roadmap

> The photo-collection plan lives in the "Penguin Photo Collection List" (generated by `make_doc.py`). This section covers **modeling/experiments beyond photo collection**.

### Phase A — Squeeze the baseline (cheap, do first)
- **A1 Stronger augmentation**: RandAugment/TrivialAugment, RandomErasing, ColorJitter, random occlusion — simulate visitor-photo backlight, blur, occlusion. Goal: shrink exp1's train(≈1.0)–val(≈0.90) overfitting gap.
- **A2 Backbone comparison**: ResNet18/50, ConvNeXt-Tiny, EfficientNet-V2-S, ViT-S under one pipeline; plot accuracy vs params; confirm the "full body" finding holds for stronger models.
- **A3 Input-resolution ablation**: 224 vs 288 vs 384.
- **A4 TTA + confidence thresholding**: abstain / "please re-shoot" on low-confidence predictions; measure coverage at high precision.

### Phase B — Long-tail / few-shot (the core difficulty)
- **B1 Metric learning / retrieval-based ID** (ArcFace/CosFace/triplet/ProxyAnchor): reframe from "44-class classification" to **embedding + nearest-neighbor**. New or sparse individuals just get enrolled — no retraining. Evaluate with top-1 / top-5 retrieval accuracy. **→ This becomes the core of [Phase E / Section 6](#6-flagship-plan-embedding-retrieval--rag).**
- **B2 Imbalance methods**: compare WeightedSampler, Focal Loss, Logit-Adjustment, class-balanced reweighting.
- **B3 Open-set recognition**: add reject capability (unknown individual / non-penguin / non-frontal); test using the 37 dropped sparse individuals + non-penguin images.

### Phase C — Close the real-world gap
- **C1 End-to-end pipeline**: locate penguin → pose/frontal filter → identify, runnable on a single visitor photo.
- **C2 Frontal/orientation classifier**: lightweight front-vs-back detector to drive the "please re-shoot" prompt.
- **C3 Robustness eval set**: a small set of real visitor photos (backlight/far/blurry/multiple birds) as a hard test set.

### Phase D — Interpretability & operations
- **D1 Grad-CAM**: confirm whether the model attends to face / chest band / belly.
- **D2 Confusion-pair analysis** from `confusion_matrix.csv`.
- **D3 Leg-band color as auxiliary feature**: band colors (`Color_Bands*.jpg`) as a strong prior/verification signal; fuse "vision model + band color".

## 6. Flagship Plan: Embedding Retrieval + RAG

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

### Optional agentic layer (extra portfolio value)
An LLM agent orchestrating tools: `identify_penguin(image)`, `get_profile(name)`, `search_knowledge(query)` — the model decides which to call. This showcases **AI agent + multimodal retrieval + RAG** in one system.

### Suggested stack
- **Image embeddings**: the ArcFace-trained backbone from B1, benchmarked against off-the-shelf **DINOv2 / CLIP** (strong fine-grained features with no training).
- **Vector DB**: FAISS (simple/local) → **Qdrant** (production feel) for the demo.
- **Text embeddings**: `bge` / `e5` or an API embedding for the knowledge base.
- **LLM**: Claude (e.g. `claude-opus-4-8`) via API, with grounded generation + citations.
- **Serving**: FastAPI backend + Streamlit/Gradio demo UI.
- **Evaluation** (what AI-application roles look for): retrieval hit-rate (top-k), answer **faithfulness/groundedness**, and open-set reject precision.

### Why this is a strong portfolio project
It combines fine-grained CV, **metric learning**, a **vector database**, **multimodal RAG**, **grounded LLM generation with anti-hallucination guardrails**, and **RAG evaluation** — the exact toolbox of an AI-application engineer, on a real, non-toy dataset.

## 7. Repo Structure

```text
pgs/
├─ README.md / README.zh-CN.md       # bilingual docs
├─ plot_experiments.py               # regenerates figures/ from run logs
├─ figures/                          # experiment record figures (PNG)
├─ penguin_image_count_summary.csv   # per-individual counts & selection
├─ make_doc.py                       # generates the photo-collection .docx
│
├─ train_experiment1.py              # classifier training (exp1/exp2)
├─ eval_checkpoint.py                # checkpoint evaluation
├─ crop_penguin_belly_yolo.py        # crop bellies with YOLO
├─ prepare_belly_yolo_dataset.py     # prepare belly-detection dataset
├─ train_belly_detector.py           # train belly detector
├─ annotate_belly.py                 # belly annotation tool
│
├─ penguins_data/                    # raw data
├─ penguins_dataset_split/           # full-body train/val/test (exp1)
├─ penguins_dataset_split_belly_by_yoloV8/  # belly-crop split (exp2)
│
└─ runs/
   ├─ exp1_baseline/                 # full-body classification results
   ├─ exp2_belly_resnet18/           # belly-crop classification results
   └─ detect/…/belly_detector/exp1/  # belly detector results
```

## 8. Reproduce

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

Regenerate figures / photo list:
```powershell
python plot_experiments.py
python make_doc.py
```
