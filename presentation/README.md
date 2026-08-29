# UCL final presentation

A ten-minute talk on this project — **`ucl_final_presentation.pptx`** (with
`ucl_final_presentation.pdf` as a projector fallback). 13 slides, every one
carrying timed speaker notes that add up to about 9 minutes 50.

Every figure comes from `figures/`, and every number traces to the dissertation
or to [`analysis/artifacts/RESULTS.md`](../analysis/artifacts/RESULTS.md).

## The shape of the talk

| # | slide | beat |
|---|---|---|
| 1 | Which penguin is this? | title |
| 2 | A penguin's name lives on a laminated sheet | why photographic ID is worth having |
| 3 | An archive, not an experiment | 2,307 photographs, 81 birds, a long tail |
| 4 | A photograph goes in; a name — or an honest refusal — comes out | the retrieval pipeline |
| 5 | **0.950** | the number that looked like a finished system |
| 6 | Then I looked at what was in the test set | the leakage audit — 0.920 → 0.389 |
| 7 | An evaluation that cannot flatter itself | session-wise 5-fold CV, macro, clustered bootstrap |
| 8 | Which change actually did the work | the loss × augmentation 2 × 2 |
| 9 | 0.559 is the friendliest number in this talk | gallery size, then real strangers |
| 10 | Nicki and Gonzo | sessions, not photographs — the central finding |
| 11 | So count encounters, not files | the four-session collection target |
| 12 | What is deployed, and what it is for | decision support, and what is unmeasured |
| 13 | Three things to take away | close |

The arc is deliberately the project's own: a headline that looked finished,
an audit that broke it, and a protocol that produced a smaller number worth
believing.

## The penguins

Slides 1, 2 and 3 carry photographs of the actual colony. The raw archive is not
in this repository, so they are recovered from the YOLO detector's plotted
mosaics under `runs/detect/`, and `penguin_photos.py` paints out the boxes and
`belly` labels the detector drew on them — that detector is a preliminary
experiment and is *not* part of the identification path, so removing its marks
is what makes the slides show the archive as photographed.

Only the **validation** mosaics are used. One validation tile is one photograph
of one bird, so the drawn filename identifies it. The train mosaics apply mosaic
augmentation — four different birds stitched into a single labelled tile — so a
photograph taken from there cannot be attributed to the bird in its label. That
is why slide 10 names Nicki and Gonzo but shows neither: Gonzo appears only in
train batches, and a photograph captioned with the wrong bird would undercut the
one slide that turns on which bird is which.

## Rebuilding it

```bash
python presentation/prepare_assets.py     # derives every image from figures/ and runs/
cd presentation && npm install pptxgenjs && node build_deck.js
```

`build_deck.js` writes `penguin_reid_final_pre.pptx`; rename it over
`ucl_final_presentation.pptx` to replace the committed deck. Slide text,
speaker notes and layout all live in that one file.

The palette is sampled from the analysis figures themselves — ground `FCFCFB`,
blue `2A78D6`, orange `EB6834` — so the charts sit on the slides without a
visible frame. The repeating dot is a ventral spot, which is the feature the
whole system identifies birds by.
