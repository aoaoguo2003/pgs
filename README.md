# Penguin Individual Re-Identification

**English** | [中文](README.zh-CN.md)

Given a photo of a **Humboldt penguin**, identify **which individual** it is (individual identity, not species). The end goal: a visitor takes one photo and instantly learns which specific penguin it is, plus that penguin's name, traits, and habits. All individuals in this project are Humboldt penguins from a single colony.

The project is evolving from a **classification baseline** into an **embedding-retrieval + RAG** system — turning each photo into a vector, matching it against a vector database, and using an LLM to generate a grounded description of the identified penguin. The retrieval core works, but a **data-leakage audit** ([§5](#5-data-leakage-audit--cross-session-evaluation)) found the headline number was inflated by same-session camera bursts shared between train and test: honest **cross-session** top-1 is **~0.49** (vs ~0.96 same-session). Closing that gap — via metric learning and more diverse photos — together with the profile/RAG layer and a conversational UI is the current work.

---

## Table of Contents
- [1. Dataset](#1-dataset)
- [2. Completed Experiments](#2-completed-experiments)
- [3. Experiment Record Figures](#3-experiment-record-figures)
- [4. Key Findings](#4-key-findings)
- [5. Data Leakage Audit & Cross-Session Evaluation](#5-data-leakage-audit--cross-session-evaluation)
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
| **exp3 embedding retrieval** | full body | ResNet18 features + FAISS (no training) | — | — | **0.959** (prototype) / 0.947 (1-NN) / 0.978 (top-5) |

> ⚠️ **Leakage caveat:** the exp1 (0.950) and exp3 (0.959) accuracies above use a **random split**. A later audit found same-session camera bursts leak into the test set, inflating these numbers; the honest **cross-session** top-1 is **~0.44–0.49**. See [§5](#5-data-leakage-audit--cross-session-evaluation).

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
4. **The bottleneck is data, not the model.** Errors fall almost entirely on classes with ≤5 samples; high-support individuals are near-perfect. Raising the ceiling depends on **more data + few-shot / metric-learning methods**, not merely a bigger backbone. A leakage-corrected evaluation ([§5](#5-data-leakage-audit--cross-session-evaluation)) makes this concrete: cross-session accuracy is far below the random-split figure.

## 5. Data Leakage Audit & Cross-Session Evaluation

The dataset contains many **burst sequences** — same camera, same moment, consecutive frames (e.g. `DSC_2743…2749`). Because `a.py` splits each individual's photos **at random**, near-duplicate frames from one burst can land in train and test at the same time; the model is then scored on photos it has effectively already seen, inflating accuracy.

**Audit** (`analysis/leakage_audit.py`) — using signals independent of the model (perceptual hash, pixel correlation, EXIF capture time, filename frame numbers):
- **13.8%** of test images have a near-duplicate in the train+val gallery;
- **97.8%** share a capture **session** with a gallery image;
- of images with EXIF, ~29% are within 1 second of their nearest train image.

**Honest re-evaluation.** We re-split by whole **session** (no burst spans train and test) and **retrain from scratch**, against a **random-split control on the same 35 birds / 1743 images / identical per-bird counts** — so any gap is due to the split alone, not to less data. The session-disjoint test set has **0%** near-duplicates vs **10%** for the control.

| metric | random split (leaky) | session-disjoint (honest) | gap |
|---|---|---|---|
| softmax classifier top-1 | 0.943 | **0.433** | +0.510 |
| retrieval prototype top-1 | 0.950 | **0.490** | +0.460 |
| retrieval 1-NN top-1 | 0.931 | 0.441 | +0.490 |
| retrieval top-5 | 0.958 | **0.594** | +0.364 |

The control **reproduces the ~0.95 headline**, so the drop is cleanly attributable to the split. Both routes collapse together — the discriminative power lived in a feature extractor that had seen every session. **Honest cross-session top-1 is ~0.44–0.49 (top-5 ~0.59):** the earlier 0.95/0.959 mainly measured *same-session* recognition and overstated *cross-session* (different day / lighting) generalization.

**Open-set threshold** (`embedding_id/tune_openset.py`) — the identifier must also answer "I don't know this bird" (only 44 of ~81 colony members are enrolled). Simulating unknowns by leave-one-penguin-out, known vs unknown separability is **AUC 0.991**; the confidence threshold was raised **0.55 → 0.80** (keeps 91.9% of enrolled birds, rejects 96.6% of unenrolled ones), so an unenrolled penguin is refused rather than misnamed.

**Implication.** Cross-session generalization — not same-session accuracy — is the real challenge, and it is data-limited: 10 of the 44 enrolled birds have only one or two photo sessions. This motivates the two next levers: **ArcFace metric learning** (features built for the cosine retrieval metric) and **more multi-session photos per individual**.

Scripts: `analysis/leakage_audit.py`, `analysis/build_session_splits.py`, `analysis/eval_session_retrain.py`, `analysis/session_disjoint_eval.py`, `embedding_id/tune_openset.py`.

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
**Done** — the CNN retrieval route (exp3): a working **FAISS vector database** with **incremental enrollment** (add a new penguin by storing its features — no retraining) and **open-set rejection** (threshold tuned to **0.80** by leave-one-penguin-out, AUC 0.991; blurry / unenrolled → refuse rather than misname). A **data-leakage audit** ([§5](#5-data-leakage-audit--cross-session-evaluation)) established the honest baseline: same-session top-1 ~0.96, but **cross-session ~0.49**. The classifier route is kept only as a baseline; **retrieval is the identification method** going forward.

**Next**
1. **Close the cross-session gap (priority)** — **ArcFace** metric-learning retrain (features built for the cosine retrieval metric, evaluated on the session-disjoint split) + **more multi-session photos** for individuals shot on only one or two occasions. (A no-training test-time-augmentation attempt gave no gain, since the model was already trained with horizontal-flip augmentation.)
2. **Build a clean penguin profile database** — one structured record per individual (name, date of birth, personality, features, habits, band colors) to ground `get_profile`.
3. **Wire the agent loop** — orchestrate `identify_penguin` / `get_profile` / `search_knowledge` via the LLM's function-calling / tool-use, with conversation memory.
4. **Conversational Humboldt penguin expert UI** — a chat window with the welcome message and session memory described above.

## 7. Repo Structure

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
├─ eval_checkpoint.py                # checkpoint evaluation
├─ crop_penguin_belly_yolo.py        # crop bellies with YOLO
├─ prepare_belly_yolo_dataset.py     # prepare belly-detection dataset
├─ train_belly_detector.py           # train belly detector
├─ annotate_belly.py                 # belly annotation tool
│
├─ embedding_id/                     # retrieval core: embedder, vector store, identify, open-set tuning
├─ analysis/                         # data-leakage audit & cross-session evaluation (§5)
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

Data-leakage audit & honest cross-session evaluation (§5):
```powershell
# quantify burst/session leakage in the current split
python analysis/leakage_audit.py
# build session-disjoint + random-control splits, then retrain and compare
python analysis/build_session_splits.py
python train_experiment1.py --data-dir penguins_dataset_split_session_disjoint --output-dir runs/exp1b_session_disjoint
python train_experiment1.py --data-dir penguins_dataset_split_session_random  --output-dir runs/exp1b_random_control
python analysis/eval_session_retrain.py
# tune the open-set rejection threshold (leave-one-penguin-out)
python embedding_id/tune_openset.py
```

Regenerate figures / photo list:
```powershell
python plot_experiments.py
python make_doc.py
```
