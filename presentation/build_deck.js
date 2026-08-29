// Final-presentation deck: "Automatic Identification of Humboldt Penguins at London Zoo"
// 10 minutes (600 s) + a backup section for Q&A.
//
// Every number here comes from the dissertation and analysis/artifacts/RESULTS.md.
// Framing: lead with the leakage result (the study's only controlled experiment and
// its transferable contribution), then the session finding, then the honest ladder.

const pptxgen = require("pptxgenjs");
const path = require("path");
const L = require("./lib.js");
const K = require("./components.js");
const { C, F, W, H, M } = L;

const A = path.join(__dirname, "assets");
const pres = L.newDeck(pptxgen, {
  title: "Automatic Identification of Humboldt Penguins at London Zoo",
  subject: "BIOS0057 Research Project — MSc Ecology and Data Science, UCL",
});

let n = 0;
const RUN = "Automatic identification of Humboldt penguins · ZSL London Zoo";

// ===========================================================================
// 1 — TITLE  (15 s)
// ===========================================================================
{
  const s = L.darkSlide(pres);
  const PANEL = 4.75;                       // width of the half-bleed photo panel
  L.coverImage(s, `${A}/penguin_title.png`, { x: W - PANEL, y: 0, w: PANEL, h: H });
  s.addText("Automatic Identification of\nHumboldt Penguins at London Zoo", {
    x: M, y: 1.5, w: W - PANEL - M - 0.5, h: 2.3,
    fontFace: F.head, fontSize: 34, bold: true, color: C.white,
    isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.02,
  });
  s.addText("What a photograph can tell you about which bird it is — and what it cannot", {
    x: M, y: 3.72, w: W - PANEL - M - 0.7, h: 0.8,
    fontFace: F.body, fontSize: 17, color: "9FC0E4",
    isTextBox: true, margin: 0, valign: "top",
  });
  // the session-dot motif, introduced here and repeated wherever sessions matter
  L.dots(s, { x: M, y: 4.78, n: 13, color: C.blue, d: 0.15, gap: 0.1 });
  s.addText(
    "Candidate TDYK3   ·   MSc Ecology and Data Science   ·   BIOS0057\n" +
    "Supervisor: Robin Freeman   ·   Division of Biosciences, UCL",
    {
      x: M, y: 5.4, w: W - PANEL - M - 0.5, h: 0.9,
      fontFace: F.body, fontSize: 13, color: "C9D6E6",
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.25,
    }
  );
  s.addNotes("My first result on this project was 0.920 — nine penguins in ten identified correctly from a photograph. It was wrong. The reason it was wrong is most of what I want to tell you in the next ten minutes.");
  n++;
}

// ===========================================================================
// 2 — MOTIVATION  (40 s)
// ===========================================================================
{
  const s = L.lightSlide(pres);
  // half-bleed image on the right
  const bs = L.imageSize(`${A}/band_sheet.jpg`);
  const bsW = W - 8.15;
  s.addImage({ path: `${A}/band_sheet.jpg`, x: 8.15, y: 0, w: bsW, h: bsW * bs[1] / bs[0] });
  s.addShape("rect", { x: 8.15, y: bsW * bs[1] / bs[0], w: bsW, h: H - bsW * bs[1] / bs[0],
    fill: { color: C.bg }, line: { color: C.bg, width: 0 } });
  L.caption(s, "The colony's identification sheet: five band colours per bird.\nNicki and Greyjoy — two birds you will meet again — are on it.",
    { x: 8.15, y: bsW * bs[1] / bs[0] + 0.11, w: 5.0, size: 10 });

  L.kicker(s, "Why this problem");
  L.title(s, "Identity is currently worn,\nnot read from the bird", { h: 1.35 });
  L.bullets(s, [
    "Bands can be hidden by posture, another bird, or the angle",
    "In king penguins, ten years of banding cost survival and breeding success (Saraux et al. 2011) — not directly transferable to captive Humboldts, but a marker is not automatically neutral",
    "Humboldts have been told apart by their breast spots since Scholten (1989)",
    "African penguins use ventral dot patterns to recognise each other (Baciadonna et al. 2024) — the cue is already doing this job",
  ], { x: M, y: 2.15, w: 7.15, h: 4.1, size: 15, space: 17 });

  L.foot(s, ++n, RUN);
  s.addNotes("London Zoo tells its 81 Humboldt penguins apart with coloured flipper bands, read off this laminated sheet. Bands work, but they can be hidden by posture or another bird — and in king penguins, ten years of banding cost survival and breeding success. That does not transfer directly to captive Humboldts; it just says a marker is not automatically neutral. The alternative is already on the bird: African penguins use their ventral dot patterns to recognise each other, so I am asking a model to read a cue the species already reads.");
}

// ===========================================================================
// 3 — THE ARCHIVE  (50 s)
// ===========================================================================
{
  const s = L.lightSlide(pres);
  L.kicker(s, "The data");
  L.title(s, "2,307 volunteer photographs — but the unit of evidence\nis the encounter, not the file", { h: 1.3, size: 25 });

  const stats = [
    { v: "2,307", l: "photographs", sub: "81 birds, 1 to 291 each" },
    { v: "81", l: "individuals", sub: "the whole colony" },
    { v: "35", l: "evaluated", sub: "≥16 photos and ≥3 sessions" },
    { v: "335", l: "capture sessions", sub: "258 across the 35" },
  ];
  stats.forEach((st, i) => L.stat(s, {
    x: M + i * 2.16, y: 1.98, w: 2.05,
    value: st.v, label: st.l, sub: st.sub,
    color: i === 2 ? C.orange : C.navy, size: 40, labelSize: 11.5,
  }));

  // two frames of Ping: same camera prefix, frame numbers two apart, so one
  // capture session under this project's own rule. This is the whole argument.
  {
    // identical boxes, cover-cropped: sizing them from one photo's aspect would
    // stretch the other and leave its residual border showing
    const pw = 1.95, ph = 2.45;
    const x0 = W - M - 2 * pw - 0.14;
    L.coverImage(s, `${A}/penguin_session_a.png`, { x: x0, y: 3.62, w: pw, h: ph });
    L.coverImage(s, `${A}/penguin_session_b.png`, { x: x0 + pw + 0.14, y: 3.62, w: pw, h: ph });
    // one bracket over the pair: these two frames are a single session
    s.addShape("rect", { x: x0, y: 3.44, w: 2 * pw + 0.14, h: 0.05,
      fill: { color: C.blue }, line: { color: C.blue, width: 0 } });
    s.addText("one capture session — two frames of Ping", {
      x: x0, y: 3.06, w: 2 * pw + 0.14, h: 0.32,
      fontFace: F.body, fontSize: 12, bold: true, color: C.blue, align: "center",
      isTextBox: true, margin: 0, valign: "bottom",
    });
    L.caption(s, "Same light, same ground, same posture. A random split can put one of these in training and the other in test.",
      { x: x0, y: 3.68 + ph, w: 2 * pw + 0.14, size: 10, align: "center" });
  }

  L.card(s, { x: M, y: 4.05, w: W - 2 * M - 4.35, h: 2.2, fill: C.panel });
  s.addText("A capture session = every photograph of one bird from a single photographic encounter.", {
    x: M + 0.3, y: 4.24, w: W - 2 * M - 4.95, h: 0.56,
    fontFace: F.body, fontSize: 15.5, bold: true, color: C.navy,
    isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText(
    "Inferred per bird from the camera filename prefix and frame number: a new session starts when the gap to the previous " +
    "frame exceeds 50. Checked against EXIF timestamps where present. Frames inside one session share light, background, " +
    "viewpoint and posture — they are correlated observations, not independent evidence of how a bird looks on a new day.",
    {
      x: M + 0.3, y: 4.88, w: W - 2 * M - 4.95, h: 1.25,
      fontFace: F.body, fontSize: 12.5, color: C.ink,
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.1,
    }
  );

  L.foot(s, ++n, RUN);
  s.addNotes("2,307 photographs of all 81 birds, taken by volunteers during husbandry, not to a research protocol — counts run from 1 to 291. Thirty-five birds clear both inclusion rules: the better-photographed 43% of the colony. The other 46 are never queries; they are gallery distractors and, later, genuine strangers. The definition at the bottom is what matters. A capture session is one photographic encounter with one bird, inferred from the camera's frame numbering. The two frames on the right are one session: same light, same ground, same posture. They are not independent samples.");
}

// ===========================================================================
// 4 — THE LEAKAGE RESULT  (85 s)
// ===========================================================================
{
  const s = L.lightSlide(pres);
  L.kicker(s, "Result 1 — the controlled experiment");
  L.title(s, "Change only the split rule, and 0.920 becomes 0.389", { h: 0.75 });

  L.fitImage(s, `${A}/06_leakage_random_vs_session_notitle.png`,
    { x: 5.35, y: 1.28, w: 7.45, h: 5.35 });

  L.bullets(s, [
    "Same 35 birds, same 1,743 photographs, same per-bird partition sizes, same training recipe",
    "Only difference: whole capture sessions may no longer straddle the split",
    "Rank-5 and 1-NN collapse the same way — not a quirk of one metric",
  ], { x: M, y: 1.4, w: 4.45, h: 2.4, size: 14, space: 11 });

  L.card(s, { x: M, y: 4.0, w: 4.45, h: 2.35, fill: C.panel });
  s.addText("Audited before any model ran", {
    x: M + 0.25, y: 4.16, w: 3.95, h: 0.3,
    fontFace: F.body, fontSize: 13, bold: true, color: C.orange,
    isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText([
    { text: "97.8%", options: { bold: true, color: C.navy } },
    { text: " of random-split test photos shared a capture session with a gallery photo; ", options: {} },
    { text: "13.8%", options: { bold: true, color: C.navy } },
    { text: " had an outright near-duplicate — measured by perceptual hash, pixel correlation and EXIF time, none of which touch the model.", options: {} },
  ], {
    x: M + 0.25, y: 4.52, w: 3.95, h: 1.7,
    fontFace: F.body, fontSize: 12.5, color: C.ink,
    isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.1,
  });

  L.foot(s, ++n, RUN);
  s.addNotes("Here is the experiment the whole project turns on. Birds, photographs, per-bird counts and training recipe all held fixed, and exactly one thing changed: whether a test photograph may come from a capture session the gallery has already seen. Under the conventional random split, rank-one accuracy — every bird weighted equally — is 0.920. Under the session-disjoint split, it is 0.389: an inflation of 0.531 attributable to the partitioning rule alone. Rank-five and nearest-neighbour move with it. And I can show the entanglement without reference to any model: 97.8% of the randomly assigned test photographs shared a capture session with a gallery photograph, and 13.8% had a near-duplicate. So the random split was measuring recognition of a familiar encounter, not identification on a new occasion.");
}

// ===========================================================================
// 5 — THE PROTOCOL  (50 s)
// ===========================================================================
{
  const s = L.lightSlide(pres);
  L.kicker(s, "What replaces it");
  L.title(s, "An evaluation whose unit is the encounter and whose\nweight is the individual", { h: 1.25, size: 25 });

  const items = [
    {
      t: "Session-wise 5-fold cross-validation",
      d: "Whole sessions are dealt to folds, largest bird and largest session first. Folds of 349 / 350 / 351 / 347 / 346 photographs. " +
         "Every one of the 1,743 photographs is tested exactly once by a model that never saw its session — the evaluation script asserts it.",
    },
    {
      t: "Macro metrics",
      d: "Accuracy is computed per bird and then averaged with equal weight, so Cooper's 127 photographs cannot cover for a bird with 18.",
    },
    {
      t: "Bootstrap that resamples sessions, not photographs",
      d: "2,000 replicates, capture sessions resampled within each bird, and the same resampled sessions applied to both arms of every " +
         "comparison — so the reported effects are paired differences, not overlapping independent intervals.",
    },
  ];
  let y = 1.95;
  items.forEach((it, i) => {
    s.addShape("ellipse", { x: M, y: y + 0.02, w: 0.36, h: 0.36,
      fill: { color: C.blue }, line: { color: C.blue, width: 0 } });
    s.addText(String(i + 1), { x: M, y: y + 0.02, w: 0.36, h: 0.36,
      fontFace: F.body, fontSize: 13, bold: true, color: C.white, align: "center",
      isTextBox: true, margin: 0, valign: "middle" });
    s.addText(it.t, { x: M + 0.58, y, w: W - 2 * M - 0.58, h: 0.34,
      fontFace: F.body, fontSize: 15.5, bold: true, color: C.navy,
      isTextBox: true, margin: 0, valign: "middle" });
    s.addText(it.d, { x: M + 0.58, y: y + 0.36, w: W - 2 * M - 0.7, h: 0.86,
      fontFace: F.body, fontSize: 12.5, color: C.ink,
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.08 });
    y += 1.5;
  });

  L.foot(s, ++n, RUN);
  s.addNotes("So what replaces it. Three things. First, session-wise five-fold cross-validation: complete sessions are dealt to folds, so no session is ever split, and every one of the 1,743 photographs is tested exactly once by a model that never saw its session. That is not a claim in prose — the evaluation script asserts it and refuses to run without the session map. Second, every number is macro: one bird, one vote. Third, the intervals resample capture sessions rather than photographs, and apply the same resampled sessions to both arms of a comparison, so these are paired differences.");
}

// ===========================================================================
// 6 — ATTRIBUTION 2x2  (60 s)
// ===========================================================================
{
  const s = L.lightSlide(pres);
  L.kicker(s, "Result 2 — which change did the work");
  L.title(s, "Augmentation is the larger lever; metric learning\nearns its place only as the gallery grows", { h: 1.2, size: 25 });

  L.fitImage(s, `${A}/12_loss_x_augmentation_notitle.png`,
    { x: M, y: 1.95, w: W - 2 * M - 3.55, h: 4.15 });

  L.card(s, { x: W - M - 3.4, y: 1.95, w: 3.4, h: 4.15, fill: C.panel });
  s.addText("Paired simple effects, rank-1", {
    x: W - M - 3.15, y: 2.12, w: 2.9, h: 0.3,
    fontFace: F.body, fontSize: 12.5, bold: true, color: C.navy,
    isTextBox: true, margin: 0, valign: "middle",
  });
  const eff = [
    ["Strong augmentation\nunder softmax", "+0.141", "[0.105, 0.179]", C.orange],
    ["ArcFace\nunder basic aug.", "+0.096", "[0.061, 0.139]", C.blue],
    ["ArcFace given strong,\n35 candidates", "+0.029", "[−0.005, 0.060]  n.s.", C.muted],
    ["ArcFace given strong,\n81 candidates", "+0.116", "[0.082, 0.148]", C.blue],
  ];
  let ey = 2.55;
  eff.forEach(([lab, val, ci, col]) => {
    s.addText(lab, { x: W - M - 3.15, y: ey, w: 1.85, h: 0.56,
      fontFace: F.body, fontSize: 10.5, color: C.ink,
      isTextBox: true, margin: 0, valign: "middle", lineSpacingMultiple: 0.95 });
    s.addText(val, { x: W - M - 1.28, y: ey, w: 1.05, h: 0.32,
      fontFace: F.head, fontSize: 16, bold: true, color: col, align: "right",
      isTextBox: true, margin: 0, valign: "middle" });
    s.addText(ci, { x: W - M - 1.95, y: ey + 0.31, w: 1.72, h: 0.24,
      fontFace: F.body, fontSize: 9, color: C.muted, align: "right",
      isTextBox: true, margin: 0, valign: "middle" });
    ey += 0.82;
  });
  s.addText("Highest of four configurations: ArcFace + strong, 0.559 [0.517, 0.610].", {
    x: W - M - 3.15, y: 5.75, w: 2.9, h: 0.4,
    fontFace: F.body, fontSize: 10, color: C.muted,
    isTextBox: true, margin: 0, valign: "middle", lineSpacingMultiple: 0.95,
  });

  L.foot(s, ++n, RUN);
  s.addNotes("Under that protocol I ran a full two-by-two: objective crossed with augmentation, five folds each, twenty runs. The baseline scores 0.390, close to the single-split 0.389 — but different recipes, so not a validation. Strong augmentation is worth plus 0.141; ArcFace alone plus 0.096. They are sub-additive: once strong augmentation is there, ArcFace adds only 0.029 and that interval crosses zero, so at 35 candidates I cannot claim the loss is doing significant work. Widen the gallery to all 81 — the right-hand panel — and ArcFace is worth plus 0.116, clear of zero, because metric learning shapes the embedding geometry rather than the top-one call. That is the regime a real colony is in.");
}

// ===========================================================================
// 7 — SESSIONS, NOT PHOTOGRAPHS  (85 s)
// ===========================================================================
{
  const s = L.lightSlide(pres);
  L.kicker(s, "Result 3 — the central finding");
  L.title(s, "Identifiability tracks how many separate occasions a bird\nwas photographed on, not how many photographs exist", { h: 1.2, size: 25 });

  L.fitImage(s, `${A}/08_accuracy_vs_sessions_notitle.png`,
    { x: M, y: 1.9, w: 7.7, h: 4.3 });

  K.sessionCompare(s, {
    x: 8.45, y: 2.05, w: 4.3, rowH: 1.72,
    birds: [
      { name: "Nicki", photos: 53, sessions: 3, acc: "0.189", color: C.orange },
      { name: "Gonzo", photos: 52, sessions: 13, acc: "0.827", color: C.blue },
    ],
  });
  L.caption(s,
    "Each figure is the fraction of that bird's photographs identified correctly. Illustration, not evidence — the evidence is the " +
    "partial rank correlation across all 35 birds: holding photograph count constant, sessions still predict accuracy " +
    "(ρ = 0.518, P = 0.002); holding sessions constant, photograph count does not reach significance (ρ = 0.224, P = 0.203) — " +
    "which does not exclude a modest effect this study is underpowered to detect.",
    { x: 8.45, y: 5.62, w: 4.3, size: 10 });

  L.foot(s, ++n, RUN);
  s.addNotes("This is the finding I care most about. Group the 35 birds by how many separate occasions they were photographed on: three sessions, 0.186; four to six, 0.618; seven or more, 0.717. The same ordering holds in all four configurations. Nicki and Gonzo make it concrete: 53 photographs against 52, but three sessions against thirteen, and 19% against 83%. That pair is an illustration, not the evidence. Sessions and photograph count are correlated at rho 0.663, so I partial one out. Sessions survive at 0.518; photograph count falls to 0.224 and does not reach significance — with 35 birds I cannot exclude a modest photograph effect, only say sessions are the stronger one. And one caution I will give you myself: a three-session bird's prototype is built from one or two gallery sessions, so part of this gradient is my design rather than the birds. It points the same way for collection either way.");
}

// ===========================================================================
// 8 — THE HONEST LADDER  (65 s)
// ===========================================================================
{
  const s = L.lightSlide(pres);
  L.kicker(s, "Result 4 — deployment readiness");
  L.title(s, "One set of models, three questions — and only one of them\ndescribes deployment", { h: 1.2, size: 25 });

  K.staircase(s, {
    x: M, y: 2.05, w: 7.5, h: 4.4,
    steps: [
      { q: "35 candidates,\nclosed set", v: 0.559, note: "the reference —\nhighest of the four\nconfigurations", color: C.blue },
      { q: "…now rank against\nall 81 colony\ncandidates", v: 0.477, note: "same 1,743 queries;\n46 identities added\nas distractors", color: C.blue },
      { q: "…now strangers must\nbe refused 99% of\nthe time", v: 0.123, note: "DIR at 1% false-accept,\nagainst 564 photographs\nof 46 never-trained birds", color: C.orange },
    ],
  });

  L.caption(s, "Each of the two is one change away from the first, not a chain: the gallery grows, or strangers must be refused. "
    + "All three come from the same five cross-validated models and are macro over the 35 individuals.",
    { x: M, y: 6.42, w: 7.5, size: 10.5 });
  L.card(s, { x: 8.5, y: 2.05, w: 4.22, h: 2.5, fill: C.panel });
  s.addText("The shortcut I did not take", {
    x: 8.75, y: 2.23, w: 3.72, h: 0.3,
    fontFace: F.body, fontSize: 13, bold: true, color: C.orange,
    isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText(
    "Simulating strangers by hiding a bird's own prototype reports 0.230 instead of 0.123 — an overstatement of 87%. " +
    "Both numbers come out of the same evaluation run, so this is a controlled comparison, not two studies stitched together.",
    { x: 8.75, y: 2.59, w: 3.72, h: 1.85,
      fontFace: F.body, fontSize: 12, color: C.ink,
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.1 }
  );
  s.addText("“The number that describes\ndeployment readiness\nis 0.123, not 0.559.”", {
    x: 8.5, y: 4.8, w: 4.22, h: 1.35,
    fontFace: F.head, fontSize: 16, italic: true, bold: true, color: C.navy,
    isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.05,
  });
  L.caption(s, "The deployed configuration's five-candidate shortlist contains the right bird 78.2% of the time (35 candidates; "
    + "softmax + strong is better at rank-5, at 0.809).",
    { x: 8.5, y: 6.2, w: 4.22, size: 10.5 });

  L.foot(s, ++n, RUN);
  s.addNotes("I want to be the one who tells you how good this is not. These are the same five models asked three questions. Against 35 candidates, closed set, the best configuration reaches 0.559. Rank the same queries against all 81 colony identities and it falls to 0.477 — how often the right bird outranks eighty alternatives, not accuracy across all 81 birds. Then the real test: it must be able to refuse. Using the 564 photographs of 46 birds the models never trained on, at a one percent false-accept rate only 12.3% of photographs of enrolled birds are both accepted and correctly named. Simulate the strangers instead — the conventional shortcut — and it reports 0.230, an 87% overstatement. Both come from the same run. The number that describes deployment readiness is 0.123, not 0.559.");
}

// ===========================================================================
// 9 — THE SYSTEM  (50 s)
// ===========================================================================
{
  const s = L.lightSlide(pres);
  L.kicker(s, "What exists");
  L.title(s, "Retrieval, not classification — so a new bird costs\nan enrolment, not a retraining", { h: 1.2, size: 25 });

  K.pipeline(s, { x: M + 1.55, y: 1.98, w: 6.1, stepH: 0.62, gap: 0.2 });
  {
    const d = L.imageSize(`${A}/penguin_query.png`);
    const pw = 1.3, ph = pw * d[1] / d[0];
    s.addImage({ path: `${A}/penguin_query.png`, x: M, y: 1.98, w: pw, h: ph });
    // the arrow points at the first box, not at the middle of the photograph
    s.addShape("rightArrow", { x: M + pw + 0.06, y: 1.98 + 0.31 - 0.08, w: 0.34, h: 0.16,
      fill: { color: C.rule }, line: { color: C.rule, width: 0 } });
    L.caption(s, "one photograph,\nuncropped, as taken",
      { x: M, y: 2.04 + ph, w: pw + 0.3, size: 9.5 });
  }

  L.card(s, { x: 8.35, y: 1.98, w: 4.4, h: 2.25, fill: C.panel });
  s.addText([
    { text: "79", options: { fontFace: F.head, fontSize: 30, bold: true, color: C.navy } },
    { text: "  trained on          ", options: { fontSize: 13, color: C.ink } },
    { text: "81", options: { fontFace: F.head, fontSize: 30, bold: true, color: C.orange } },
    { text: "  enrolled", options: { fontSize: 13, color: C.ink } },
  ], { x: 8.6, y: 2.13, w: 3.9, h: 0.55, isTextBox: true, margin: 0, valign: "middle" });
  s.addText(
    "Smew and Skunk have one and two photographs. Never trained on, in the gallery, searchable. A softmax head would need a new " +
    "output layer and a full retrain for each arrival. The deployed model has no held-out partition of its own — the cross-validated " +
    "0.559 is its estimate.",
    { x: 8.6, y: 2.68, w: 3.9, h: 1.45,
      fontFace: F.body, fontSize: 11, color: C.ink,
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.08 }
  );

  L.card(s, { x: 8.35, y: 4.46, w: 4.4, h: 1.95, fill: C.panel });
  s.addText("It refuses in two ways", {
    x: 8.6, y: 4.64, w: 3.9, h: 0.3,
    fontFace: F.body, fontSize: 13, bold: true, color: C.orange,
    isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText(
    "Below 0.938 it returns “not a bird I know” and asks for a clearer photograph. Above it, but with a top-two margin under 0.05, " +
    "it returns a shortlist and asks the keeper to confirm. It never emits a name it is not confident in.",
    { x: 8.6, y: 5.0, w: 3.9, h: 1.3,
      fontFace: F.body, fontSize: 11.5, color: C.ink,
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.08 }
  );

  L.foot(s, ++n, RUN);
  s.addNotes("What exists is a retrieval system, not a classifier. A photograph becomes a 512-dimensional vector, compared by cosine similarity against one prototype per enrolled identity. I chose retrieval for two properties a softmax head does not have. First, enrolment without retraining: the deployed model trained on 79 birds, but the gallery holds all 81. Smew and Skunk, with one and two photographs, were never trained on — and they are searchable. Second, a principled way to say I don't know. A softmax head must name something, whatever walks past. Here, below 0.938 — that five-per-cent point — the answer is a refusal, and a narrow top-two margin returns a shortlist for the keeper to confirm.");
}

// ===========================================================================
// 10 — LIMITATIONS  (35 s)
// ===========================================================================
{
  const s = L.lightSlide(pres);
  L.kicker(s, "Scope");
  L.title(s, "What this study does not show", { h: 0.72 });

  const lims = [
    ["No end-to-end test", "Identification is measured from the archive as photographed. There is no detector in the deployed path, so every claim is conditional on inputs that resemble the existing archive."],
    ["The threshold is transferred, not recalibrated", "0.938 was measured at 5% false-accept on the cross-validated models. Once all 81 birds are enrolled the realistic unknown is a blurred, rear-facing or non-penguin image — which it has never been calibrated against."],
    ["35 of 81 birds", "The evaluated set is the better-photographed 43% of the colony. Given the session gradient, the rest are likely to be harder, and they were not measured."],
    ["One backbone, reconstructed sessions", "Only ResNet18, so this compares objective and augmentation, not architectures — 0.559 is not a ceiling. And sessions were inferred from filenames and frame gaps, not recorded at capture."],
  ];
  let y = 1.45;
  lims.forEach(([t, d]) => {
    s.addShape("ellipse", { x: M, y: y + 0.06, w: 0.2, h: 0.2,
      fill: { color: C.orange }, line: { color: C.orange, width: 0 } });
    s.addText(t, { x: M + 0.42, y, w: 4.15, h: 0.62,
      fontFace: F.body, fontSize: 14.5, bold: true, color: C.navy,
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 0.95 });
    s.addText(d, { x: M + 4.75, y, w: W - M - 4.75 - M, h: 1.05,
      fontFace: F.body, fontSize: 12.5, color: C.ink,
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.08 });
    y += 1.32;
  });

  L.foot(s, ++n, RUN);
  s.addNotes("Four things this does not show, quickly. There is no end-to-end test — no detector in the deployed path, so every claim is conditional on inputs like the archive. The operating threshold was transferred from the cross-validated models, not recalibrated, and has never been tested against blurred or rear-facing photographs. The evaluated set is the better-photographed 43% of the colony, and the rest are probably harder. And there is one backbone and one reconstructed session rule — so 0.559 is not an upper limit.");
}

// ===========================================================================
// 11 — THE ASK  (45 s)
// ===========================================================================
{
  const s = L.lightSlide(pres);
  L.kicker(s, "What to do about it");
  L.title(s, "The next gain is a camera, not a loss function", { h: 0.72 });

  L.fitImage(s, `${A}/13_colony_sessions_per_individual_notitle.png`,
    { x: M, y: 1.3, w: W - 2 * M, h: 4.0 });

  const asks = [
    { v: "53 of 81", l: "birds below four sessions", sub: "only 28 reach the provisional target", color: C.orange },
    { v: "116", l: "further individual encounters", sub: "to bring the whole colony to four", color: C.navy },
    { v: "≈ 8", l: "separate outings", sub: "at ~15 birds each — on different days", color: C.navy },
  ];
  asks.forEach((a, i) => L.stat(s, {
    x: M + i * 4.1, y: 5.42, w: 3.9,
    value: a.v, label: a.l, sub: a.sub, color: a.color, size: 38, labelSize: 12.5,
  }));

  L.foot(s, ++n, RUN);
  s.addNotes("So the recommendation is a collection protocol, not an architecture. Applying my session rule to the whole colony: 335 sessions across 81 birds, very unevenly spread. Only 28 reach four separate occasions; 53 fall short. Four is provisional — I grouped four, five and six sessions together and did not assign effort experimentally, so it is a starting point, not a validated threshold. But it is costable: 116 further encounters, about eight outings, on different days, deliberately varying viewpoint, light and distance. Eight mornings with a camera is something a zoo can approve.");
}

// ===========================================================================
// 12 — CLOSE  (20 s)
// ===========================================================================
{
  const s = L.darkSlide(pres);
  s.addText("The number I would defend is not 0.559.", {
    x: M, y: 2.05, w: W - 2 * M, h: 0.75,
    fontFace: F.head, fontSize: 32, bold: true, color: C.white,
    isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText([
    { text: "It is ", options: { color: "9FC0E4" } },
    { text: "0.531", options: { color: C.orange, bold: true } },
    { text: " — the amount a conventional random split\nsilently added to a result that already looked finished.", options: { color: "9FC0E4" } },
  ], {
    x: M, y: 2.95, w: W - 2 * M, h: 1.3,
    fontFace: F.head, fontSize: 27, bold: true,
    isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.1,
  });
  L.dots(s, { x: M, y: 4.5, n: 13, color: C.blue, d: 0.15, gap: 0.1 });
  s.addText(
    "If you can tell me which day a photograph was taken, you can tell me whether it belongs in your test set.\n" +
    "github.com/aoaoguo2003/pgs",
    {
      x: M, y: 5.1, w: W - 2 * M, h: 0.9,
      fontFace: F.body, fontSize: 14, color: "C9D6E6",
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.4,
    }
  );
  L.foot(s, ++n, "");
  s.addNotes("To close. On this evidence, 116 more individual encounters — about eight mornings with a camera — is worth more than any change I could make to the model. Better algorithms cannot substitute for observations that are not in the archive. And the number I would defend is not 0.559. It is 0.531: the amount a conventional random split silently added to a result that already looked finished. Thank you.");
}

// ===========================================================================
// 13 — THANK YOU / QUESTIONS  (the slide that stays up during Q&A)
// ===========================================================================
{
  const s = L.darkSlide(pres);
  const PANEL2 = 4.75;
  L.coverImage(s, `${A}/penguin_thanks.png`, { x: W - PANEL2, y: 0, w: PANEL2, h: H });
  s.addText("Thank you", {
    x: M, y: 0.95, w: 7.4, h: 0.85,
    fontFace: F.head, fontSize: 42, bold: true, color: C.white,
    isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText("Any questions?", {
    x: M, y: 1.8, w: 7.4, h: 0.55,
    fontFace: F.head, fontSize: 26, color: C.orange,
    isTextBox: true, margin: 0, valign: "middle",
  });

  // the three numbers the panel is most likely to want in front of them
  const recap = [
    { v: "0.531", l: "inflation from splitting by\nfile instead of by encounter", c: C.orange },
    { v: "0.559", l: "macro rank-1, 35 candidates,\nclosed set", c: C.white },
    { v: "0.123", l: "correctly named at a 1%\nstranger false-accept rate", c: C.white },
  ];
  recap.forEach((r, i) => {
    const x = M + i * 2.5;
    s.addText(r.v, {
      x, y: 2.75, w: 2.3, h: 0.6,
      fontFace: F.head, fontSize: 34, bold: true, color: r.c,
      isTextBox: true, margin: 0, valign: "middle",
    });
    s.addText(r.l, {
      x, y: 3.35, w: 2.3, h: 0.66,
      fontFace: F.body, fontSize: 10.5, color: "9FC0E4",
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.05,
    });
  });

  L.dots(s, { x: M, y: 4.3, n: 13, color: C.blue, d: 0.13, gap: 0.09 });

  s.addText(
    "With thanks to Robin Freeman for his supervision, and to ZSL London Zoo and the volunteer " +
    "photographers whose archive made this possible.",
    {
      x: M, y: 4.75, w: 7.2, h: 0.75,
      fontFace: F.body, fontSize: 12.5, color: "C9D6E6",
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.2,
    }
  );
  s.addText("Code and analysis:  github.com/aoaoguo2003/pgs", {
    x: M, y: 5.62, w: 7.2, h: 0.34,
    fontFace: F.body, fontSize: 12.5, bold: true, color: "9FC0E4",
    isTextBox: true, margin: 0, valign: "middle",
  });
  n++;   // no page number: it would land on the photograph, and this slide is the end
  s.addNotes(
    "Thank you. I am happy to take questions — and I have backup slides on the inclusion criteria, " +
    "the open-set calibration, the training recipe and the full results table."
  );
}

// ===========================================================================
// BACKUP SECTION
// ===========================================================================
{
  const s = L.darkSlide(pres);
  s.addText("Backup", {
    x: M, y: 3.0, w: 6, h: 0.9,
    fontFace: F.head, fontSize: 40, bold: true, color: C.white,
    isTextBox: true, margin: 0, valign: "middle",
  });
  s.addText("Prepared answers", {
    x: M, y: 3.9, w: 6, h: 0.4,
    fontFace: F.body, fontSize: 16, color: "9FC0E4",
    isTextBox: true, margin: 0, valign: "middle",
  });
  L.dots(s, { x: M, y: 4.6, n: 8, color: C.blue, d: 0.15, gap: 0.1 });
}

function backup(titleText, kickerText, build, notes) {
  const s = L.lightSlide(pres);
  L.kicker(s, kickerText);
  L.title(s, titleText, { h: 0.72, size: 25 });
  build(s);
  s.addText("BACKUP", {
    x: W - M - 1.2, y: H - 0.46, w: 1.2, h: 0.28,
    fontFace: F.body, fontSize: 9, bold: true, color: C.faint, align: "right",
    charSpacing: 1.2, isTextBox: true, margin: 0, valign: "middle",
  });
  if (notes) s.addNotes(notes);
  return s;
}

backup("Why 35 of 81? The session rule binds, not the photo rule",
  "Q — inclusion criteria",
  s => {
    L.fitImage(s, `${A}/14_photos_vs_sessions_notitle.png`,
      { x: M, y: 1.35, w: 7.6, h: 4.9 });
    L.bullets(s, [
      "37 of 81 birds fall below 16 photographs; 43 fall below 3 sessions; 34 fail both",
      "The 46 excluded birds are never queries — they are gallery distractors and, in the open-set test, genuine strangers",
      "Nicki and Gonzo sit at almost the same photo count and thirteen sessions apart",
      "Consequence to concede: 0.559 describes the better-photographed 43% of the colony",
    ], { x: 8.35, y: 1.5, w: 4.4, h: 4.6, size: 12.5, space: 12 });
  },
  "Two criteria: at least 16 photographs, which leaves 44 birds, and at least 3 capture sessions, which leaves 35. " +
  "The session rule is the binding one — 43 birds fall below three sessions against 37 below sixteen photographs. " +
  "I concede the consequence: these figures describe the better-photographed 43% of the colony, and the session gradient " +
  "says the remaining birds are likely to be harder.");

backup("Did ArcFace help everyone, or did the macro mean hide it?",
  "Q — is the gain broad?",
  s => {
    L.fitImage(s, `${A}/09_per_individual_change_notitle.png`,
      { x: M, y: 1.35, w: 8.1, h: 4.9 });
    L.bullets(s, [
      "31 of 35 birds improve from softmax+basic to ArcFace+strong",
      "Three decline: Beau 0.632→0.579, Nicki 0.207→0.189, Peapod 0.136→0.045",
      "Greyjoy is 0.000 under both — the only bird never identified by the best configuration",
      "The four that do not gain are all 3-to-5-session birds: the same session story",
    ], { x: 8.85, y: 1.5, w: 3.9, h: 4.6, size: 12.5, space: 12 });
  },
  "Thirty-one of thirty-five birds improve. Three decline slightly and Greyjoy is zero under both. " +
  "The birds that do not gain are the sparsely sampled ones, which is the session finding again rather than a counterexample.");

backup("Why cross-validate rather than hold out one split?",
  "Q — evaluation design",
  s => {
    L.fitImage(s, `${A}/11_evaluation_coverage_notitle.png`,
      { x: 5.1, y: 1.22, w: 7.6, h: 5.2 });
    L.bullets(s, [
      "A single session-disjoint split tests only 261 of 1,743 photographs",
      "Three birds are judged on a single test photograph",
      "Session-wise 5-fold tests all 1,743 exactly once, still session-disjoint",
      "Every bird's whole record contributes out-of-fold evidence",
    ], { x: M, y: 1.75, w: 4.1, h: 4.4, size: 13.5, space: 16 });

  },
  "Under one split only 261 of the 1,743 photographs are ever tested, and three birds are judged on a single photograph. " +
  "Five-fold session-wise cross-validation tests every photograph exactly once while still keeping complete sessions disjoint.");

backup("Why not crop to the breast spots?",
  "Q — the obvious ecology question",
  s => {
    L.fitImage(s, `${A}/03_belly_detector_map.png`,
      { x: 7.05, y: 1.5, w: 5.68, h: 4.7 });
    L.bullets(s, [
      "I did. A YOLOv8s ventral-region detector reaches mAP@50 ≈ 0.98",
      "The classifier on the cropped bellies still lost: 0.866 against 0.950 on full-body images (both under the leaky random split)",
      "Cropping removes identity information the model was using — face, chest band, proportions, posture",
      "So localisation was not the bottleneck, and every reported identification number uses uncropped photographs",
    ], { x: M, y: 1.6, w: 6.1, h: 4.6, size: 14, space: 19 });
  },
  "I did try it — the literature points straight at the ventral spots. The detector was not the problem: mAP at 50 is about 0.98. " +
  "But the classifier on cropped bellies scored 0.866 against 0.950 on whole images, both under the random split. " +
  "Cropping throws away identity cues the model was actually using. So the reported pipeline uses uncropped photographs.");

backup("The threshold has a provenance, and it was wrong once",
  "Q — open-set calibration",
  s => {
    L.fitImage(s, `${A}/s10_openset.png`,
      { x: M, y: 1.35, w: 7.5, h: 4.85 });
    L.card(s, { x: 8.3, y: 1.4, w: 4.45, h: 2.35, fill: C.panel });
    s.addText("The error I caught", {
      x: 8.55, y: 1.56, w: 3.95, h: 0.3,
      fontFace: F.body, fontSize: 13, bold: true, color: C.orange,
      isTextBox: true, margin: 0, valign: "middle" });
    s.addText(
      "The first shipped threshold was 0.800, tuned on the leaky split with simulated impostors, and documented as rejecting 96.6% " +
      "of unknown birds. Measured against real never-trained birds it accepts 29.7% of them. That is what replaced it with 0.938.",
      { x: 8.55, y: 1.92, w: 3.95, h: 1.7,
        fontFace: F.body, fontSize: 11.5, color: C.ink,
        isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.08 });
    L.bullets(s, [
      "0.974 → 1% FAR → DIR 0.123",
      "0.938 → 5% FAR → DIR 0.237  (shipped)",
      "0.908 → 10% FAR → DIR 0.312",
      "Transferred from the CV models, not recalibrated after full-data training",
    ], { x: 8.55, y: 3.95, w: 4.0, h: 2.1, size: 12, space: 10 });
  },
  "The operating threshold carries its own calibration table in the deployed code. And it was wrong once: the first version, 0.800, " +
  "was tuned on the leaky split using simulated impostors and documented as rejecting 96.6% of unknowns. Against real never-trained " +
  "birds it accepts 29.7% of them. Finding that is what produced 0.938.");

backup("Training is fixed-length by design — and memorises perfectly",
  "Q — overfitting and the 1.000 diagnostic",
  s => {
    L.card(s, { x: M, y: 1.4, w: 6.05, h: 4.75, fill: C.panel });
    s.addText("The recipe, identical in all 20 runs", {
      x: M + 0.3, y: 1.6, w: 5.45, h: 0.3,
      fontFace: F.body, fontSize: 13, bold: true, color: C.navy,
      isTextBox: true, margin: 0, valign: "middle" });
    L.bullets(s, [
      "ResNet18, ImageNet init; 512-d penultimate embedding, L2-normalised; head discarded at inference",
      "ArcFace scale 30, margin 0.3, warmed up over the first five epochs — the paper's defaults, never tuned, not exposed as flags",
      "AdamW, lr 3e-4, wd 1e-4, batch 32, AMP, seed 42",
      "80 fixed epochs; 3-epoch warm-up then cosine decay to exactly zero; final epoch kept unconditionally",
      "No validation split, no early stopping, no checkpoint selection — so no configuration can win by being selected more luckily",
    ], { x: M + 0.3, y: 2.0, w: 5.45, h: 4.0, size: 12, space: 10 });

    L.stat(s, { x: 7.15, y: 1.75, w: 2.75, value: "1.000", label: "training photographs",
      sub: "own session excluded — fold 0, 1,394 photos.\nA diagnostic, not a test.", color: C.faint, size: 40 });
    L.stat(s, { x: 10.15, y: 1.75, w: 2.6, value: "0.390", label: "held-out sessions",
      sub: "softmax + basic, session-disjoint.\nThe same fixed recipe.", color: C.orange, size: 40 });
    s.addText(
      "Those 1,394 photographs had already contributed to optimising the parameters, so high performance was expected and this is " +
      "not independent evidence of generalisation. Its only job is to locate the failure: the model separates everything it was " +
      "fitted on, and fails on sessions it was not. The bottleneck is new capture occasions, not the representation. " +
      "It was run for fold 0 only, and no script was retained to reproduce it across folds.",
      { x: 7.15, y: 3.75, w: 5.6, h: 2.4,
        fontFace: F.body, fontSize: 12, color: C.ink,
        isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.1 });
  },
  "Training is 80 fixed epochs with no early stopping and no checkpoint selection, so no configuration can win by being selected more " +
  "luckily. Yes, it memorises: query the training photographs against prototypes rebuilt without their own session and it is perfect. " +
  "That is a diagnostic, not a test — those photographs shaped the parameters. What it tells me is where the failure is: the model " +
  "separates what it was fitted on and fails on sessions it was not.");

backup("Every reported number, in one table",
  "Q — the full results",
  s => {
    const rows = [
      ["configuration", "rank-1 (35)", "rank-5 (35)", "mAP", "rank-1 (81)", "DIR@FAR 1%"],
      ["softmax + basic", "0.390", "0.746", "0.420", "0.224", "0.076"],
      ["softmax + strong", "0.530", "0.809", "0.533", "0.361", "0.086"],
      ["ArcFace + basic", "0.486", "0.734", "0.509", "0.364", "0.097"],
      ["ArcFace + strong", "0.559", "0.782", "0.581", "0.477", "0.123"],
    ];
    s.addTable(rows.map((r, i) =>
      r.map((cell, j) => ({
        text: cell,
        options: {
          fontFace: i === 0 ? F.body : (j === 0 ? F.body : F.head),
          fontSize: i === 0 ? 12 : 15,
          bold: i === 0 || i === 4,
          color: i === 0 ? C.muted : (i === 4 ? C.navy : C.ink),
          align: j === 0 ? "left" : "center",
          fill: { color: i === 4 ? "E8F0FB" : C.bg },
          valign: "middle",
        },
      }))
    ), {
      x: M, y: 1.45, w: W - 2 * M, colW: [3.2, 1.78, 1.78, 1.78, 1.78, 1.78],
      rowH: [0.42, 0.5, 0.5, 0.5, 0.5],
      border: { type: "solid", pt: 1, color: C.rule },
    });
    s.addText("Session-wise 5-fold cross-validation · 35 individuals · 1,743 photographs · every value macro over individuals", {
      x: M, y: 3.95, w: W - 2 * M, h: 0.3,
      fontFace: F.body, fontSize: 11.5, color: C.muted,
      isTextBox: true, margin: 0, valign: "middle" });

    L.bullets(s, [
      "Session gradient (ArcFace + strong): 3 sessions 0.186 (n=8) · 4–6 sessions 0.618 (n=13) · 7+ sessions 0.717 (n=14) · ≥4 combined 0.669 (n=27)",
      "CMC, 35 candidates: rank-2 0.650 · rank-3 0.702 · rank-5 0.782 · rank-10 0.860. Rank-k beyond 1 was never computed at 81 candidates",
      "Softmax + strong is the best rank-5 configuration at 0.809 — ArcFace was selected on rank-1, mAP and colony-scale degradation, not rank-5",
      "Single session-disjoint split, different recipe: rank-1 0.389, rank-5 0.726, 1-NN 0.384; random split 0.920 / 0.984 / 0.902",
    ], { x: M, y: 4.4, w: W - 2 * M, h: 2.0, size: 12, space: 10 });
  },
  "Everything in one place, if you want to check a number.");

// ===========================================================================
pres.writeFile({ fileName: process.argv[2] || path.join(__dirname, "final_presentation.pptx") })
  .then(f => console.log("wrote", f, "— slides:", n, "+ backup"));
