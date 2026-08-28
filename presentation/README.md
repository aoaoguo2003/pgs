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
| 2 | Identity is currently worn, not read from the bird | 43 | 1:03 |
| 3 | 2,307 photographs — but the unit of evidence is the encounter | 47 | 1:50 |
| 4 | **Change only the split rule, and 0.920 becomes 0.389** | 72 | 3:02 |
| 5 | An evaluation whose unit is the encounter, whose weight is the individual | 49 | 3:51 |
| 6 | Augmentation is the larger lever; metric learning earns its place as the gallery grows | 57 | 4:48 |
| 7 | **Identifiability is set by how many days a bird was photographed** | 75 | 6:03 |
| 8 | The more honest the question, the lower the answer | 63 | 7:06 |
| 9 | Retrieval, not classification — a new bird costs an enrolment | 54 | 8:00 |
| 10 | What this study does not show | 39 | 8:39 |
| 11 | The next gain is a camera, not a loss function | 46 | 9:25 |
| 12 | Close | 33 | 9:58 |

598 s budgeted; the scripts themselves are ~562 s at 140 wpm, leaving the rest
for pauses and slide changes. Rehearse against the stamped clock — number-heavy
delivery runs slower than prose, so if your first run lands past 10:00, **cut
from slides 5 and 10 first**: the protocol slide survives as "sessions to folds,
macro, session bootstrap", and the limitations slide can be read at pace. Slides
4 and 7 are the two that must not be rushed.

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

- **"What is the confidence interval on 0.531?"** There isn't one, and don't
  invent one: the controlled pair is a single retrain per arm, one seed,
  n_test = 261 (`session_retrain_report.json`). Claim it as directional and
  large rather than precise — rank-1, rank-5 and 1-NN all collapse together,
  and the entanglement was measured without any model at all. If you want the
  interval before the viva, the paired session bootstrap in `eval_cv.py` is the
  machinery to run over the two arms.
- **"Is 0.390 vs 0.389 a replication?"** No — say so before they do. The
  dissertation states it itself: the single split used a different recipe (30
  epochs, early stopping, weighted sampling) and was not a controlled
  comparison. It is a numerical coincidence between two differently-trained
  pipelines, and reading it as validation is the trap.
- **"Your own artifact reports session-disjoint at 0.974."** It does:
  `session_disjoint_report.json` re-splits gallery and query around the
  *already-trained* `exp1_baseline` checkpoint, so the training leakage is
  still there and only −0.015 shows up. Only the count-matched retrain
  (`session_retrain_report.json`) isolates the partitioning rule; that is the
  0.920 → 0.389 pair.
- **"Isn't the session gradient built into the evaluation?"** Partly, and it is
  worth conceding cleanly: under session-disjoint CV a three-session bird's
  prototype is assembled from one or two gallery sessions, so averaging over
  more encounters helps close to by construction. It does not weaken the
  collection recommendation — it is an argument for it — but "days decide
  recognisability" is too strong without this sentence attached.
- **"The two leakage numbers — same dataset?"** No, and say so: the 97.8% /
  13.8% entanglement audit was run on the original 70:15:15 split over 44
  individuals (1,676 gallery, 320 query); the 0.920 vs 0.389 retrain is the
  purpose-built count-matched pair over 35 birds and 261 test photographs. Two
  independent lines of evidence, not one measurement.
- **"De-duplicate and the problem goes away?"** It does not. Within the random
  split, the half with near-duplicates scores 1.000 and the clean half still
  scores 0.946 — dropping the 13.8% recovers almost nothing. Keep that
  comparison inside the random split when you quote it: those are per-image
  softmax numbers over 44 birds, not the macro prototype 0.389, so do not line
  the three up as one scale.
- **"Was the session gradient's 0.186 vs 0.535 head-to-head significant?"** It
  is not on a slide, deliberately: those are bin means over 8 and 14 birds with
  no intervals. Quote the monotone ordering and the partial correlation
  instead.
- **"Did you tune the ArcFace margin?"** No — scale 30 and margin 0.3 are the
  paper's defaults and are not exposed as CLI flags, so they could not have
  been tuned per configuration.
- **"You deployed the configuration that is worse at rank-5."** True: softmax +
  strong reaches 0.809 against 0.782. ArcFace was selected on rank-1, mAP and
  colony-scale degradation. The rank-5 choice is genuinely open.
- **"Is FAISS computing your results?"** No. FAISS backs the deployed vector
  store's nearest-reference-photo lookup; every cross-validated number is an
  exact inner product over L2-normalised vectors in numpy. Same arithmetic.

### One number to check before you present

Backup slide 18 repeats the dissertation's statement that the old threshold of
**0.800 accepts 29.7% of genuine strangers**. That figure does not reproduce
from `analysis/artifacts/cv_report.json`: reading the false-accept rate off the
genuine-stranger curve at threshold 0.800 gives **0.346** for ArcFace + strong,
and 0.271 / 0.380 / 0.284 for the other three configurations. Same source for
`identify.py`'s comment block, which also says 29.7%.

The argument is unaffected — every configuration puts the old threshold between
27% and 38%, against the 96.6% *rejection* the superseded tuning script claimed
(`embedding_id/artifacts/openset_threshold_report.json`, threshold 0.8,
`unknown_rejected = 0.9656`), so "it accepts roughly a third of real strangers"
is safe under any of them. The slide keeps the submitted number so the deck
matches the dissertation. Worth tracing where 29.7% came from before the viva,
and being ready to say "between a quarter and a third, depending on the
configuration" if pressed.

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
