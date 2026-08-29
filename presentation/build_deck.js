// UCL final presentation — Automatic Identification of Humboldt Penguins at ZSL London Zoo
// Aoao Guo. 10 minutes, 13 slides.
const pptxgen = require("pptxgenjs");
const path = require("path");

const D = __dirname;
const F = (n) => path.join(D, "fig", n);

// ---------------------------------------------------------------- palette
// sampled from the project's own analysis figures so charts sit seamlessly
const DARK   = "102C4A";  // deep ocean navy
const DARK2  = "0A1F36";
const GROUND = "FCFCFB";  // exact background of every analysis figure
const INK    = "24231F";
const BODY   = "55534E";
const MUTED  = "8A877F";
const BLUE   = "2A78D6";  // figure blue
const ORANGE = "EB6834";  // figure orange
const LINE   = "E1E0D9";
const ICE    = "AEC8E6";
const CARD   = "F4F3EF";

const HEAD = "Cambria";
const SANS = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";           // 13.333 x 7.5
pres.author = "Aoao Guo";
pres.title  = "Automatic Identification of Humboldt Penguins at ZSL London Zoo";

const W = 13.333, H = 7.5, M = 0.85;

// ---------------------------------------------------------------- helpers
function lightSlide() {
  const s = pres.addSlide();
  s.background = { color: GROUND };
  return s;
}
function darkSlide() {
  const s = pres.addSlide();
  s.background = { color: DARK };
  return s;
}
// the visual motif: a penguin's ventral spot
function dot(s, x, y, d, color, opts) {
  s.addShape(pres.ShapeType.ellipse, Object.assign({
    x, y, w: d, h: d, fill: { color }, line: { type: "none" },
  }, opts || {}));
}
function scatterDots(s, seedList, color, transparency) {
  seedList.forEach(([x, y, d]) =>
    dot(s, x, y, d, color, transparency ? { fill: { color, transparency } } : {}));
}
function title(s, text, opts) {
  s.addText(text, Object.assign({
    x: M, y: 0.42, w: W - 2 * M, h: 1.12,
    fontFace: HEAD, fontSize: 32, bold: true, color: INK,
    align: "left", valign: "middle", isTextBox: true, margin: 0,
  }, opts || {}));
}
function kicker(s, text, opts) {
  s.addText(text, Object.assign({
    x: M, y: 0.16, w: W - 2 * M, h: 0.28,
    fontFace: SANS, fontSize: 11.5, bold: true, color: BLUE,
    charSpacing: 1.6, isTextBox: true, margin: 0, valign: "middle",
  }, opts || {}));
}
// bullet rows led by a spot rather than a bullet glyph
function spotList(s, items, o) {
  const { x, y, w, gap = 0.72, size = 14, color = BODY, dotColor = BLUE, dotD = 0.13 } = o;
  items.forEach((t, i) => {
    const yy = y + i * gap;
    dot(s, x, yy + 0.085, dotD, dotColor);
    s.addText(t, {
      x: x + 0.34, y: yy - 0.05, w: w - 0.34, h: gap,
      fontFace: SANS, fontSize: size, color, lineSpacing: size * 1.28,
      isTextBox: true, margin: 0, valign: "top",
    });
  });
}
function caption(s, text, o) {
  s.addText(text, Object.assign({
    fontFace: SANS, fontSize: 11, italic: true, color: MUTED,
    isTextBox: true, margin: 0, valign: "top",
  }, o));
}

// ================================================================ 1. TITLE
{
  const s = darkSlide();
  s.addImage({ path: path.join(D, "title_bg.jpg"), x: 0, y: 0, w: W, h: H });

  s.addText("MSc Ecology and Data Science  ·  Research Project BIOS0057", {
    x: M, y: 0.94, w: 8.2, h: 0.3, fontFace: SANS, fontSize: 12.5, bold: true,
    color: ICE, charSpacing: 1.8, isTextBox: true, margin: 0, valign: "middle",
  });

  s.addText("Which penguin\nis this?", {
    x: M, y: 1.4, w: 7.1, h: 1.8, fontFace: HEAD, fontSize: 52, bold: true,
    color: "FFFFFF", lineSpacing: 56, isTextBox: true, margin: 0, valign: "middle",
  });

  s.addText("Automatic identification of Humboldt penguins at ZSL London Zoo — and what an honest evaluation says it can really do.", {
    x: M, y: 3.38, w: 6.35, h: 1.1, fontFace: SANS, fontSize: 18,
    color: "D6E4F5", lineSpacing: 26, isTextBox: true, margin: 0, valign: "top",
  });

  s.addText("Aoao Guo", {
    x: M, y: 4.78, w: 6.0, h: 0.42, fontFace: HEAD, fontSize: 24, bold: true,
    color: "FFFFFF", isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText("Supervisor: Robin Freeman  ·  Division of Biosciences, UCL", {
    x: M, y: 5.22, w: 6.4, h: 0.32, fontFace: SANS, fontSize: 13.5,
    color: ICE, isTextBox: true, margin: 0, valign: "middle",
  });

  // the archive, in three numbers, along the foot of the navy field
  const stats = [
    ["2,307", "photographs"],
    ["81", "individuals"],
    ["335", "capture sessions"],
  ];
  stats.forEach(([n, l], i) => {
    const x = M + i * 2.28;
    dot(s, x, 6.13, 0.13, ORANGE);
    s.addText(n, {
      x, y: 6.3, w: 2.1, h: 0.52, fontFace: HEAD, fontSize: 28, bold: true,
      color: "FFFFFF", isTextBox: true, margin: 0, valign: "middle",
    });
    s.addText(l, {
      x, y: 6.79, w: 2.1, h: 0.28, fontFace: SANS, fontSize: 12,
      color: ICE, isTextBox: true, margin: 0, valign: "middle",
    });
  });

  s.addNotes(
`[0:00-0:40]  Good morning. I am Aoao Guo, and this is my project with Robin Freeman on identifying individual Humboldt penguins at ZSL London Zoo from photographs.

The archive I was given is 2,307 photographs of 81 birds, taken by volunteers across 335 separate photographic occasions.

The talk has a turn in it. I built a system that looked excellent, discovered it was measuring the wrong thing, rebuilt the evaluation, and ended up with a much smaller number and a much more useful conclusion.`);
}

// ============================================================ 2. WHY / BANDS
{
  const s = lightSlide();
  kicker(s, "WHY BOTHER");
  title(s, "A penguin's name lives on a laminated sheet");

  s.addText("ZSL London Zoo keeps 81 Humboldt penguins. A welfare note, a veterinary history or a breeding decision only means something once it is attached to the right bird.",
    { x: M, y: 1.66, w: 6.3, h: 0.95, fontFace: SANS, fontSize: 15.5, color: INK,
      lineSpacing: 22, isTextBox: true, margin: 0, valign: "top" });

  spotList(s, [
    "Coloured flipper bands are the current answer — and they are hidden by the bird's posture, by another penguin, or simply by the viewing angle.",
    "Over ten years, flipper-banded king penguins showed lower survival and breeding success than electronically tagged controls (Saraux et al., 2011). A marker is not automatically neutral.",
    "The birds already carry an identifier: the black spots on their white ventral plumage. African penguins use those same patterns to recognise each other (Baciadonna et al., 2024).",
  ], { x: M, y: 2.7, w: 6.3, gap: 1.12, size: 14 });

  // the identifier the bird already carries
  [1, 2, 3].forEach((n, i) => {
    s.addImage({ path: path.join(D, `spot${n}.jpg`), x: M + i * 1.22, y: 5.84, w: 1.1, h: 1.1 });
  });
  s.addText("Ventral spot patterns: individual, stable, and already on the bird.", {
    x: 4.6, y: 5.88, w: 2.6, h: 1.02, fontFace: SANS, fontSize: 12.5, italic: true,
    color: BODY, lineSpacing: 17, isTextBox: true, margin: 0, valign: "middle",
  });

  s.addImage({ path: path.join(D, "bands.jpg"), x: 8.55, y: 1.7, w: 2.95, h: 4.83 });
  caption(s, "The colony's own band chart — the system a photograph would complement.",
    { x: 7.85, y: 6.66, w: 4.6, h: 0.5, align: "center" });

  s.addNotes(
`[0:40-1:30]  Identification is the foundation of colony management. Right now it is done with coloured flipper bands, read off a chart like the one on the right.

Two problems. Bands get obscured — by posture, by another bird, by the angle you happen to be standing at. And attached markers are not free: a ten-year study on king penguins found banded birds had lower survival and lower breeding success than electronically tagged controls.

Meanwhile the penguins already carry an identifier — the spot pattern on the belly. African penguins use those patterns to recognise each other. So the question is whether a camera can too.`);
}

// ============================================================ 3. THE ARCHIVE
{
  const s = lightSlide();
  kicker(s, "THE DATA");
  title(s, "An archive, not an experiment");

  const stats = [
    ["2,307", "photographs"],
    ["81", "individuals"],
    ["1 → 291", "photographs per bird"],
    ["335", "capture sessions"],
  ];
  const cw = 2.5, cgap = 0.2;
  stats.forEach(([n, l], i) => {
    const x = M + (i % 2) * (cw + cgap);
    const y = 1.66 + Math.floor(i / 2) * 1.16;
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w: cw, h: 1.06, rectRadius: 0.06,
      fill: { color: CARD }, line: { type: "none" },
    });
    dot(s, x + 0.2, y + 0.19, 0.1, i === 2 ? ORANGE : BLUE);
    s.addText(n, {
      x: x + 0.2, y: y + 0.32, w: cw - 0.4, h: 0.44, fontFace: HEAD, fontSize: 23, bold: true,
      color: INK, isTextBox: true, margin: 0, valign: "middle",
    });
    s.addText(l, {
      x: x + 0.2, y: y + 0.74, w: cw - 0.4, h: 0.26, fontFace: SANS, fontSize: 11.5,
      color: MUTED, isTextBox: true, margin: 0, valign: "middle",
    });
  });

  const iw = 5.9;
  s.addImage({ path: F("05_dataset_distribution.jpg"), x: 6.55, y: 1.72, w: iw, h: iw * 0.3395 });
  caption(s, "Every colony member, sorted by photograph count — Medici holds 291.",
    { x: 6.55, y: 3.78, w: iw, h: 0.3, align: "center" });

  s.addText([
    { text: "Taken by volunteers during routine husbandry — no protocol, no fixed viewpoint, no schedule. ", options: { color: INK } },
    { text: "Two inclusion thresholds leave the ", options: { color: BODY } },
    { text: "35 individuals and 1,743 photographs", options: { color: INK, bold: true } },
    { text: " behind every number here.", options: { color: BODY } },
  ], { x: M, y: 4.28, w: W - 2 * M, h: 0.66, fontFace: SANS, fontSize: 14.5,
       lineSpacing: 21, isTextBox: true, margin: 0, valign: "top" });

  const pw = 1.31, pgap = 0.14, pn = 7;
  const px0 = (W - (pn * pw + (pn - 1) * pgap)) / 2;
  for (let i = 0; i < pn; i++) {
    s.addImage({ path: path.join(D, `strip${i + 1}.jpg`),
                 x: px0 + i * (pw + pgap), y: 5.02, w: pw, h: pw / 0.78 });
  }
  caption(s, "Seven of the eighty-one, as photographed — different days, light, distance and backgrounds, and one bird facing away.",
    { x: M, y: 6.78, w: W - 2 * M, h: 0.34, align: "center" });

  s.addNotes(
`[1:30-2:15]  Here is the raw material. 2,307 photographs of 81 birds — but look at the shape of it. One bird has 291 photographs; the tail has one each. An eighteen-fold spread across even the birds I could use.

This was never collected as an experiment. Volunteers photographed the penguins during husbandry, whenever it was convenient. Two inclusion thresholds — sixteen photographs, and three separate capture sessions — leave the 35 individuals and 1,743 photographs behind every number I am about to show you.

Hold on to one word from that sentence: session. It is going to matter more than anything else in this talk.`);
}

// ============================================================ 4. THE SYSTEM
{
  const s = lightSlide();
  kicker(s, "THE SYSTEM");
  title(s, "A photograph goes in; a name — or an honest refusal — comes out");

  const steps = [
    ["Photograph", "frontal, full body,\nas taken"],
    ["Embedding", "ResNet18, 512-d,\nL2-normalised"],
    ["Gallery search", "FAISS, cosine over\n81 prototypes"],
    ["Threshold 0.938", "accept, or decline\nto identify"],
    ["Decision", "identity + ranked\nalternatives"],
  ];
  const pitch = (W - 2 * M) / steps.length;
  steps.forEach(([lab, sub], i) => {
    const cx = M + pitch * (i + 0.5);
    const d = 1.02;
    const filled = i === 3;
    s.addShape(pres.ShapeType.ellipse, {
      x: cx - d / 2, y: 1.72, w: d, h: d,
      fill: { color: filled ? ORANGE : DARK }, line: { type: "none" },
    });
    s.addText(String(i + 1), {
      x: cx - d / 2, y: 1.72, w: d, h: d, fontFace: HEAD, fontSize: 26, bold: true,
      color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0,
    });
    s.addText(lab, {
      x: cx - pitch / 2 + 0.1, y: 2.9, w: pitch - 0.2, h: 0.36, fontFace: SANS, fontSize: 14.5,
      bold: true, color: INK, align: "center", valign: "middle", isTextBox: true, margin: 0,
    });
    s.addText(sub, {
      x: cx - pitch / 2 + 0.1, y: 3.24, w: pitch - 0.2, h: 0.66, fontFace: SANS, fontSize: 11.5,
      color: MUTED, align: "center", valign: "top", lineSpacing: 15, isTextBox: true, margin: 0,
    });
    if (i < steps.length - 1) {
      const mid = cx + pitch / 2;
      [-0.17, 0, 0.17].forEach((o) => dot(s, mid + o - 0.035, 2.19, 0.07, LINE));
    }
  });

  const cards = [
    ["Enrolment, not retraining",
     "A new bird is a stored vector. Smew and Skunk are searchable in the deployed gallery although no model was ever trained on them. A softmax head would need a new output layer and a full retrain for every arrival."],
    ["A principled way to refuse",
     "Cosine similarity to a prototype carries a threshold. A classifier must spread probability across the names it knows, so it names something — whatever walks past the camera."],
  ];
  cards.forEach(([h, b], i) => {
    const x = M + i * (5.9 + 0.36);
    s.addShape(pres.ShapeType.roundRect, {
      x, y: 4.28, w: 5.9, h: 2.28, rectRadius: 0.05,
      fill: { color: CARD }, line: { type: "none" },
    });
    dot(s, x + 0.34, 4.66, 0.13, BLUE);
    s.addText(h, {
      x: x + 0.68, y: 4.53, w: 5.0, h: 0.36, fontFace: SANS, fontSize: 15, bold: true,
      color: INK, isTextBox: true, margin: 0, valign: "middle",
    });
    s.addText(b, {
      x: x + 0.34, y: 5.02, w: 5.22, h: 1.32, fontFace: SANS, fontSize: 13,
      color: BODY, lineSpacing: 18.5, isTextBox: true, margin: 0, valign: "top",
    });
  });

  s.addText("Why retrieval rather than an 81-way classifier", {
    x: M, y: 3.94, w: 6.0, h: 0.3, fontFace: SANS, fontSize: 11.5, bold: true,
    color: BLUE, charSpacing: 1.2, isTextBox: true, margin: 0, valign: "middle",
  });

  s.addNotes(
`[2:15-3:05]  The system is retrieval, not classification. A photograph becomes a 512-dimensional vector from a ResNet18. That vector is compared by cosine similarity against one prototype per enrolled individual, held in a FAISS index. If the best score clears the threshold you get a name and a ranked shortlist; if it does not, you get "I don't know".

Two properties made me choose retrieval, and both paid off. First, enrolment without retraining — Smew and Skunk are searchable in the deployed gallery even though no model ever trained on them. Second, a classifier is structurally incapable of refusing: softmax must distribute probability over the names it has, so it will name something no matter what walks past.

That refusal mechanism turns out to matter enormously, and I will come back to it.`);
}

// =========================================================== 5. THE REVEAL
{
  const s = darkSlide();
  scatterDots(s, [
    [1.1, 1.0, 0.10], [2.4, 0.7, 0.06], [11.6, 1.2, 0.12], [12.4, 2.4, 0.07],
    [0.9, 6.3, 0.08], [12.0, 6.0, 0.10], [3.0, 6.7, 0.06], [10.6, 0.8, 0.06],
  ], ICE, 55);

  s.addText("WHERE THIS PROJECT NEARLY ENDED", {
    x: 0, y: 1.32, w: W, h: 0.34, fontFace: SANS, fontSize: 13, bold: true,
    color: ICE, charSpacing: 2.6, align: "center", isTextBox: true, margin: 0, valign: "middle",
  });

  s.addText("0.950", {
    x: 0, y: 1.9, w: W, h: 2.1, fontFace: HEAD, fontSize: 150, bold: true,
    color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0,
  });

  s.addText("Test accuracy. ResNet18 over 44 individuals, random 70:15:15 split.", {
    x: 0, y: 4.15, w: W, h: 0.4, fontFace: SANS, fontSize: 19, color: "D6E4F5",
    align: "center", isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText("Frozen features plus FAISS retrieval scored 0.959. Both looked like a finished system.", {
    x: 0, y: 4.58, w: W, h: 0.4, fontFace: SANS, fontSize: 16, color: ICE,
    align: "center", isTextBox: true, margin: 0, valign: "middle",
  });

  s.addText("It was not.", {
    x: 0, y: 5.62, w: W, h: 0.6, fontFace: HEAD, fontSize: 30, bold: true, italic: true,
    color: ORANGE, align: "center", isTextBox: true, margin: 0, valign: "middle",
  });

  s.addNotes(
`[3:05-3:30]  This is where the project nearly ended.

A ResNet18 classifier over 44 individuals scored 0.950 on its test set. The retrieval version scored 0.959. On a random split, with a conventional protocol, I had a finished system.

I did not believe it. Ninety-five per cent on hand-held zoo snapshots of birds that look, frankly, extremely similar, is not a number you should accept without asking what is in the test set.

[pause]`);
}

// ============================================================= 6. THE AUDIT
{
  const s = lightSlide();
  kicker(s, "THE AUDIT");
  title(s, "Then I looked at what was in the test set");

  s.addText("The archive is full of bursts — DSC_2743 … 2749: one camera, one moment, seven frames. A random split scatters those frames across train and test.",
    { x: M, y: 1.64, w: 5.55, h: 0.95, fontFace: SANS, fontSize: 15, color: INK,
      lineSpacing: 21, isTextBox: true, margin: 0, valign: "top" });

  spotList(s, [
    "97.8% of test photographs shared a capture session with a photograph in the gallery.",
    "13.8% had an outright near-duplicate, by perceptual hash and pixel correlation.",
    "Of the EXIF-stamped photographs, ~29% were within one second of their nearest training image.",
  ], { x: M, y: 2.76, w: 5.55, gap: 0.78, size: 14, dotColor: ORANGE });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 5.14, w: 5.55, h: 1.62, rectRadius: 0.05,
    fill: { color: DARK }, line: { type: "none" },
  });
  s.addText("Same 35 birds. Same 1,743 photographs. Same per-bird partition sizes. Same training recipe. Only the splitting rule changed.", {
    x: M + 0.32, y: 5.36, w: 4.95, h: 0.82, fontFace: SANS, fontSize: 14,
    color: "FFFFFF", lineSpacing: 20, isTextBox: true, margin: 0, valign: "top",
  });
  s.addText([
    { text: "Absolute inflation:  ", options: { color: ICE, fontSize: 13 } },
    { text: "0.531", options: { color: ORANGE, fontSize: 20, bold: true, fontFace: HEAD } },
  ], { x: M + 0.32, y: 6.16, w: 4.95, h: 0.4, fontFace: SANS,
       isTextBox: true, margin: 0, valign: "middle" });

  const iw = 6.15;
  s.addImage({ path: F("06_leakage_random_vs_session.jpg"), x: 6.85, y: 1.64, w: iw, h: iw * 0.7036 });
  caption(s, "Macro accuracy: each individual weighted equally, whatever its photograph count.",
    { x: 6.85, y: 6.06, w: iw, h: 0.4, align: "center" });

  s.addNotes(
`[3:30-4:35]  Here is what was in it. The archive is full of camera bursts — seven consecutive frames from one moment, one angle, one light. A random split scatters those frames across training and test.

The audit used signals independent of the model: perceptual hash, pixel correlation, EXIF timestamps, frame numbers. Ninety-eight per cent of test photographs shared a capture session with a gallery photograph. Fourteen per cent had an outright near-duplicate. Nearly a third of the EXIF-stamped ones were within one second of their nearest training image.

So I re-split by whole session and retrained from scratch — same birds, same photographs, same per-bird counts, same recipe. Only the splitting rule changed.

0.920 became 0.389. An inflation of 0.53. The original number was not measuring identification; it was measuring whether two frames came from the same afternoon.`);
}

// ========================================================== 7. THE PROTOCOL
{
  const s = lightSlide();
  kicker(s, "THE PROTOCOL");
  title(s, "An evaluation that cannot flatter itself");

  const items = [
    ["The unit is the encounter",
     "A capture session is one photographic occasion, inferred from filename prefix and a frame-number gap above 50, cross-checked against EXIF. 335 sessions across the colony."],
    ["Sessions are dealt into folds, never photographs",
     "Session-wise five-fold cross-validation. All 1,743 photographs are tested exactly once, each by a model that never saw its own session — against 261 under a single split."],
    ["Every bird counts once",
     "Macro averaging throughout: Medici's 291 photographs weigh exactly as much as Beau's 19. Per-image accuracy silently adopts a prior over which penguin gets photographed."],
    ["Uncertainty respects the bursts",
     "95% intervals resample capture sessions, not photographs. Fixed 80 epochs, no validation split, no early stopping, no checkpoint selection — so nothing is tuned per configuration."],
  ];
  const cw = 5.9, ch = 2.05;
  items.forEach(([h, b], i) => {
    const x = M + (i % 2) * (cw + 0.36);
    const y = 1.62 + Math.floor(i / 2) * (ch + 0.3);
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w: cw, h: ch, rectRadius: 0.05, fill: { color: CARD }, line: { type: "none" },
    });
    s.addShape(pres.ShapeType.ellipse, {
      x: x + 0.32, y: y + 0.3, w: 0.44, h: 0.44, fill: { color: BLUE }, line: { type: "none" },
    });
    s.addText(String(i + 1), {
      x: x + 0.32, y: y + 0.3, w: 0.44, h: 0.44, fontFace: HEAD, fontSize: 15, bold: true,
      color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0,
    });
    s.addText(h, {
      x: x + 0.92, y: y + 0.28, w: cw - 1.24, h: 0.48, fontFace: SANS, fontSize: 15, bold: true,
      color: INK, lineSpacing: 19, isTextBox: true, margin: 0, valign: "middle",
    });
    s.addText(b, {
      x: x + 0.32, y: y + 0.88, w: cw - 0.64, h: 1.0, fontFace: SANS, fontSize: 12.5,
      color: BODY, lineSpacing: 17.5, isTextBox: true, margin: 0, valign: "top",
    });
  });

  s.addText("Pre-registered before any run and held identical for every configuration compared — so the comparisons below measure the change, not the tuning.", {
    x: M, y: 6.28, w: W - 2 * M, h: 0.42, fontFace: SANS, fontSize: 13.5, italic: true,
    color: MUTED, align: "center", isTextBox: true, margin: 0, valign: "middle",
  });

  s.addNotes(
`[4:35-5:20]  So I rebuilt the evaluation around four rules.

One: the independent unit is the encounter, not the file. A session is one photographic occasion — recovered from filename prefixes and frame-number gaps, checked against EXIF. 335 of them across the colony.

Two: sessions get dealt into folds, never photographs. Five-fold cross-validation, so every one of the 1,743 photographs is tested exactly once by a model that never saw its session. Under a single split I could only test 261, and three birds were judged on a single photograph each.

Three: macro averaging. Medici's 291 photographs count exactly as much as Beau's nineteen — otherwise you are measuring which penguin gets photographed.

Four: confidence intervals resample sessions, not photographs, because photographs inside a burst are near-duplicates. Fixed epochs, no early stopping, no checkpoint selection.

All of it fixed before any run.`);
}

// =============================================================== 8. THE 2x2
{
  const s = lightSlide();
  kicker(s, "WHAT HELPED");
  title(s, "Which change actually did the work");

  const iw = 8.28;
  s.addImage({ path: F("12_loss_x_augmentation.jpg"), x: 4.35, y: 1.66, w: iw, h: iw * 0.4582 });

  spotList(s, [
    "Strong augmentation alone\n+0.141  [+0.105, +0.179]",
    "ArcFace alone\n+0.096  [+0.061, +0.139]",
    "ArcFace given strong aug.\n+0.029  [−0.005, +0.060]  n.s.",
  ], { x: M, y: 1.74, w: 3.3, gap: 1.0, size: 13, dotColor: BLUE });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 4.78, w: 3.3, h: 1.62, rectRadius: 0.05, fill: { color: DARK }, line: { type: "none" },
  });
  s.addText("Best configuration", {
    x: M + 0.26, y: 4.94, w: 2.8, h: 0.3, fontFace: SANS, fontSize: 11.5, bold: true,
    color: ICE, charSpacing: 1.2, isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText("0.559", {
    x: M + 0.26, y: 5.24, w: 2.8, h: 0.66, fontFace: HEAD, fontSize: 40, bold: true,
    color: "FFFFFF", isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText("ArcFace + strong augmentation,\nmacro rank-1 over 35 individuals", {
    x: M + 0.26, y: 5.88, w: 2.8, h: 0.44, fontFace: SANS, fontSize: 11,
    color: ICE, lineSpacing: 14, isTextBox: true, margin: 0, valign: "top",
  });

  s.addText([
    { text: "Augmentation is the larger single lever", options: { bold: true, color: INK } },
    { text: " — and the two are sub-additive, interaction −0.068. But ArcFace's marginal value grows with the gallery: invisible at 35 candidates, +0.116 against all 81. Metric learning shapes the embedding geometry, not the top-1 call.", options: { color: BODY } },
  ], { x: 4.35, y: 5.62, w: iw, h: 0.9, fontFace: SANS, fontSize: 13,
       lineSpacing: 18.5, isTextBox: true, margin: 0, valign: "top" });

  s.addNotes(
`[5:20-6:05]  With an honest protocol, what actually helps? I ran the full two-by-two — softmax against ArcFace, basic against strong augmentation — so each change could be attributed rather than confounded.

Strong augmentation on its own is worth +0.141. ArcFace on its own +0.096. Augmentation, not metric learning, is the bigger lever — which is the opposite of what my earlier single-split reading suggested, and it is a useful correction.

They are sub-additive: once you have strong augmentation, ArcFace adds only +0.029, and that interval includes zero.

But look at the right panel. Against all 81 colony members the two lines stay apart — ArcFace still adds +0.116. Metric learning shapes the geometry of the whole embedding rather than the top-one decision, so it earns its keep exactly as the gallery grows. Which is the regime a real colony is in.

Best configuration: 0.559.`);
}

// ================================================ 9. GALLERY SIZE + OPEN SET
{
  const s = lightSlide();
  kicker(s, "TWO HARDER QUESTIONS");
  title(s, "0.559 is the friendliest number in this talk");

  const blocks = [
    ["How big is the line-up?", BLUE,
     "0.559 assumes 35 candidates. Add the other 46 colony members as distractors — no retraining, same queries — and it falls to 0.477. ArcFace degrades least: −0.082, against the baseline's −0.166."],
    ["What if the bird is not enrolled?", ORANGE,
     "564 photographs of 46 birds no model ever trained on. Required to refuse those strangers 99% of the time, the system still correctly names only 0.123 of enrolled birds."],
  ];
  blocks.forEach(([h, c, b], i) => {
    const y = 1.62 + i * 2.0;
    dot(s, M, y + 0.09, 0.15, c);
    s.addText(h, {
      x: M + 0.38, y: y - 0.04, w: 5.2, h: 0.36, fontFace: SANS, fontSize: 15.5, bold: true,
      color: INK, isTextBox: true, margin: 0, valign: "middle",
    });
    s.addText(b, {
      x: M + 0.38, y: y + 0.4, w: 5.05, h: 1.4, fontFace: SANS, fontSize: 13.5,
      color: BODY, lineSpacing: 19, isTextBox: true, margin: 0, valign: "top",
    });
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 5.5, w: 5.6, h: 1.45, rectRadius: 0.05, fill: { color: DARK }, line: { type: "none" },
  });
  s.addText([
    { text: "Simulating strangers instead claimed 0.230", options: { bold: true, color: "FFFFFF" } },
    { text: " — an 87% overestimate. The earlier 0.80 threshold, tuned that way, actually accepts 29.7% of real strangers.", options: { color: ICE } },
  ], { x: M + 0.32, y: 5.7, w: 4.96, h: 1.06, fontFace: SANS, fontSize: 13,
       lineSpacing: 18, isTextBox: true, margin: 0, valign: "top" });

  const iw = 6.15;
  s.addImage({ path: F("10_open_set_dir_far.jpg"), x: 6.8, y: 1.62, w: iw, h: iw * 0.6563 });
  caption(s, "Strangers are real: 46 colony members the cross-validated models never trained on.",
    { x: 6.8, y: 5.86, w: iw, h: 0.4, align: "center" });

  s.addNotes(
`[6:05-6:55]  Two things 0.559 does not tell you.

First, how big is the line-up? That figure assumes 35 candidates. Add the other 46 colony members as distractors and it drops to 0.477. Notice ArcFace degrades least here — that is the same effect as the previous slide.

Second, and this is the one that matters: what if the bird in front of the camera is not enrolled at all? In use the system is asked about strangers constantly and must refuse them rather than pick the nearest name.

I used 564 photographs of 46 birds no model had ever trained on. At the threshold where real strangers are refused 99 times in 100, the system correctly names 0.123 of enrolled birds. Closed-set 0.559 becomes 0.123.

And an earlier version of this analysis simulated strangers by hiding a bird's own prototype. That claimed 0.230 — an 87% overestimate, because the bird had been in training and pushed away from every other identity. Realistic evaluation of unknowns is not optional.`);
}

// ======================================================= 10. SESSIONS, NOT PHOTOS
{
  const s = lightSlide();
  kicker(s, "THE CENTRAL FINDING");
  title(s, "Nicki and Gonzo");

  const pair = [
    ["Nicki", "53 photographs · 3 sessions", "0.189", ORANGE],
    ["Gonzo", "52 photographs · 13 sessions", "0.827", BLUE],
  ];
  pair.forEach(([n, meta, acc, c], i) => {
    const y = 1.64 + i * 1.24;
    s.addShape(pres.ShapeType.roundRect, {
      x: M, y, w: 5.25, h: 1.06, rectRadius: 0.05, fill: { color: CARD }, line: { type: "none" },
    });
    dot(s, M + 0.28, y + 0.44, 0.16, c);
    s.addText(n, {
      x: M + 0.62, y: y + 0.13, w: 2.3, h: 0.4, fontFace: HEAD, fontSize: 21, bold: true,
      color: INK, isTextBox: true, margin: 0, valign: "middle",
    });
    s.addText(meta, {
      x: M + 0.62, y: y + 0.55, w: 2.9, h: 0.32, fontFace: SANS, fontSize: 12.5,
      color: MUTED, isTextBox: true, margin: 0, valign: "middle",
    });
    s.addText(acc, {
      x: M + 3.6, y: y + 0.2, w: 1.4, h: 0.66, fontFace: HEAD, fontSize: 30, bold: true,
      color: c, align: "right", isTextBox: true, margin: 0, valign: "middle",
    });
  });

  s.addText("Almost the same number of files. Four times the accuracy.", {
    x: M, y: 4.14, w: 5.4, h: 0.54, fontFace: SANS, fontSize: 15, bold: true, color: INK,
    lineSpacing: 21, isTextBox: true, margin: 0, valign: "middle",
  });

  spotList(s, [
    "Grouped by session count: 3 sessions (8 birds) 0.186  ·  4–6 (13 birds) 0.618  ·  7+ (14 birds) 0.717.",
    "Controlling for photograph count, sessions still predict accuracy: partial ρ = 0.518, p = 0.002. Controlling for sessions, photographs do not: ρ = 0.224, p = 0.203.",
    "Metric learning lifts every bucket but cannot rescue the three-session birds — from 0.081 only to 0.186.",
  ], { x: M, y: 4.76, w: 5.4, gap: 0.72, size: 12.5, dotColor: BLUE, dotD: 0.11 });

  const iw = 6.25;
  s.addImage({ path: F("14_photos_vs_sessions.jpg"), x: 6.66, y: 1.68, w: iw, h: iw * 0.6253 });
  caption(s, "One point per colony member. Photograph count runs across; capture sessions run up.",
    { x: 6.66, y: 5.74, w: iw, h: 0.4, align: "center" });

  s.addNotes(
`[6:55-7:45]  This is the finding I care most about.

Nicki: 53 photographs, three capture sessions, identified correctly 19% of the time. Gonzo: 52 photographs, thirteen sessions, 83%. Almost the same number of files. Four times the accuracy.

That is not a coincidence. Group the birds by session count and you get 0.186, 0.618, 0.717. And because session count and photograph count are themselves correlated, I separated them with partial correlations: controlling for photograph count, sessions still predict accuracy at rho 0.52, p equals 0.002. Controlling for sessions, photograph count does not predict anything — p equals 0.20.

Extra frames from an existing burst add nothing. A photograph on a new day, in new light, adds a great deal.

And metric learning cannot fix it: the three-session birds go from 0.081 to 0.186 and stay unusable. That gap needs a camera, not a loss function.`);
}

// ===================================================== 11. THE RECOMMENDATION
{
  const s = lightSlide();
  kicker(s, "WHAT TO DO ABOUT IT");
  title(s, "So count encounters, not files");

  const recs = [
    ["Target four sessions per bird", "Provisional — the 4–6 and 7+ groups were pooled, and sampling effort was not experimentally assigned. It is a starting point for prospective validation, not a validated threshold."],
    ["53 of 81 birds fall short", "Reaching four for everyone needs 116 further individual capture encounters — roughly eight outings at about fifteen birds each, and they must fall on different days."],
  ];
  recs.forEach(([h, b], i) => {
    const x = M + i * (5.9 + 0.36);
    dot(s, x, 1.7, 0.14, i ? ORANGE : BLUE);
    s.addText(h, {
      x: x + 0.36, y: 1.58, w: 5.4, h: 0.34, fontFace: SANS, fontSize: 15, bold: true,
      color: INK, isTextBox: true, margin: 0, valign: "middle",
    });
    s.addText(b, {
      x: x + 0.36, y: 1.98, w: 5.35, h: 0.86, fontFace: SANS, fontSize: 13,
      color: BODY, lineSpacing: 18, isTextBox: true, margin: 0, valign: "top",
    });
  });

  const iw = 9.4;
  s.addImage({ path: F("13_colony_sessions_per_individual.jpg"), x: (W - iw) / 2, y: 2.98, w: iw, h: iw * 0.3890 });

  s.addText("Vary the day, the light, the distance and the social context — and record a session ID at capture.", {
    x: M, y: 6.68, w: W - 2 * M, h: 0.4, fontFace: SANS, fontSize: 13, italic: true,
    color: MUTED, align: "center", isTextBox: true, margin: 0, valign: "middle",
  });

  s.addNotes(
`[7:45-8:25]  Which turns the result into a collection instruction.

The contrast between the three-session and four-to-six-session groups supports a provisional target of at least four separate capture occasions per bird. Provisional — I pooled four, five and six, and I did not assign sampling effort experimentally. It is a starting point for prospective validation.

Applied to the whole colony: 28 of 81 birds already reach four sessions. 53 do not. Closing that needs 116 further individual capture encounters — about eight outings at fifteen birds each.

And the crucial constraint: those outings must be on different days. More frames from an existing visit do nothing. Vary the light, the distance, the angle, the social context — and record a session ID at capture, so next time session independence is observable rather than reconstructed from filenames.`);
}

// ======================================================= 12. WHAT IS DEPLOYED
{
  const s = lightSlide();
  kicker(s, "THE DELIVERABLE");
  title(s, "What is deployed, and what it is for");

  const cols = [
    ["Built and measured", BLUE, [
      "The extractor retrained with the identical recipe on all 2,304 photographs of 79 individuals — no held-out set, because the estimate already exists.",
      "A gallery enrolling all 81 colony members and all 2,307 photographs, one L2-normalised prototype apiece.",
      "An acceptance threshold of 0.938, measured at 5% false-accept against real strangers. Smew and Skunk are enrolled without ever being trained on.",
    ]],
    ["Not yet measured", ORANGE, [
      "The chain from an unconstrained photograph through localisation to an identity. Every number here is measured on the archive as photographed.",
      "Rejection of blurred, rear-facing or non-penguin inputs — once all 81 are enrolled, that is what \"unknown\" actually means, and the threshold was never calibrated for it.",
      "Rank-5 against the full 81-way gallery; the 35-way 0.782 cannot be assumed to transfer.",
    ]],
  ];
  cols.forEach(([h, c, items], i) => {
    const x = M + i * (5.9 + 0.36);
    dot(s, x, 1.7, 0.15, c);
    s.addText(h, {
      x: x + 0.38, y: 1.58, w: 5.0, h: 0.34, fontFace: SANS, fontSize: 16, bold: true,
      color: INK, isTextBox: true, margin: 0, valign: "middle",
    });
    items.forEach((t, j) => {
      s.addText(t, {
        x: x + 0.38, y: 2.12 + j * 1.14, w: 5.32, h: 1.06, fontFace: SANS, fontSize: 13,
        color: BODY, lineSpacing: 18, isTextBox: true, margin: 0, valign: "top",
      });
    });
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 5.62, w: W - 2 * M, h: 1.18, rectRadius: 0.05, fill: { color: DARK }, line: { type: "none" },
  });
  s.addText([
    { text: "Decision support, not autonomous identification.  ", options: { bold: true, color: "FFFFFF" } },
    { text: "A ranked shortlist a keeper confirms — never an identity written straight into a welfare, veterinary or breeding record.", options: { color: ICE } },
  ], { x: M + 0.4, y: 5.86, w: W - 2 * M - 0.8, h: 0.72, fontFace: SANS, fontSize: 15,
       align: "center", lineSpacing: 21, isTextBox: true, margin: 0, valign: "middle" });

  s.addNotes(
`[8:25-9:00]  What I am actually handing over.

Cross-validation gives an estimate, not a shippable model, so the extractor is retrained with the identical recipe on every photograph of 79 birds, and the gallery enrols all 81 individuals — including Smew and Skunk, who have one and two photographs and were never trained on. That is the retrieval design earning its keep. Acceptance threshold 0.938.

What I have not measured, and want to be explicit about: the end-to-end chain. Every number in this talk is measured on the archive as photographed — there is no detector in the identification path. And once all 81 birds are enrolled, the realistic unknown is no longer an unenrolled bird; it is a blurred photograph, or a back, or something that is not a penguin. The threshold has never been calibrated for that.

Which is why the honest framing is decision support. A ranked shortlist a keeper confirms — not an identity written straight into a record.`);
}

// ============================================================ 13. TAKEAWAYS
{
  const s = darkSlide();
  scatterDots(s, [
    [12.2, 0.6, 0.12], [11.5, 1.5, 0.07], [0.42, 5.9, 0.09], [12.6, 4.4, 0.08], [4.9, 0.35, 0.06],
  ], ICE, 60);

  s.addText("IN CLOSING", {
    x: M, y: 0.62, w: 6.0, h: 0.32, fontFace: SANS, fontSize: 12.5, bold: true,
    color: ICE, charSpacing: 2.4, isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText("Three things to take away", {
    x: M, y: 1.02, w: 9.0, h: 0.7, fontFace: HEAD, fontSize: 36, bold: true,
    color: "FFFFFF", isTextBox: true, margin: 0, valign: "middle",
  });

  const takes = [
    ["In a burst-structured archive, the independent unit is the encounter — not the file.",
     "Ignoring that inflated macro rank-1 by 0.531. This is not a penguin problem; it is true of any ecological image set built from bursts, repeat visits or shared conditions."],
    ["Method took 0.390 to 0.559. Only a camera moves the three-session birds off 0.186.",
     "Augmentation was the larger lever, ArcFace's value grows with the gallery — and neither can manufacture a photograph taken on a different day."],
    ["Made to refuse real strangers, 0.559 becomes 0.123.",
     "That gap, not the closed-set figure, describes deployment readiness. So it ships as a ranked suggestion for a human, and says so."],
  ];
  takes.forEach(([h, b], i) => {
    const y = 2.12 + i * 1.36;
    s.addShape(pres.ShapeType.ellipse, {
      x: M, y: y + 0.02, w: 0.46, h: 0.46, fill: { color: ORANGE }, line: { type: "none" },
    });
    s.addText(String(i + 1), {
      x: M, y: y + 0.02, w: 0.46, h: 0.46, fontFace: HEAD, fontSize: 16, bold: true,
      color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0,
    });
    s.addText(h, {
      x: M + 0.72, y, w: 11.2, h: 0.44, fontFace: SANS, fontSize: 16.5, bold: true,
      color: "FFFFFF", isTextBox: true, margin: 0, valign: "middle",
    });
    s.addText(b, {
      x: M + 0.72, y: y + 0.48, w: 11.2, h: 0.72, fontFace: SANS, fontSize: 13,
      color: ICE, lineSpacing: 18.5, isTextBox: true, margin: 0, valign: "top",
    });
  });

  s.addText("Thank you.", {
    x: M, y: 6.24, w: 3.0, h: 0.44, fontFace: HEAD, fontSize: 22, bold: true,
    color: "FFFFFF", isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText("Aoao Guo  ·  code and analysis: github.com/aoaoguo2003/pgs\nWith thanks to Robin Freeman, ZSL London Zoo, and the volunteer photographers.", {
    x: 4.0, y: 6.16, w: 8.5, h: 0.6, fontFace: SANS, fontSize: 12, color: ICE,
    align: "right", lineSpacing: 17, isTextBox: true, margin: 0, valign: "middle",
  });

  s.addNotes(
`[9:00-9:50]  Three things to take away.

First, the methodological one, and it travels well beyond penguins. In an archive built from bursts, repeat visits or shared sampling conditions, the independent unit is the encounter, not the file. Ignoring that inflated my headline by 0.53.

Second, method and data are complementary, not alternatives. Better training took me from 0.390 to 0.559 — a real gain, worth having. But nothing in the loss function can rescue a bird photographed on three occasions. Only a camera does that.

Third, the moment the system has to say "I don't know" to a bird it has never seen, 0.559 becomes 0.123. That number, not the closed-set one, is what deployment readiness means — so it ships as a ranked suggestion for a keeper to confirm, and it says so out loud.

Thank you. The code and all the analysis are on GitHub, and I am happy to take questions.`);
}

pres.writeFile({ fileName: path.join(D, "penguin_reid_final_pre.pptx") })
  .then((f) => console.log("wrote", f));
