# Revised defence deck — what changed and why

**File:** `TAO_XINYI_EDS_presentation_v2.pptx` — 18 main slides + 5 backup slides.

The talk now lives in the **speaker notes**, not on the slides. On-slide text is down from
**103 words per slide to 61** (main deck), while the speaker notes grew from ~1,000 to ~2,600
words. Every slide has a full script in the notes pane.

---

## 1. Too much text

Every slide was rebuilt around one visual and one idea.

* Hard rule applied: one headline, at most 3 short lines, one dark "takeaway" bar.
* Everything that was a bullet is now a sentence you *say*. Open the notes pane
  (View → Notes Page, or the Notes button in Presenter View) — the full script is there.
* All implementation detail (scaler, C = 1.0, lbfgs, nfft, window settings) has left the
  main deck. It lives on Backup 5 and in the notes, ready if you are asked.

## 2. Motivate broadly first

* **Title slide** is now a question — *"Where do bats feed?"* — with the formal title in
  small print at the bottom. (SMB: *"simplify the title to something more immediately
  interesting… what is the question you are answering?"*)
* **Slide 2** is the broad hook: *"Bats eat. We barely know where."* No dataset, no method,
  no Kenya. One sentence about why bats matter ecologically.
* **Slide 3** explains why a *feeding buzz* is the thing worth finding: a call says the bat
  was here; a buzz says it tried to eat.
* Kenya is no longer named until it is needed. Slide 4 now says "9.4 h **from one recorder**",
  with the site in the small caption; the Mara Triangle is properly introduced at Question 3.

## 3. Show the gap, don't describe it

Slide 5 is a new visual argument, using your own numbers:

* A slope from **0.930** (random split) down to **0.727** (weakest held-out site) with the
  −0.203 drop marked in red — the same detector, the same clips, only the split changed.
* Six squares along the bottom, one highlighted, showing how leave-one-site-out works.
* A side panel naming where the existing tools come from — Buzzfindr (Ontario),
  BatBuddy (Netherlands) — against where you deploy (Kenya).

The Question 1 result slide then answers it in the same visual form: pale bars = random
split, teal bars = worst unheard site. The baseline's bar collapses; Perch's barely moves.

## 4. One question at a time

The three questions are no longer stacked on one slide. The deck now runs in three acts,
each opened by a full-screen numbered question slide:

| | |
|---|---|
| **01** (slide 6) | Which way of describing the sound survives a site it has never heard? |
| **02** (slide 11) | Can it put the right clips at the top of a reviewer's list, with no threshold? |
| **03** (slide 13) | Does any of it survive a real night in the field? |

Each question is answered before the next is asked.

## 5. Other points from the annotated deck

* **"Explain what acoustic representations are."** New slide 7, *"A detector never hears the
  sound"* — a three-box diagram: the recording → **the representation** (a list of numbers,
  highlighted) → the detector. Takeaway: whatever the representation leaves out, the detector
  can never learn. This sets up the comparison before any numbers appear.
* **"Draw a figure that shows what each representation is. Show don't tell."** Slide 8 gives
  each representation a small diagram: 513 narrow frequency bands, 5 wide bands, and a
  pretrained-network box feeding a grid of learned values.
* **"Don't use 'folders', use sites."** All main slides now say *site* / *recording site* /
  *held-out site*. The folder-vs-site subtlety is stated honestly once, on the limitations
  slide, and the backup tables keep the exact folder names for questions.
* **"The header is not fully clear — what is better on average?"** Result headers are now
  claims: *"The gap closes — for one of the three"*, *"Ten results. How many are real?"*,
  *"The score ranks. It does not identify."*
* **Time-expansion slide** (slide 9): you suggested this could go, as implementation detail.
  It is kept but stripped to two spectrogram panels and a ×10 badge — the same picture, two
  sets of axis labels. **If you are short on time, this is the first slide to cut.**
* **Retrieval result** (slide 12) is now three rows of ten tiles: how many of the first ten
  results are real buzzes — 10, 8, 5 — rather than a bar chart of precision values.

---

## Running order and rough timings (15 min)

| # | Slide | Time |
|---|---|---|
| 1 | Where do bats feed? | 0:30 |
| 2 | Bats eat. We barely know where. | 0:45 |
| 3 | Presence is easy. Feeding is the question. | 0:50 |
| 4 | Hours of audio, seconds of signal | 0:45 |
| 5 | Detectors are graded where they were born | 1:15 |
| 6 | **Question 01** | 0:10 |
| 7 | A detector never hears the sound | 0:50 |
| 8 | Three ways to describe the same sound | 1:00 |
| 9 | Perch hears up to 16 kHz. Bats call at 20–120. | 0:50 |
| 10 | The gap closes — for one of the three | 1:15 |
| 11 | **Question 02** | 0:10 |
| 12 | Ten results. How many are real? | 1:00 |
| 13 | **Question 03** | 0:15 |
| 14 | The score ranks. It does not identify. | 1:15 |
| 15 | High scores arrive after sunset | 0:50 |
| 16 | Four things this study cannot tell you | 1:15 |
| 17 | A little closer than we were | 1:00 |
| 18 | Thank you | 0:15 |

≈ 13:30, leaving headroom. **For a 10-minute version:** move slides 9 and 15 to backup.

## Backup slides (18–23)

Kept dense on purpose — they are reference material for questions, not for reading aloud.

1. Detection — full metric set (all splits, SD, ROC-AUC, AP, folder-level range)
2. Retrieval — full metric set and protocol
3. Preprocessing sensitivity — window duration, spectrogram resolution, the padding shortcut
4. Kenya — thresholds, coverage, temporal pattern, candidate-selection routes
5. Two more reviewed Kenya candidates + implementation details

Likely questions and where the answer is:

* *"Why 0.25 s and not 0.50 s, which scored higher?"* → Backup 3 (the padding shortcut is
  total at 0.50 s).
* *"Isn't the Perch gain just the preprocessing?"* → Limitations 3, and Backup 5.
* *"How do you know the Kenya candidates are bats?"* → You don't, and slide 14 says so;
  Backup 4 has the selection routes.
* *"Is leave-one-site-out really site-level?"* → Limitations 1, Backup 1 folder-level range.

---

## One thing I could not check

The marking-sheet link in the email is a time-limited Moodle/S3 URL and it had **expired**
(it was signed to expire at 21:10 UTC on 1 September; the server refused it minutes later
with `Request has expired`). So the deck is built against the standard criteria for a
presentation of this kind — motivation and aims, methods, results, interpretation,
limitations, slide quality, delivery, timing, handling of questions — rather than against
the actual form. Re-download the PDF from Moodle and send it over, and I will check the deck
against it point by point.
