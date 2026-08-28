# Final presentation — 10 minutes

`final_presentation.pptx` — 12 content slides for a ten-minute slot, followed by
seven backup slides for questions. Every speaker note is stamped with its time
budget and the running clock, so the deck can be rehearsed without a crib sheet.

Every number on every slide is one of the values in
[`../analysis/artifacts/RESULTS.md`](../analysis/artifacts/RESULTS.md) or the
dissertation, and every figure is generated from
[`../analysis/artifacts/*.json`](../analysis/artifacts) — nothing is transcribed
by hand.

## The argument

Lead with the **leakage result**, because it is the only genuinely controlled
experiment in the project and the only finding that transfers to everyone else
in the room with an image archive. Then the **session finding**, because it is
the only one that yields an action a zoo can take. Then the **honest ladder**,
volunteered rather than extracted.

The line to land: *the number I would defend is not 0.559, it is 0.531.*

| # | slide | s | ends |
|---|---|---|---|
| 1 | Title | 20 | 0:20 |
| 2 | Identity is currently worn, not read from the bird | 48 | 1:08 |
| 3 | 2,307 photographs — but the unit of evidence is the encounter | 47 | 1:55 |
| 4 | **Change only the split rule, and 0.920 becomes 0.389** | 72 | 3:07 |
| 5 | An evaluation whose unit is the encounter, whose weight is the individual | 49 | 3:56 |
| 6 | Augmentation is the larger lever; metric learning earns its place as the gallery grows | 54 | 4:50 |
| 7 | **Identifiability is set by how many days a bird was photographed** | 66 | 5:56 |
| 8 | The more honest the question, the lower the answer | 63 | 6:59 |
| 9 | Retrieval, not classification — a new bird costs an enrolment | 54 | 7:53 |
| 10 | What this study does not show | 39 | 8:32 |
| 11 | The next gain is a camera, not a loss function | 46 | 9:18 |
| 12 | Close | 33 | 9:51 |

591 s budgeted; the scripts themselves are ~555 s at 140 wpm, leaving the rest
for pauses and slide changes. **If you are running long, compress slides 5 and
10** — the protocol slide survives as "sessions to folds, macro, session
bootstrap", and the limitations slide can be read at pace. Slides 4 and 7 are
the two that must not be rushed.

## Backup slides (13–19)

| slide | answers |
|---|---|
| 14 | Why 35 of 81? The session rule binds, not the photo rule |
| 15 | Did ArcFace help everyone, or did the macro mean hide it? |
| 16 | Why cross-validate rather than hold out one split? |
| 17 | Why not crop to the breast spots? |
| 18 | The threshold has a provenance, and it was wrong once |
| 19 | Training is fixed-length by design — and the 1.000 diagnostic |
| 20 | Every reported number, in one table |

Answers held in reserve, not on a slide:

- **"Is 0.390 vs 0.389 a replication?"** Numerically near-identical, but the
  single split used a different training recipe (30 epochs, early stopping,
  weighted sampling). It is corroboration that cross-validation introduces no
  bias, not a controlled comparison.
- **"The two leakage numbers — same dataset?"** No, and say so: the 97.8% /
  13.8% entanglement audit was run on the original 70:15:15 split over 44
  individuals; the 0.920 vs 0.389 retrain is the purpose-built count-matched
  pair over 35. Two independent lines of evidence.
- **"De-duplicate and the problem goes away?"** It does not. The clean half of
  the random test set still scores 0.946 against 1.000 on the leaky half, and
  0.389 session-disjoint. Dropping duplicates recovers almost nothing; only
  splitting by encounter exposes the gap.
- **"Did you tune the ArcFace margin?"** No — scale 30 and margin 0.3 are the
  paper's defaults and are not exposed as CLI flags, so they could not have
  been tuned per configuration.
- **"You deployed the configuration that is worse at rank-5."** True: softmax +
  strong reaches 0.809 against 0.782. ArcFace was selected on rank-1, mAP and
  colony-scale degradation. The rank-5 choice is genuinely open.
- **"Is FAISS computing your results?"** No. FAISS backs the deployed vector
  store's nearest-reference-photo lookup; every cross-validated number is an
  exact inner product over L2-normalised vectors in numpy. Same arithmetic.

## Rebuilding

```bash
cd presentation
python3 prepare_assets.py     # crops figures/, redraws the two slide-only plots
npm install                   # pptxgenjs
npm run build                 # -> final_presentation.pptx, with timings stamped
```

`prepare_assets.py` needs Pillow, matplotlib and numpy; `finalise.py` needs
python-pptx. `assets/` is gitignored — it is derived from `figures/`,
`Color_Bands1.jpg` and `analysis/artifacts/cv_report.json`.

To preview without PowerPoint:

```bash
soffice --headless --convert-to pdf final_presentation.pptx
```

## Files

| file | what it is |
|---|---|
| `build_deck.js` | the deck: content, speaker notes, slide layout |
| `lib.js` | palette, type scale and layout helpers |
| `components.js` | the four custom graphics (pipeline, honesty staircase, 2×2, session comparison) |
| `prepare_assets.py` | regenerates every image the deck uses |
| `finalise.py` | stamps time budgets into the notes, checks each script fits, repairs content types |

The palette is sampled from the project's own figures — background `#FCFCFB`,
series `#2A78D6` and `#EB6834`, grid `#E1E0D9` — so the plots sit on the slides
without a visible frame. One dot per capture session is the repeated motif,
because the capture session is what the talk is about.
