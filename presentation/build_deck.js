/* Redesigned defence deck — visual-first, one question at a time. */
const pptxgen = require("pptxgenjs");
const path = require("path");

const A = (f) => path.join(__dirname, "assets", f);

// ---------------------------------------------------------------- palette
const NAVY_DEEP = "0E1B33";
const NAVY = "22314D";
const SLATE = "5F718C";
const PALE = "F2F5F9";
const BORDER = "D5DEEA";
const TEAL = "1E7A70";
const TEAL_LT = "2A9D8F";
const AMBER = "F2A541";
const CORAL = "E76F51";
const WHITE = "FFFFFF";
const ICE = "B3C4DC";

const SERIF = "Cambria";
const SANS = "Calibri";

const W = 13.333;
const H = 7.5;
const M = 0.7; // page margin

const pres = new pptxgen();
pres.defineLayout({ name: "W16X9", width: W, height: H });
pres.layout = "W16X9";
pres.author = "Candidate WPNS1";
pres.title = "Time-Expanded Perch Embeddings for Feeding-Buzz Detection";

let pageNo = 0;

// ---------------------------------------------------------------- helpers
function lightSlide(eyebrow, title, footerLabel) {
  const s = pres.addSlide();
  pageNo += 1;
  s.background = { color: WHITE };
  if (eyebrow) {
    s.addText(eyebrow, {
      isTextBox: true, x: M, y: 0.42, w: 11.0, h: 0.28,
      fontFace: SANS, fontSize: 11, bold: true, color: TEAL,
      charSpacing: 2.4, margin: 0, valign: "middle",
    });
  }
  if (title) {
    s.addText(title, {
      isTextBox: true, x: M, y: 0.72, w: 11.9, h: 0.72,
      fontFace: SERIF, fontSize: 33, bold: true, color: NAVY,
      margin: 0, valign: "middle",
    });
  }
  if (footerLabel) {
    s.addText(footerLabel, {
      isTextBox: true, x: M, y: 6.92, w: 8.0, h: 0.3,
      fontFace: SANS, fontSize: 9, color: SLATE, margin: 0, valign: "middle",
    });
  }
  s.addText(String(pageNo), {
    isTextBox: true, x: W - M - 1.0, y: 6.92, w: 1.0, h: 0.3,
    fontFace: SANS, fontSize: 9, color: SLATE, align: "right", margin: 0, valign: "middle",
  });
  return s;
}

function darkSlide() {
  const s = pres.addSlide();
  pageNo += 1;
  s.background = { color: NAVY_DEEP };
  return s;
}

function takeaway(s, text, y) {
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: y, w: W - 2 * M, h: 0.62, rectRadius: 0.06,
    fill: { color: NAVY_DEEP }, line: { color: NAVY_DEEP, width: 0 },
  });
  s.addText(text, {
    isTextBox: true, x: M + 0.3, y: y, w: W - 2 * M - 0.6, h: 0.62,
    fontFace: SANS, fontSize: 14.5, bold: true, color: WHITE,
    margin: 0, valign: "middle",
  });
}

function caption(s, text, x, y, w, opts = {}) {
  s.addText(text, {
    isTextBox: true, x: x, y: y, w: w, h: opts.h || 0.5,
    fontFace: SANS, fontSize: opts.size || 11, color: opts.color || SLATE,
    italic: opts.italic !== false, margin: 0, valign: "top",
    align: opts.align || "left",
  });
}

// ================================================================ 1 · TITLE
{
  const s = darkSlide();
  s.addImage({ path: A("buzz_strip.jpg"), x: 0, y: 4.62, w: W, h: 1.05 });
  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 5.67, w: W, h: H - 5.67,
    fill: { color: NAVY_DEEP }, line: { color: NAVY_DEEP, width: 0 },
  });
  s.addImage({ path: A("bat_white.png"), x: 0.75, y: 4.82, w: 1.5, h: 0.34, transparency: 15 });

  s.addText("MSc Ecology and Data Science   ·   Dissertation defence", {
    isTextBox: true, x: M, y: 1.05, w: 11.0, h: 0.32,
    fontFace: SANS, fontSize: 12.5, bold: true, color: AMBER, charSpacing: 2, margin: 0,
  });
  s.addText("Where do bats feed?", {
    isTextBox: true, x: M, y: 1.6, w: 11.6, h: 1.1,
    fontFace: SERIF, fontSize: 52, bold: true, color: WHITE, margin: 0, valign: "middle",
  });
  s.addText("Teaching a bird-trained model to find feeding buzzes\nin places it has never heard", {
    isTextBox: true, x: M, y: 2.85, w: 10.5, h: 1.0,
    fontFace: SANS, fontSize: 19, color: ICE, lineSpacing: 28, margin: 0, valign: "top",
  });

  s.addText("Time-Expanded Perch Embeddings for Feeding-Buzz Detection, Retrieval and Field Candidate Discovery", {
    isTextBox: true, x: M, y: 5.88, w: 9.2, h: 0.3,
    fontFace: SANS, fontSize: 11, italic: true, color: "7C8CA8", margin: 0,
  });
  s.addText("Candidate WPNS1", {
    isTextBox: true, x: M, y: 6.2, w: 8.0, h: 0.3,
    fontFace: SANS, fontSize: 13, bold: true, color: WHITE, margin: 0,
  });
  s.addText("Supervisors: Santiago Martinez Balvanera · Kate Jones   ·   BIOS0057 · University College London · 2025–2026", {
    isTextBox: true, x: M, y: 6.53, w: 11.0, h: 0.35,
    fontFace: SANS, fontSize: 12, color: ICE, margin: 0,
  });
  s.addNotes(
    "Good morning. Before I say a word about methods, I want to start with the animal.\n\n" +
    "Insectivorous bats are night-shift predators in almost every terrestrial ecosystem on Earth. They eat enormous " +
    "quantities of insects, including agricultural pests, and that has real consequences for crops and for disease vectors. " +
    "But we know remarkably little about WHERE they actually do that eating — which patches of habitat are the dinner tables " +
    "and which are just corridors they pass through.\n\n" +
    "This project is about closing a small part of that gap with sound. Over the next fifteen minutes I will ask three questions " +
    "in turn, and answer each one before moving on to the next."
  );
}

// ================================================================ 2 · HOOK
{
  const s = darkSlide();
  s.addImage({ path: A("bat_white.png"), x: 7.55, y: 3.45, w: 5.1, h: 1.15, transparency: 45 });
  s.addImage({ path: A("buzz_strip.jpg"), x: 0, y: 6.45, w: W, h: 1.05, transparency: 25 });

  s.addText("THE BIG PICTURE", {
    isTextBox: true, x: M, y: 1.05, w: 8.0, h: 0.3,
    fontFace: SANS, fontSize: 11.5, bold: true, color: AMBER, charSpacing: 2.6, margin: 0,
  });
  s.addText("Bats eat.\nWe barely know where.", {
    isTextBox: true, x: M, y: 1.55, w: 8.9, h: 2.1,
    fontFace: SERIF, fontSize: 46, bold: true, color: WHITE, lineSpacing: 56, margin: 0, valign: "top",
  });
  s.addText("Insectivorous bats hold down insect populations across almost every terrestrial ecosystem — yet their foraging sites are largely unmapped.", {
    isTextBox: true, x: M, y: 3.95, w: 6.4, h: 1.1,
    fontFace: SANS, fontSize: 16, color: ICE, lineSpacing: 25, margin: 0, valign: "top",
  });
  s.addNotes(
    "Here is the puzzle in one line. Bats eat, in quantities that matter ecologically and economically — and we barely know where.\n\n" +
    "The reason is practical. You cannot follow a bat around at night. Radio-tracking is expensive, invasive and gives you a handful of " +
    "individuals. What you CAN do is leave a microphone in the landscape and let the bats tell you themselves.\n\n" +
    "That is passive acoustic monitoring, and it is now routine in biodiversity work. A recorder sits in the field for weeks with " +
    "almost no disturbance to the animals. The difficulty is not collecting the sound. The difficulty is what comes next."
  );
}

// ================================================================ 3 · PRESENCE VS FEEDING
{
  const s = lightSlide("WHAT WE LISTEN FOR", "Presence is easy. Feeding is the question.", "Why feeding buzzes");

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 1.72, w: W - 2 * M, h: 3.24, rectRadius: 0.06,
    fill: { color: NAVY_DEEP }, line: { color: NAVY_DEEP, width: 0 },
  });
  s.addImage({ path: A("buzz_spec.jpg"), x: M + 0.35, y: 1.85, w: 11.23, h: 11.23 / 4.3796 });

  s.addText("search-phase calls", {
    isTextBox: true, x: M + 0.9, y: 4.5, w: 2.6, h: 0.3,
    fontFace: SANS, fontSize: 11.5, bold: true, color: ICE, margin: 0,
  });
  s.addText("terminal buzz  →  a capture attempt", {
    isTextBox: true, x: 8.05, y: 4.5, w: 3.9, h: 0.3,
    fontFace: SANS, fontSize: 11.5, bold: true, color: AMBER, margin: 0, align: "right",
  });

  const cards = [
    ["A call", "the bat was here", SLATE],
    ["A buzz", "the bat tried to eat here", TEAL],
  ];
  cards.forEach(([h1, h2, col], i) => {
    const x = M + i * 3.6;
    s.addText(h1, {
      isTextBox: true, x: x, y: 5.15, w: 3.3, h: 0.42,
      fontFace: SERIF, fontSize: 23, bold: true, color: col, margin: 0,
    });
    s.addText(h2, {
      isTextBox: true, x: x, y: 5.6, w: 3.3, h: 0.4,
      fontFace: SANS, fontSize: 13.5, color: NAVY, margin: 0,
    });
  });
  s.addText("Brief · ultrasonic · recorded at 384 kHz\nOver 200 calls a second in the terminal phase.", {
    isTextBox: true, x: 8.4, y: 5.15, w: 4.2, h: 0.9,
    fontFace: SANS, fontSize: 13, color: SLATE, lineSpacing: 19, margin: 0, align: "right",
  });

  s.addNotes(
    "This is the signal the whole project turns on.\n\n" +
    "On the left of the spectrogram you can see the regular, widely spaced search-phase calls of a hunting bat. On the right " +
    "those calls compress — the interval collapses, the repetition rate climbs past two hundred calls a second in some species — " +
    "and then it stops. That compression is a feeding buzz, and it is the acoustic signature of a bat closing on prey.\n\n" +
    "This is the important distinction. An ordinary call tells you a bat passed through. A buzz tells you a bat tried to eat. " +
    "Buzzes are behaviour, not just presence — which is exactly what you need if you want to map foraging.\n\n" +
    "They are also hard to find: brief, ultrasonic, recorded here at 384 kilohertz, and easily confused with other pulse trains."
  );
}

// ================================================================ 4 · THE HAYSTACK
{
  const s = lightSlide("THE SCALE PROBLEM", "Hours of audio, seconds of signal", "The workload");

  // texture: one recording, subdivided into windows
  const barX = M, barY = 1.95, barW = W - 2 * M, barH = 0.5;
  s.addShape(pres.ShapeType.rect, {
    x: barX, y: barY, w: barW, h: barH,
    fill: { color: PALE }, line: { color: BORDER, width: 1 },
  });
  const nTicks = 78;
  for (let i = 1; i < nTicks; i++) {
    const tx = barX + (barW * i) / nTicks;
    s.addShape(pres.ShapeType.rect, {
      x: tx, y: barY, w: 0.012, h: barH,
      fill: { color: BORDER }, line: { color: BORDER, width: 0 },
    });
  }
  s.addShape(pres.ShapeType.rect, {
    x: barX + (barW * 46) / nTicks, y: barY - 0.09, w: barW / nTicks, h: barH + 0.18,
    fill: { color: AMBER }, line: { color: AMBER, width: 0 },
  });
  s.addText("one 0.25 s window", {
    isTextBox: true, x: barX + (barW * 46) / nTicks - 1.2, y: barY + barH + 0.14, w: 2.6, h: 0.28,
    fontFace: SANS, fontSize: 10.5, bold: true, color: AMBER, align: "center", margin: 0,
  });
  s.addText("one 60-second recording", {
    isTextBox: true, x: barX, y: barY + barH + 0.14, w: 3.2, h: 0.28,
    fontFace: SANS, fontSize: 10.5, color: SLATE, margin: 0,
  });

  // funnel of three numbers
  const steps = [
    ["9.4 h", "from one recorder", NAVY],
    ["270,156", "windows to be scored", AMBER],
    ["69", "a human could review", TEAL],
  ];
  steps.forEach(([big, lab, col], i) => {
    const x = M + i * 4.35;
    s.addText(big, {
      isTextBox: true, x: x, y: 3.25, w: 3.6, h: 1.05,
      fontFace: SERIF, fontSize: 54, bold: true, color: col, margin: 0, valign: "middle",
    });
    s.addText(lab, {
      isTextBox: true, x: x, y: 4.35, w: 3.6, h: 0.34,
      fontFace: SANS, fontSize: 13.5, color: SLATE, margin: 0,
    });
    if (i < 2) {
      s.addText("→", {
        isTextBox: true, x: x + 3.62, y: 3.25, w: 0.7, h: 1.05,
        fontFace: SANS, fontSize: 26, color: BORDER, align: "center", margin: 0, valign: "middle",
      });
    }
  });

  takeaway(s, "Something has to rank those windows before anyone listens to them.", 5.45);
  caption(s, "564 one-minute recordings · 0.25 s windows with a 0.125 s hop · one AudioMoth, Mara Triangle, Kenya", M, 6.28, 11.9, { size: 10.5 });

  s.addNotes(
    "Here is the workload, in the dataset I actually worked with.\n\n" +
    "Nine point four hours of field audio from a single recorder in the Mara Triangle in Kenya. I score it in overlapping " +
    "quarter-second windows — the bar at the top is one minute of audio, and the amber sliver is one window. That one minute " +
    "alone is 479 windows. Across 564 recordings it comes to two hundred and seventy thousand windows.\n\n" +
    "A person can carefully review a few dozen of those. Sixty-nine, in my case. So the question is never 'can a human find " +
    "the buzzes' — it is 'what puts the right sixty-nine in front of the human'.\n\n" +
    "That is a ranking problem, and ranking depends entirely on how you turn sound into numbers."
  );
}

// ================================================================ 5 · THE GAP
{
  const s = lightSlide("THE GAP", "Detectors are graded where they were born", "The generalisation gap");

  // slope graphic
  const gx = M + 0.15, gTop = 2.1, gBot = 4.7;
  const f1ToY = (v) => gBot - ((v - 0.65) / 0.40) * (gBot - gTop);
  const xA = gx + 1.35, xB = gx + 6.15;
  const yA = f1ToY(0.930), yB = f1ToY(0.727);

  // baseline grid
  [1.0, 0.9, 0.8, 0.7].forEach((v) => {
    s.addShape(pres.ShapeType.rect, {
      x: gx, y: f1ToY(v), w: 7.6, h: 0.008,
      fill: { color: "EDF1F7" }, line: { color: "EDF1F7", width: 0 },
    });
    s.addText(v.toFixed(1), {
      isTextBox: true, x: gx - 0.62, y: f1ToY(v) - 0.14, w: 0.52, h: 0.28,
      fontFace: SANS, fontSize: 10, color: BORDER, align: "right", margin: 0, valign: "middle",
    });
  });

  s.addShape(pres.ShapeType.line, {
    x: xA, y: yA, w: xB - xA, h: yB - yA,
    line: { color: CORAL, width: 4 },
  });
  [[xA, yA, NAVY, "0.930"], [xB, yB, CORAL, "0.727"]].forEach(([px, py, col, lab], i) => {
    s.addShape(pres.ShapeType.ellipse, {
      x: px - 0.11, y: py - 0.11, w: 0.22, h: 0.22,
      fill: { color: col }, line: { color: WHITE, width: 2 },
    });
    s.addText(lab, {
      isTextBox: true, x: px - 0.85, y: py - 0.72, w: 1.7, h: 0.46,
      fontFace: SERIF, fontSize: 28, bold: true, color: col, align: "center", margin: 0, valign: "middle",
    });
  });
  s.addText("−0.203 F1", {
    isTextBox: true, x: (xA + xB) / 2 - 0.95, y: (yA + yB) / 2 + 0.12, w: 1.9, h: 0.34,
    fontFace: SANS, fontSize: 15, bold: true, color: CORAL, align: "center", margin: 0, valign: "middle",
  });

  s.addText("tested the usual way\nclips shuffled and split at random", {
    isTextBox: true, x: xA - 1.6, y: 4.88, w: 3.2, h: 0.7,
    fontFace: SANS, fontSize: 12.5, color: NAVY, align: "center", lineSpacing: 17, margin: 0, valign: "top",
  });
  s.addText("tested on a site it has never heard\nits weakest held-out site", {
    isTextBox: true, x: xB - 1.8, y: 4.88, w: 3.6, h: 0.7,
    fontFace: SANS, fontSize: 12.5, bold: true, color: CORAL, align: "center", lineSpacing: 17, margin: 0, valign: "top",
  });

  // how the honest test works: hold every site out in turn
  const sqY = 5.95, sqW = 0.34, sqGap = 0.14, sqX = M + 0.15;
  for (let i = 0; i < 6; i++) {
    const held = i === 3;
    s.addShape(pres.ShapeType.roundRect, {
      x: sqX + i * (sqW + sqGap), y: sqY, w: sqW, h: sqW, rectRadius: 0.1,
      fill: { color: held ? CORAL : "DDE5EF" }, line: { color: held ? CORAL : BORDER, width: 1 },
    });
  }
  s.addText([
    { text: "Six recording sites. ", options: { bold: true, color: NAVY } },
    { text: "Each one held out in turn, and scored only on the site left out.", options: { color: SLATE } },
  ], {
    isTextBox: true, x: sqX + 6 * (sqW + sqGap) + 0.12, y: sqY - 0.06, w: 4.4, h: 0.5,
    fontFace: SANS, fontSize: 12, margin: 0, valign: "middle",
  });

  // right column
  s.addShape(pres.ShapeType.roundRect, {
    x: 8.85, y: 1.95, w: 3.78, h: 3.78, rectRadius: 0.06,
    fill: { color: PALE }, line: { color: BORDER, width: 1 },
  });
  s.addText("Same detector.\nSame clips.\nOnly the split changed.", {
    isTextBox: true, x: 9.15, y: 2.2, w: 3.2, h: 1.4,
    fontFace: SERIF, fontSize: 19, bold: true, color: NAVY, lineSpacing: 26, margin: 0, valign: "top",
  });
  s.addText([
    { text: "Built and validated close to home:", options: { breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 5 } },
    { text: "Buzzfindr", options: { bold: true, color: NAVY, breakLine: false } },
    { text: "  ·  Ontario, Canada", options: { breakLine: true } },
    { text: "BatBuddy", options: { bold: true, color: NAVY, breakLine: false } },
    { text: "  ·  the Netherlands", options: { breakLine: true } },
    { text: "This field test", options: { bold: true, color: TEAL, breakLine: false } },
    { text: "  ·  Mara Triangle, Kenya", options: { color: TEAL, breakLine: true } },
  ], {
    isTextBox: true, x: 9.15, y: 3.78, w: 3.25, h: 1.8,
    fontFace: SANS, fontSize: 11.5, color: SLATE, lineSpacing: 20, margin: 0, valign: "top",
  });

  caption(s, "Spectral-statistics baseline, this study · F1 on the Ontario clips · random split vs the weakest of six held-out rounds.", M, 6.55, 11.9, { size: 10.5 });

  s.addNotes(
    "This is the gap I want you to see rather than take on trust.\n\n" +
    "On the left is the number you normally get quoted. Take a labelled set of clips, shuffle them, split at random, train and " +
    "test. My hand-crafted spectral baseline scores 0.930 F1 that way, and that sounds like a solved problem.\n\n" +
    "On the right is the same detector on the same clips, with one change: I held out an entire recording site, so the detector " +
    "has never heard that place before. I repeat that six times, holding each site out in turn — the squares along the bottom — " +
    "and its weakest site falls to 0.727. Twenty F1 points vanish, and nothing about the model changed, only the honesty of the test.\n\n" +
    "That matters here because of where these tools come from. Buzzfindr was developed on Ontario recordings, BatBuddy on Dutch " +
    "ones, and the recordings I care about are from the Mara Triangle in Kenya — different species assemblage, different insects, " +
    "different background. If twenty points can disappear between two Ontario sites, we should not assume anything survives that jump.\n\n" +
    "So the first question writes itself."
  );
}

// ================================================================ 6 · QUESTION 1
{
  const s = darkSlide();
  s.addImage({ path: A("buzz_strip.jpg"), x: 0, y: 6.45, w: W, h: 1.05, transparency: 45 });
  s.addText("01", {
    isTextBox: true, x: M, y: 1.85, w: 2.2, h: 1.5,
    fontFace: SERIF, fontSize: 90, bold: true, color: AMBER, margin: 0, valign: "middle",
  });
  s.addText("Which way of describing\nthe sound survives a site\nit has never heard?", {
    isTextBox: true, x: M, y: 3.25, w: 10.5, h: 2.4,
    fontFace: SERIF, fontSize: 40, bold: true, color: WHITE, lineSpacing: 50, margin: 0, valign: "top",
  });
  s.addNotes(
    "Question one. Which way of describing the sound survives a site it has never heard?\n\n" +
    "To answer that I need to say what 'a way of describing the sound' actually means, because it is the thing the whole talk turns on."
  );
}

// ============================================== 7 · WHAT A DETECTOR ACTUALLY SEES
{
  const s = lightSlide("METHOD · QUESTION 1", "A detector never hears the sound", "What a representation is");

  const boxY = 2.35, boxH = 1.95;
  // step 1 — the recording
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: boxY, w: 3.3, h: boxH, rectRadius: 0.06,
    fill: { color: NAVY_DEEP }, line: { color: NAVY_DEEP, width: 0 },
  });
  s.addImage({ path: A("buzz_spec.jpg"), x: M + 0.22, y: boxY + 0.5, w: 2.86, h: 2.86 / 4.3796 });
  s.addText("THE RECORDING", {
    isTextBox: true, x: M + 0.22, y: boxY + 0.16, w: 2.9, h: 0.28,
    fontFace: SANS, fontSize: 10.5, bold: true, color: ICE, charSpacing: 1.4, margin: 0,
  });
  s.addText("what a bat actually did", {
    isTextBox: true, x: M, y: boxY + boxH + 0.14, w: 3.3, h: 0.3,
    fontFace: SANS, fontSize: 12, color: SLATE, align: "center", margin: 0,
  });

  // step 2 — the representation (highlighted)
  const rx = M + 4.05;
  s.addShape(pres.ShapeType.roundRect, {
    x: rx, y: boxY, w: 3.3, h: boxH, rectRadius: 0.06,
    fill: { color: "FDF3E3" }, line: { color: AMBER, width: 2 },
  });
  s.addText("THE REPRESENTATION", {
    isTextBox: true, x: rx + 0.22, y: boxY + 0.16, w: 2.9, h: 0.28,
    fontFace: SANS, fontSize: 10.5, bold: true, color: "B9761E", charSpacing: 1.4, margin: 0,
  });
  for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 7; c++) {
      s.addShape(pres.ShapeType.rect, {
        x: rx + 0.35 + c * 0.37, y: boxY + 0.62 + r * 0.3, w: 0.27, h: 0.2,
        fill: { color: (r + c) % 3 === 0 ? AMBER : (r + c) % 3 === 1 ? "EBC489" : "F7DFBB" },
        line: { width: 0, color: WHITE },
      });
    }
  }
  s.addText("a list of numbers", {
    isTextBox: true, x: rx, y: boxY + boxH + 0.14, w: 3.3, h: 0.3,
    fontFace: SANS, fontSize: 12, bold: true, color: "B9761E", align: "center", margin: 0,
  });

  // step 3 — the detector
  const dx = M + 8.1;
  s.addShape(pres.ShapeType.roundRect, {
    x: dx, y: boxY, w: 3.3, h: boxH, rectRadius: 0.06,
    fill: { color: PALE }, line: { color: BORDER, width: 1 },
  });
  s.addText("THE DETECTOR", {
    isTextBox: true, x: dx + 0.22, y: boxY + 0.16, w: 2.9, h: 0.28,
    fontFace: SANS, fontSize: 10.5, bold: true, color: TEAL, charSpacing: 1.4, margin: 0,
  });
  [["buzz", TEAL], ["not a buzz", SLATE]].forEach(([lab, col], i) => {
    s.addShape(pres.ShapeType.roundRect, {
      x: dx + 0.45, y: boxY + 0.68 + i * 0.62, w: 2.4, h: 0.48, rectRadius: 0.08,
      fill: { color: WHITE }, line: { color: col, width: i === 0 ? 2 : 1 },
    });
    s.addText(lab, {
      isTextBox: true, x: dx + 0.45, y: boxY + 0.68 + i * 0.62, w: 2.4, h: 0.48,
      fontFace: SANS, fontSize: 13.5, bold: i === 0, color: col, align: "center", margin: 0, valign: "middle",
    });
  });
  s.addText("one decision per window", {
    isTextBox: true, x: dx, y: boxY + boxH + 0.14, w: 3.3, h: 0.3,
    fontFace: SANS, fontSize: 12, color: SLATE, align: "center", margin: 0,
  });

  [M + 3.42, M + 7.47].forEach((ax) => {
    s.addText("→", {
      isTextBox: true, x: ax, y: boxY, w: 0.55, h: boxH,
      fontFace: SANS, fontSize: 24, color: BORDER, align: "center", margin: 0, valign: "middle",
    });
  });

  takeaway(s, "Whatever the representation leaves out, the detector can never learn.", 5.55);
  caption(s, "The classifier is the same in every experiment. Only the middle box changes.", M, 6.35, 11.9, { size: 10.5 });

  s.addNotes(
    "One idea, and everything else in the talk depends on it.\n\n" +
    "A detector never hears anything. What actually reaches it is the middle box: a fixed-length list of numbers describing a " +
    "quarter of a second of sound. That list is what we call an acoustic representation.\n\n" +
    "Whatever the representation leaves out is gone. If your numbers throw away the fine timing of a pulse train, no classifier " +
    "downstream can recover it, however clever the classifier is.\n\n" +
    "So in every experiment I keep the right-hand box fixed — the same simple logistic regression, the same settings, the same " +
    "threshold — and change only the middle box. Any difference you see is a difference between representations."
  );
}

// ================================================================ 8 · THREE REPRESENTATIONS
{
  const s = lightSlide("METHOD · QUESTION 1", "Three ways to describe the same sound", "Acoustic representations");

  const reps = [
    { name: "Baseline", dim: "1,543", line1: "Mean, SD and max in every narrow band", dark: false, kind: "fine" },
    { name: "Compact", dim: "199", line1: "The same summary, over wider bands", dark: false, kind: "coarse" },
    { name: "Perch v2", dim: "1,536", line1: "A pretrained network's own description", dark: true, kind: "learned" },
  ];
  reps.forEach((r, i) => {
    const x = M + i * 4.05;
    const dark = r.dark;
    s.addShape(pres.ShapeType.roundRect, {
      x: x, y: 1.9, w: 3.75, h: 3.72, rectRadius: 0.06,
      fill: { color: dark ? NAVY_DEEP : PALE },
      line: { color: dark ? NAVY_DEEP : BORDER, width: 1 },
    });
    s.addText(r.name, {
      isTextBox: true, x: x + 0.32, y: 2.12, w: 3.1, h: 0.34,
      fontFace: SANS, fontSize: 12.5, bold: true, charSpacing: 1.6,
      color: dark ? AMBER : TEAL, margin: 0,
    });

    // --- the little diagram that says what this representation is
    const dY = 2.5, dH = 1.0, dX = x + 0.32, dW = 3.11;
    if (r.kind === "fine" || r.kind === "coarse") {
      const nBands = r.kind === "fine" ? 17 : 5;
      s.addShape(pres.ShapeType.rect, {
        x: dX, y: dY, w: dW, h: dH,
        fill: { color: "E4EBF3" }, line: { color: BORDER, width: 1 },
      });
      for (let b = 0; b < nBands; b++) {
        const bh = dH / nBands;
        s.addShape(pres.ShapeType.rect, {
          x: dX + 0.06, y: dY + b * bh + bh * 0.2, w: (dW - 0.12) * (0.25 + 0.72 * Math.abs(Math.sin(b * 1.9 + 0.6))), h: bh * 0.6,
          fill: { color: b % 2 ? TEAL_LT : TEAL }, line: { width: 0, color: WHITE },
        });
      }
      s.addText(r.kind === "fine" ? "513 narrow frequency bands" : "64 wide frequency bands", {
        isTextBox: true, x: dX, y: dY + dH + 0.06, w: dW, h: 0.28,
        fontFace: SANS, fontSize: 10.5, italic: true, color: SLATE, margin: 0,
      });
    } else {
      s.addShape(pres.ShapeType.roundRect, {
        x: dX, y: dY + 0.16, w: 1.42, h: dH - 0.32, rectRadius: 0.08,
        fill: { color: "16294A" }, line: { color: AMBER, width: 1.5 },
      });
      s.addText("pretrained\nnetwork", {
        isTextBox: true, x: dX, y: dY + 0.16, w: 1.42, h: dH - 0.32,
        fontFace: SANS, fontSize: 11.5, bold: true, color: AMBER, align: "center", lineSpacing: 15, margin: 0, valign: "middle",
      });
      s.addText("→", {
        isTextBox: true, x: dX + 1.45, y: dY, w: 0.4, h: dH,
        fontFace: SANS, fontSize: 17, color: ICE, align: "center", margin: 0, valign: "middle",
      });
      for (let b = 0; b < 20; b++) {
        s.addShape(pres.ShapeType.rect, {
          x: dX + 1.92 + (b % 5) * 0.24, y: dY + 0.19, w: 0.18, h: 0.145,
          fill: { color: b % 3 === 0 ? AMBER : b % 3 === 1 ? "C98F3C" : "8C6A33" },
          line: { width: 0, color: NAVY_DEEP },
        }, {});
      }
      for (let b = 0; b < 15; b++) {
        s.addShape(pres.ShapeType.rect, {
          x: dX + 1.92 + (b % 5) * 0.24, y: dY + 0.39 + Math.floor(b / 5) * 0.2, w: 0.18, h: 0.145,
          fill: { color: b % 3 === 1 ? AMBER : b % 3 === 2 ? "C98F3C" : "8C6A33" },
          line: { width: 0, color: NAVY_DEEP },
        });
      }
      s.addText("learned, not chosen by me", {
        isTextBox: true, x: dX, y: dY + dH + 0.06, w: dW, h: 0.28,
        fontFace: SANS, fontSize: 10.5, italic: true, color: ICE, margin: 0,
      });
    }

    s.addText(r.dim, {
      isTextBox: true, x: x + 0.32, y: 3.88, w: 3.1, h: 0.78,
      fontFace: SERIF, fontSize: 40, bold: true, color: dark ? WHITE : NAVY, margin: 0, valign: "middle",
    });
    s.addText("numbers per 0.25 s window", {
      isTextBox: true, x: x + 0.32, y: 4.64, w: 3.1, h: 0.28,
      fontFace: SANS, fontSize: 11, color: dark ? ICE : SLATE, margin: 0,
    });
    s.addText(r.line1, {
      isTextBox: true, x: x + 0.32, y: 4.96, w: 3.1, h: 0.5,
      fontFace: SANS, fontSize: 13, bold: true, color: dark ? WHITE : NAVY,
      lineSpacing: 17, margin: 0, valign: "top",
    });
  });

  takeaway(s, "Two are built by hand. One is learned — and used frozen, with no fine-tuning.", 5.82);
  caption(s, "Perch v2 was pretrained on a very large multi-taxa sound collection. It needs one adaptation before it can hear a bat.", M, 6.58, 11.9, { size: 10.5 });

  s.addNotes(
    "Three representations, and then a deliberately boring classifier.\n\n" +
    "The baseline is what a bioacoustician would build by hand: temporal mean, standard deviation and maximum for each of 513 " +
    "frequency bins, plus four global statistics. Fifteen hundred and forty-three numbers, every one of them interpretable.\n\n" +
    "The compact version is the same idea with the frequency axis coarsened into 64 bands instead of 513 bins — 199 numbers. " +
    "I included it to ask whether the fine frequency detail is doing any work.\n\n" +
    "Perch v2 is different in kind. It is a pretrained network trained on a very large multi-taxa sound collection, and I use it " +
    "frozen — no fine-tuning at all. I just take its 1,536-dimensional embedding.\n\n" +
    "Downstream everything is identical: a standard scaler fitted on training data only, L2 logistic regression, C of one, " +
    "balanced class weights, threshold 0.5. So any difference I show you is a difference between representations, not between classifiers.\n\n" +
    "One catch: Perch cannot listen to a bat."
  );
}

// ================================================================ 8 · THE ADAPTATION
{
  const s = lightSlide("METHOD · THE KEY ADAPTATION", "Perch hears up to 16 kHz. Bats call at 20–120.", "Tenfold time expansion");

  const panW = 5.0, panH = 1.15, gap = 1.35;
  const leftX = (W - (panW * 2 + gap)) / 2;
  const rightX = leftX + panW + gap;
  const panY = 2.55;

  [[leftX, "AS RECORDED", "0.25 s   ·   0 – 192 kHz", "every call is above the model's ceiling", CORAL],
   [rightX, "AS PERCH READS IT", "2.5 s   ·   0 – 19.2 kHz", "the same pattern, now inside the ceiling", TEAL]].forEach(
    ([x, tag, axes, note, col]) => {
      s.addShape(pres.ShapeType.roundRect, {
        x: x - 0.18, y: panY - 0.55, w: panW + 0.36, h: panH + 1.55, rectRadius: 0.06,
        fill: { color: PALE }, line: { color: BORDER, width: 1 },
      });
      s.addText(tag, {
        isTextBox: true, x: x, y: panY - 0.45, w: panW, h: 0.3,
        fontFace: SANS, fontSize: 11, bold: true, color: col, charSpacing: 1.6, margin: 0,
      });
      s.addImage({ path: A("buzz_spec.jpg"), x: x, y: panY, w: panW, h: panH });
      s.addText(axes, {
        isTextBox: true, x: x, y: panY + panH + 0.14, w: panW, h: 0.32,
        fontFace: SERIF, fontSize: 17, bold: true, color: NAVY, margin: 0,
      });
      s.addText(note, {
        isTextBox: true, x: x, y: panY + panH + 0.5, w: panW, h: 0.32,
        fontFace: SANS, fontSize: 12, color: SLATE, margin: 0,
      });
    }
  );

  s.addShape(pres.ShapeType.ellipse, {
    x: leftX + panW + 0.28, y: panY + 0.18, w: 0.79, h: 0.79,
    fill: { color: NAVY_DEEP }, line: { color: NAVY_DEEP, width: 0 },
  });
  s.addText("×10", {
    isTextBox: true, x: leftX + panW + 0.28, y: panY + 0.18, w: 0.79, h: 0.79,
    fontFace: SANS, fontSize: 17, bold: true, color: AMBER, align: "center", margin: 0, valign: "middle",
  });

  takeaway(s, "Resample 384 → 320 kHz, then let a 32 kHz model read it: time ×10, frequency ÷10, pattern intact.", 5.5);
  caption(s, "Only Perch carries this conversion — the comparison is between whole pipelines, not architectures.", M, 6.32, 11.9, { size: 10.5 });

  s.addNotes(
    "This is the one piece of engineering I want to spend a slide on, because it is what makes the rest possible.\n\n" +
    "Perch was built for birds, and it expects 32 kilohertz audio. A 32 kilohertz frontend can only represent frequencies up to " +
    "16 kilohertz. Bat echolocation in this dataset sits between roughly 20 and 120 kilohertz. So if I simply downsample the " +
    "recordings, I delete the entire signal and hand the model silence.\n\n" +
    "Instead I resample from 384 to 320 kilohertz, and then let Perch read those samples as though they were 32 kilohertz. " +
    "That is a tenfold time expansion. A quarter of a second of real audio becomes two and a half seconds for the model, and every " +
    "frequency drops by a factor of ten — so a 100 kilohertz call arrives at 10 kilohertz, comfortably inside what the model can see.\n\n" +
    "The two panels are the same spectrogram. Nothing about the pattern changes; only the axes move. That is the point — the " +
    "relative structure of the pulse train, which is what identifies a buzz, is preserved exactly.\n\n" +
    "I should be straight about the cost: only the Perch route carries this step. So what I compare is three complete pipelines, " +
    "not three architectures under identical preprocessing. I come back to that in the limitations."
  );
}

// ================================================================ 9 · RESULT 1
{
  const s = lightSlide("RESULT · QUESTION 1", "The gap closes — for one of the three", "Detection performance");

  s.addChart(
    pres.ChartType.bar,
    [
      { name: "Random split", labels: ["Baseline (1,543-d)", "Compact (199-d)", "Perch v2 (1,536-d)"], values: [0.930, 0.905, 1.000] },
      { name: "Worst held-out site", labels: ["Baseline (1,543-d)", "Compact (199-d)", "Perch v2 (1,536-d)"], values: [0.727, 0.691, 0.950] },
    ],
    {
      x: M - 0.1, y: 1.85, w: 8.1, h: 3.5,
      barDir: "col", barGapWidthPct: 60,
      chartColors: [ICE, TEAL],
      showLegend: true, legendPos: "t", legendFontFace: SANS, legendFontSize: 11, legendColor: NAVY,
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000",
      dataLabelFontFace: SANS, dataLabelFontSize: 10.5, dataLabelColor: NAVY,
      valAxisMinVal: 0.6, valAxisMaxVal: 1.05, valAxisMajorUnit: 0.1,
      valAxisLabelFontFace: SANS, valAxisLabelFontSize: 10, valAxisLabelColor: SLATE,
      catAxisLabelFontFace: SANS, catAxisLabelFontSize: 11, catAxisLabelColor: NAVY,
      valGridLine: { color: "EDF1F7", size: 1 },
      catGridLine: { style: "none" },
      valAxisLineShow: false, catAxisLineShow: true, catAxisLineColor: BORDER,
    }
  );

  const notes = [
    ["Perch's worst site beats the baseline's average", "0.950 against 0.872 mean F1"],
    ["And it is steady, not just high", "Spread across sites 0.020, vs 0.101 and 0.114"],
    ["More features bought nothing", "199 dimensions matched 1,543 to within 0.002 F1"],
  ];
  notes.forEach(([h, b], i) => {
    const y = 1.88 + i * 1.24;
    s.addShape(pres.ShapeType.roundRect, {
      x: 8.5, y: y, w: 4.13, h: 1.12, rectRadius: 0.06,
      fill: { color: i === 0 ? NAVY_DEEP : PALE }, line: { color: i === 0 ? NAVY_DEEP : BORDER, width: 1 },
    });
    s.addText(h, {
      isTextBox: true, x: 8.78, y: y + 0.13, w: 3.6, h: 0.5,
      fontFace: SANS, fontSize: 12.5, bold: true, color: i === 0 ? AMBER : NAVY, lineSpacing: 16, margin: 0, valign: "top",
    });
    s.addText(b, {
      isTextBox: true, x: 8.78, y: y + 0.63, w: 3.6, h: 0.42,
      fontFace: SANS, fontSize: 11, color: i === 0 ? ICE : SLATE, lineSpacing: 15, margin: 0, valign: "top",
    });
  });

  caption(s, "F1 on 316 balanced Ontario clips. Six rounds, each recording site held out in turn, scaler and detector refitted inside every round. Two of the six groups share a site — see limitations.", M, 5.72, 11.9, { size: 10.5, h: 0.8 });

  s.addNotes(
    "Here is the answer to question one, in the same shape as the gap slide.\n\n" +
    "The pale bars are the flattering random split. The teal bars are the worst site the detector had never heard. For both " +
    "hand-crafted representations the bar collapses — 0.930 down to 0.727, and 0.905 down to 0.691. For Perch it barely moves: " +
    "1.000 down to 0.950.\n\n" +
    "The comparison I would put weight on is this one: Perch's WORST site, 0.950, is better than the baseline's AVERAGE across " +
    "all six folds, which is 0.872. And the spread tells the same story — a standard deviation of 0.020 across folds against 0.101 " +
    "and 0.114. It is not only better on average, it is stable, and stability is what you need if you are going to point a detector " +
    "at a place you have no labels for.\n\n" +
    "One honest aside on the compact representation: 199 dimensions matched 1,543 to within two thousandths of an F1 point. Eight " +
    "times fewer features, the same answer. More hand-crafted detail was not buying anything.\n\n" +
    "I should also say the grouped-site split did not discriminate: all three reached F1 of exactly 1.000, so that test told me nothing.\n\n" +
    "Classification needs a threshold, though. In a real review workflow, you do not want a yes/no — you want an ordered queue."
  );
}

// ================================================================ 10 · QUESTION 2
{
  const s = darkSlide();
  s.addImage({ path: A("buzz_strip.jpg"), x: 0, y: 6.45, w: W, h: 1.05, transparency: 45 });
  s.addText("02", {
    isTextBox: true, x: M, y: 1.85, w: 2.2, h: 1.5,
    fontFace: SERIF, fontSize: 90, bold: true, color: AMBER, margin: 0, valign: "middle",
  });
  s.addText("Can it put the right clips\nat the top of a reviewer's list,\nwith no threshold at all?", {
    isTextBox: true, x: M, y: 3.25, w: 11.0, h: 2.4,
    fontFace: SERIF, fontSize: 40, bold: true, color: WHITE, lineSpacing: 50, margin: 0, valign: "top",
  });
  s.addNotes(
    "Question two. Forget the threshold. Give me one labelled buzz, and rank everything else by how similar it looks in the " +
    "representation. That is query-by-example retrieval, and it is much closer to how a person would actually use this: not " +
    "'is this a buzz, yes or no', but 'show me the twenty clips most worth my time'.\n\n" +
    "I used all 158 labelled buzz clips as queries in turn, and — importantly — removed every clip from the query's own site " +
    "from the candidate pool. So the model is always retrieving across sites, never within one."
  );
}

// ================================================================ 11 · RESULT 2
{
  const s = lightSlide("RESULT · QUESTION 2", "Ten results. How many are real?", "Similarity retrieval");

  const rows = [
    { name: "Perch v2", hits: 9.84, p10: "0.984", col: TEAL, strong: true },
    { name: "Baseline", hits: 8.31, p10: "0.831", col: "8FA3BF", strong: false },
    { name: "Random ranking", hits: 5.0, p10: "0.500", col: "C3D2E8", strong: false },
  ];
  const tileW = 0.68, tileGap = 0.13, startX = 2.95;
  rows.forEach((r, ri) => {
    const y = 2.22 + ri * 1.2;
    s.addText(r.name, {
      isTextBox: true, x: M, y: y, w: 2.15, h: 0.7,
      fontFace: SANS, fontSize: r.strong ? 15 : 14, bold: r.strong, color: r.strong ? NAVY : SLATE,
      margin: 0, valign: "middle",
    });
    for (let i = 0; i < 10; i++) {
      const filled = i < Math.floor(r.hits);
      const partial = i === Math.floor(r.hits) && r.hits % 1 > 0.4;
      s.addShape(pres.ShapeType.roundRect, {
        x: startX + i * (tileW + tileGap), y: y + 0.06, w: tileW, h: 0.58, rectRadius: 0.05,
        fill: filled ? { color: r.col } : partial ? { color: r.col, transparency: 55 } : { color: "F4F7FA" },
        line: { color: filled || partial ? r.col : BORDER, width: 1 },
      });
    }
    s.addText(r.p10, {
      isTextBox: true, x: 11.25, y: y, w: 1.4, h: 0.7,
      fontFace: SERIF, fontSize: r.strong ? 24 : 20, bold: true, color: r.strong ? TEAL : SLATE,
      align: "right", margin: 0, valign: "middle",
    });
  });
  s.addText("Precision@10", {
    isTextBox: true, x: 10.9, y: 1.85, w: 1.75, h: 0.3,
    fontFace: SANS, fontSize: 10.5, bold: true, color: SLATE, align: "right", charSpacing: 1, margin: 0,
  });
  s.addText("the first ten results  →", {
    isTextBox: true, x: startX - 0.02, y: 1.85, w: 3.4, h: 0.3,
    fontFace: SANS, fontSize: 10.5, bold: true, color: SLATE, charSpacing: 1, margin: 0,
  });

  takeaway(s, "Same ordering as detection — and the separation sits right at the top, where a reviewer looks.", 5.6);
  caption(s, "158 buzz queries · the query's own site removed from the candidate pool · cosine similarity · averaged over sites. Average Precision 0.879 vs 0.770 and 0.771.", M, 6.32, 11.9, { size: 10.5, h: 0.55 });

  s.addNotes(
    "Read each row as: if a reviewer opened the top ten results, how many would be real feeding buzzes?\n\n" +
    "An unguided reviewer, working through a balanced pool at random, gets five. The hand-crafted baseline gets about eight — " +
    "Precision at ten of 0.831. Perch gets essentially ten — 0.984. And this holds while retrieving across sites, because I removed " +
    "everything from the query's own site from the pool every time.\n\n" +
    "Two things worth noticing. First, the ordering is the same as in detection, which is reassuring: it is not an artefact of the " +
    "classifier or the threshold. Second, the separation is concentrated at the top of the ranking — Perch's Average Precision over " +
    "the whole list, 0.879, is lower than its precision at ten. For a review workflow that is exactly the right shape of error: " +
    "the list is at its most trustworthy where people actually look.\n\n" +
    "I want to be honest about difficulty, though. This candidate pool is balanced, which is why random scores 0.5. In continuous " +
    "field recordings buzzes are far rarer than that, so this is an easier problem than the one I turn to next."
  );
}

// ================================================================ 12 · QUESTION 3
{
  const s = darkSlide();
  s.addImage({ path: A("buzz_strip.jpg"), x: 0, y: 6.45, w: W, h: 1.05, transparency: 45 });
  s.addText("03", {
    isTextBox: true, x: M, y: 1.85, w: 2.2, h: 1.5,
    fontFace: SERIF, fontSize: 90, bold: true, color: AMBER, margin: 0, valign: "middle",
  });
  s.addText("Does any of it survive\na real night in the field?", {
    isTextBox: true, x: M, y: 3.25, w: 11.0, h: 1.8,
    fontFace: SERIF, fontSize: 40, bold: true, color: WHITE, lineSpacing: 50, margin: 0, valign: "top",
  });
  s.addText("9.4 h · 564 recordings · one AudioMoth · Mara Triangle, Kenya · no ground truth", {
    isTextBox: true, x: M, y: 5.05, w: 11.0, h: 0.4,
    fontFace: SANS, fontSize: 15, color: ICE, margin: 0,
  });
  s.addNotes(
    "Question three, and the hardest one. Everything so far has been curated clips from Ontario, balanced fifty-fifty, with labels.\n\n" +
    "Now I take the Perch pipeline, unchanged, and point it at nine and a half hours of continuous recording from a single " +
    "AudioMoth in the Mara Triangle in Kenya. Different continent, different bats, different insects, and — this is the crucial " +
    "constraint — no exhaustive ground truth. Nobody has listened to all of it, so I cannot compute precision or recall here. " +
    "What I can do is ask what the detector puts at the top, and then look at it myself."
  );
}

// ================================================================ 13 · RESULT 3a
{
  const s = lightSlide("RESULT · QUESTION 3 · MARA TRIANGLE, KENYA", "The score ranks. It does not identify.", "Reviewed Kenya candidates");

  const imgW = 5.55, imgH = imgW / 2.797;
  const lx = M, rx = M + imgW + 0.82;
  [[lx, "kenya_A.jpg", "Buzz-like", "score 1.000", TEAL],
   [rx, "kenya_C.jpg", "Insect-like", "score 0.999", CORAL]].forEach(([x, file, lab, sc, col]) => {
    s.addShape(pres.ShapeType.roundRect, {
      x: x - 0.14, y: 1.78, w: imgW + 0.28, h: imgH + 0.7, rectRadius: 0.06,
      fill: { color: PALE }, line: { color: BORDER, width: 1 },
    });
    s.addImage({ path: A(file), x: x, y: 1.9, w: imgW, h: imgH });
    s.addText([
      { text: lab, options: { bold: true, color: col } },
      { text: "   ·   " + sc, options: { color: SLATE } },
    ], {
      isTextBox: true, x: x, y: 1.98 + imgH, w: imgW, h: 0.34,
      fontFace: SANS, fontSize: 13, margin: 0, valign: "middle",
    });
  });
  caption(s, "1.25 s of context; the cyan band is the scored 0.25 s window.", M, 2.62 + imgH, 11.9, { size: 10.5 });

  // category strip for the 69 reviewed candidates
  const cats = [
    ["Insect-like", 27, CORAL, WHITE],
    ["Buzz-like", 19, TEAL, WHITE],
    ["Background", 10, "9FB0C8", NAVY],
    ["Artefact", 9, "6E819F", WHITE],
    ["Click", 3, "C3D2E8", NAVY],
    ["Unclear", 1, "E7EDF4", NAVY],
  ];
  const stripX = M, stripY = 4.98, stripW = W - 2 * M, total = 69;
  let cx = stripX;
  cats.forEach(([lab, n, col, txt]) => {
    const w = (stripW * n) / total;
    s.addShape(pres.ShapeType.rect, {
      x: cx, y: stripY, w: w, h: 0.5,
      fill: { color: col }, line: { color: WHITE, width: 1.5 },
    });
    if (n >= 9) {
      s.addText(`${lab}  ${n}`, {
        isTextBox: true, x: cx, y: stripY, w: w, h: 0.5,
        fontFace: SANS, fontSize: 11.5, bold: true, color: txt,
        align: "center", margin: 0, valign: "middle",
      });
    }
    cx += w;
  });
  s.addText("69 top-ranked candidates, one per recording, reviewed by hand", {
    isTextBox: true, x: stripX, y: stripY + 0.56, w: stripW, h: 0.3,
    fontFace: SANS, fontSize: 10.5, italic: true, color: SLATE, margin: 0,
  });

  takeaway(s, "27 of the 69 were insect pulse trains — ranking is not identification.", 6.05);

  s.addNotes(
    "Both of these panels scored essentially 1.0. The one on the left is a feeding buzz. The one on the right is an insect.\n\n" +
    "That is the honest headline of question three. The Perch score is a good ranker — it pulled genuinely pulse-like structure " +
    "to the top of two hundred and seventy thousand windows — but it is not an identifier. Insects produce pulse trains too, and " +
    "at the level of a single quarter-second window they look very similar.\n\n" +
    "The strip along the bottom is what the sixty-nine top-ranked candidates actually were when I reviewed each one with 1.25 " +
    "seconds of surrounding context, its pulse timing and time-expanded audio. Nineteen were buzz-like. Twenty-seven — the " +
    "largest single category — were insect-like. The rest were background, recording artefacts, single clicks and one I could not call.\n\n" +
    "Two caveats I want to state plainly. These candidates were selected BY the Perch score, so those proportions describe the " +
    "reviewed set, not the prevalence of buzzes in the recordings. And my category labels are my own descriptive judgements, not " +
    "verified ground truth.\n\n" +
    "What separated the two panels was context — the wider window showed the insect's pulse train continuing, where a real buzz " +
    "compresses and stops."
  );
}

// ================================================================ 14 · RESULT 3b
{
  const s = lightSlide("RESULT · QUESTION 3", "High scores arrive after sunset", "Temporal pattern");

  const chH = 4.2, chW = chH * 1.2254;
  s.addShape(pres.ShapeType.roundRect, {
    x: M - 0.1, y: 1.78, w: chW + 0.35, h: chH + 0.3, rectRadius: 0.06,
    fill: { color: WHITE }, line: { color: BORDER, width: 1 },
  });
  s.addImage({ path: A("hour_of_day.jpg"), x: M + 0.05, y: 1.9, w: chW, h: chH });

  const pts = [
    ["Nothing in daylight", "The recorder ran 18:00–23:00 and 00:00–05:00 EAT."],
    ["Peak at 23:00 EAT", "30.1% of windows ≥ 0.50, against about 5% at 04:00."],
    ["Consistent with foraging", "What you would expect of foraging bats — but these are candidates, not confirmed buzzes."],
  ];
  const txtX = M + chW + 0.5;
  pts.forEach(([h, b], i) => {
    const y = 1.95 + i * 1.42;
    s.addText(h, {
      isTextBox: true, x: txtX, y: y, w: W - M - txtX, h: 0.34,
      fontFace: SANS, fontSize: 14, bold: true, color: i === 2 ? SLATE : NAVY, margin: 0,
    });
    s.addText(b, {
      isTextBox: true, x: txtX, y: y + 0.36, w: W - M - txtX, h: 0.95,
      fontFace: SANS, fontSize: 12, color: SLATE, lineSpacing: 17, margin: 0, valign: "top",
    });
  });

  caption(s, "Windows above each Perch threshold, by hour of day (EAT, UTC+3). Descriptive — no ground truth exists for this site.", M, 6.32, 11.9, { size: 10.5 });

  s.addNotes(
    "This is the part that takes us back to the opening question — where and when do bats feed.\n\n" +
    "This plots the percentage of scored windows above each threshold against hour of day. There is nothing in daylight, which is " +
    "partly because the recorder only ran from six in the evening to eleven, and midnight to five. Within the dark hours, though, " +
    "there is a clear gradient: the rate climbs through the evening and peaks at eleven at night, where thirty percent of windows " +
    "scored above 0.5, against about five percent at four in the morning.\n\n" +
    "I want to be careful about what I claim. This is a distribution of detector scores, not of confirmed feeding buzzes — and we " +
    "have just seen that a large share of the high-scoring windows are insects. So I present this as a descriptive pattern that is " +
    "consistent with nocturnal foraging activity, and as an illustration of the kind of question this pipeline could answer once " +
    "the candidates are verified. It is not, yet, a measurement of when bats feed."
  );
}

// ================================================================ 15 · LIMITATIONS
{
  const s = lightSlide("HONEST LIMITS", "Four things this study cannot tell you", "Limitations");

  const lims = [
    ["Two groups, one site", "Two of the six recording groups come from the same site, so the held-out test is group-level, not strict five-site isolation."],
    ["A duration shortcut survives", "127 buzz clips padded, every non-buzz clip cropped — duration partly encodes the label."],
    ["Pipelines, not architectures", "Only Perch carries the ×10 expansion, so the gain is not the embedding alone."],
    ["No Kenya ground truth", "Candidates were chosen by score, so no precision or recall can be computed."],
  ];
  lims.forEach(([h, b], i) => {
    const x = M + (i % 2) * 6.2;
    const y = 1.95 + Math.floor(i / 2) * 2.05;
    s.addShape(pres.ShapeType.roundRect, {
      x: x, y: y, w: 5.75, h: 1.8, rectRadius: 0.06,
      fill: { color: PALE }, line: { color: BORDER, width: 1 },
    });
    s.addShape(pres.ShapeType.ellipse, {
      x: x + 0.32, y: y + 0.3, w: 0.42, h: 0.42,
      fill: { color: CORAL }, line: { color: CORAL, width: 0 },
    });
    s.addText(String(i + 1), {
      isTextBox: true, x: x + 0.32, y: y + 0.3, w: 0.42, h: 0.42,
      fontFace: SANS, fontSize: 12, bold: true, color: WHITE, align: "center", margin: 0, valign: "middle",
    });
    s.addText(h, {
      isTextBox: true, x: x + 0.92, y: y + 0.28, w: 4.6, h: 0.36,
      fontFace: SANS, fontSize: 14.5, bold: true, color: NAVY, margin: 0, valign: "middle",
    });
    s.addText(b, {
      isTextBox: true, x: x + 0.92, y: y + 0.68, w: 4.6, h: 0.95,
      fontFace: SANS, fontSize: 11.5, color: SLATE, lineSpacing: 16, margin: 0, valign: "top",
    });
  });

  takeaway(s, "Every one of these has a concrete fix — that is the next project.", 6.15);

  s.addNotes(
    "Four limitations, and I would rather raise them than have you find them.\n\n" +
    "One. The six recording groups I hold out are not six separate places. Two of them, buzzes_sp and buzzes_spmylu, come from the " +
    "same location — Site 4 — so in those two rounds a companion group from the same place was still in training. My headline test " +
    "therefore measures group-level robustness, not strict isolation of five locations. The grouped-site test on buzzes_tb is genuinely geographically separated, and Perch " +
    "held up there too, but I do not want to overstate the main result.\n\n" +
    "Two. A duration shortcut. Buzz clips tend to be shorter than non-buzz clips, so when I pad or crop everything to a fixed " +
    "window, the padding itself partly encodes the label. At half a second that shortcut is complete — every buzz padded, every " +
    "non-buzz cropped — which is exactly why the half-second result of 0.994 is not the one I report. At a quarter of a second it " +
    "is weakened but not gone: 127 buzz clips are still padded. A duration-matched benchmark would quantify it.\n\n" +
    "Three. Only Perch carries the resampling and time expansion, so strictly I have compared three pipelines, not three " +
    "representations under identical preprocessing. Testing other expansion factors would separate those.\n\n" +
    "Four. Kenya has no exhaustive labels, so nothing I show from it is a precision or recall figure.\n\n" +
    "Each of these has a concrete fix, and that is what I would do next."
  );
}

// ================================================================ 16 · CONCLUSIONS
{
  const s = darkSlide();
  s.addImage({ path: A("buzz_strip.jpg"), x: 0, y: 6.45, w: W, h: 1.05, transparency: 45 });

  s.addText("SO — WHERE DO BATS FEED?", {
    isTextBox: true, x: M, y: 0.72, w: 9.0, h: 0.32,
    fontFace: SANS, fontSize: 11.5, bold: true, color: AMBER, charSpacing: 2.4, margin: 0,
  });
  s.addText("A little closer than we were", {
    isTextBox: true, x: M, y: 1.12, w: 11.5, h: 0.72,
    fontFace: SERIF, fontSize: 34, bold: true, color: WHITE, margin: 0, valign: "middle",
  });

  const answers = [
    ["01", "Representation decides transfer", "Frozen, time-expanded Perch: 0.989 mean F1 across held-out sites, worst site 0.950."],
    ["02", "It ranks as well as it classifies", "Precision@10 of 0.984 against 0.831, with the query's own site removed."],
    ["03", "The field still needs a human", "Insect pulse trains were the largest category among the top-ranked Kenya candidates."],
  ];
  answers.forEach(([n, h, b], i) => {
    const y = 2.25 + i * 1.15;
    s.addText(n, {
      isTextBox: true, x: M, y: y, w: 0.8, h: 0.9,
      fontFace: SERIF, fontSize: 26, bold: true, color: AMBER, margin: 0, valign: "middle",
    });
    s.addText(h, {
      isTextBox: true, x: M + 0.85, y: y + 0.04, w: 5.0, h: 0.38,
      fontFace: SANS, fontSize: 16, bold: true, color: WHITE, margin: 0, valign: "middle",
    });
    s.addText(b, {
      isTextBox: true, x: M + 6.0, y: y + 0.02, w: 5.93, h: 0.85,
      fontFace: SANS, fontSize: 13, color: ICE, lineSpacing: 18, margin: 0, valign: "top",
    });
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 5.75, w: W - 2 * M, h: 0.72, rectRadius: 0.06,
    fill: { color: "16294A" }, line: { color: "24406B", width: 1 },
  });
  s.addText([
    { text: "NEXT   ", options: { bold: true, color: AMBER, charSpacing: 1.6 } },
    { text: "An independently sampled, exhaustively reviewed Kenya subset — event-level precision and recall, and those insect pulse trains as hard negatives.", options: { color: WHITE } },
  ], {
    isTextBox: true, x: M + 0.3, y: 5.75, w: W - 2 * M - 0.6, h: 0.72,
    fontFace: SANS, fontSize: 13.5, margin: 0, valign: "middle",
  });

  s.addNotes(
    "So, back to where I started.\n\n" +
    "One. How you represent the sound is what decides whether a detector survives a new site. A frozen, time-expanded Perch " +
    "embedding reached 0.989 mean F1 across held-out sites with a worst site of 0.950, where hand-crafted spectral statistics " +
    "fell to 0.727.\n\n" +
    "Two. The same representation ranks as well as it classifies — 0.984 precision at ten across sites — which is what you would " +
    "actually deploy, because it needs no threshold and it puts its best work at the top of the queue.\n\n" +
    "Three. And in the field, none of that removes the human. The largest category among my top-ranked Kenya candidates was " +
    "insects, not bats. What the pipeline buys you is a shortlist of sixty-nine instead of two hundred and seventy thousand — which " +
    "is the difference between an impossible job and an afternoon.\n\n" +
    "The next step is the obvious one: an independently sampled, exhaustively reviewed Kenya subset. That would give real " +
    "event-level precision and recall, let both detectors be compared on the same confirmed events, and turn those insect pulse " +
    "trains into hard negatives for retraining.\n\n" +
    "Thank you — I am happy to take questions."
  );
}

// ================================================================ 17 · THANKS
{
  const s = darkSlide();
  s.addImage({ path: A("buzz_strip.jpg"), x: 0, y: 4.6, w: W, h: 1.05 });
  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 5.65, w: W, h: H - 5.65,
    fill: { color: NAVY_DEEP }, line: { color: NAVY_DEEP, width: 0 },
  });
  s.addImage({ path: A("bat_white.png"), x: 0.75, y: 4.75, w: 1.5, h: 0.34, transparency: 15 });

  s.addText("Thank you", {
    isTextBox: true, x: M, y: 1.85, w: 9.0, h: 1.1,
    fontFace: SERIF, fontSize: 54, bold: true, color: WHITE, margin: 0, valign: "middle",
  });
  s.addText("Questions welcome", {
    isTextBox: true, x: M, y: 3.0, w: 9.0, h: 0.5,
    fontFace: SANS, fontSize: 20, color: AMBER, margin: 0, valign: "middle",
  });
  s.addText("With thanks to Santiago Martinez Balvanera and Kate Jones for their supervision, and to the researchers who collected and shared the Kenya recordings.", {
    isTextBox: true, x: M, y: 5.95, w: 8.6, h: 0.9,
    fontFace: SANS, fontSize: 12, color: ICE, lineSpacing: 18, margin: 0, valign: "top",
  });
  s.addText("Backup slides follow →", {
    isTextBox: true, x: 9.4, y: 6.35, w: 3.2, h: 0.32,
    fontFace: SANS, fontSize: 11, color: SLATE, align: "right", margin: 0,
  });
  s.addNotes("Thank you. I am happy to take questions. I have backup slides on the full metric tables, the preprocessing sensitivity analysis, the Kenya threshold counts and the implementation settings.");
}

// ================================================================ BACKUP
function backupSlide(tag, title) {
  const s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText(tag, {
    isTextBox: true, x: M, y: 0.42, w: 11.0, h: 0.28,
    fontFace: SANS, fontSize: 11, bold: true, color: CORAL, charSpacing: 2.4, margin: 0, valign: "middle",
  });
  s.addText(title, {
    isTextBox: true, x: M, y: 0.72, w: 11.9, h: 0.6,
    fontFace: SERIF, fontSize: 28, bold: true, color: NAVY, margin: 0, valign: "middle",
  });
  s.addText(tag.replace("BACKUP ", "B"), {
    isTextBox: true, x: W - M - 1.0, y: 6.92, w: 1.0, h: 0.3,
    fontFace: SANS, fontSize: 9, color: SLATE, align: "right", margin: 0, valign: "middle",
  });
  return s;
}

const tblHead = {
  fill: { color: NAVY_DEEP }, color: WHITE, bold: true,
  fontFace: SANS, fontSize: 10.5, align: "center", valign: "middle",
};
const tblOpts = {
  fontFace: SANS, fontSize: 10.5, color: NAVY, align: "center", valign: "middle",
  border: [{ type: "solid", color: BORDER, pt: 0.5 }],
};

// ---- B1 detection
{
  const s = backupSlide("BACKUP 1", "Detection — full metric set");
  const head = ["Representation", "Random F1", "Grouped-site F1", "LOFO mean F1", "LOFO SD", "Worst folder", "LOFO accuracy", "LOFO ROC-AUC", "LOFO AP"];
  const body = [
    ["Baseline (1,543-d)", "0.930", "1.000", "0.872", "0.101", "0.727", "0.883", "0.9728", "0.9744"],
    ["Compact (199-d)", "0.905", "1.000", "0.870", "0.114", "0.691", "0.881", "0.9716", "0.9737"],
    ["Perch v2 (1,536-d)", "1.000", "1.000", "0.989", "0.020", "0.950", "0.990", "0.9997", "0.9996"],
  ];
  s.addTable(
    [head.map((h) => ({ text: h, options: tblHead }))].concat(
      body.map((r, ri) =>
        r.map((c, ci) => ({
          text: c,
          options: {
            ...tblOpts,
            align: ci === 0 ? "left" : "center",
            bold: ri === 2,
            fill: { color: ri === 2 ? "E9F3F1" : ri % 2 ? "FBFCFE" : WHITE },
          },
        }))
      )
    ),
    { x: M, y: 1.65, w: W - 2 * M, colW: [2.5, 1.16, 1.35, 1.28, 0.95, 1.2, 1.28, 1.3, 0.91], rowH: 0.42 }
  );
  s.addText([
    { text: "LOFO mean precision / recall  ", options: { bold: true, color: NAVY } },
    { text: "0.910 / 0.857 (baseline) · 0.910 / 0.851 (compact) · 0.994 / 0.984 (Perch).", options: { color: SLATE, breakLine: true } },
    { text: "Folder-level range  ", options: { bold: true, color: NAVY } },
    { text: "baseline F1 0.727 (buzzes_sp) → 1.000 (buzzes_tb); compact low 0.691 (buzzes_sp); Perch 0.950 (buzzes_o), 0.983 (buzzes_sp), 1.000 in the other four rounds.", options: { color: SLATE, breakLine: true } },
    { text: "Splits  ", options: { bold: true, color: NAVY } },
    { text: "Random: 222 train / 48 validation / 46 test, stratified.  Grouped-site: buzzes_o (Site 3) validation, buzzes_tb (Site 2) test, 229 train.  LOFO: six rounds, scaler and detector refitted inside each round. Representation definitions, detector settings and the 0.5 threshold were fixed independently of the reserved validation set.", options: { color: SLATE } },
  ], {
    isTextBox: true, x: M, y: 3.45, w: W - 2 * M, h: 2.2,
    fontFace: SANS, fontSize: 12, lineSpacing: 19, margin: 0, valign: "top",
  });
  s.addNotes("Backup: full detection metric set, including accuracy, ROC-AUC and Average Precision averaged over the six LOFO rounds.");
}

// ---- B2 retrieval
{
  const s = backupSlide("BACKUP 2", "Retrieval — full metric set");
  const head = ["Representation", "Precision@5", "Precision@10", "Precision@20", "Average Precision"];
  const body = [
    ["Baseline", "0.834", "0.831", "0.822", "0.770"],
    ["Compact", "0.839", "0.830", "0.821", "0.771"],
    ["Perch v2", "0.988", "0.984", "0.968", "0.879"],
    ["Random ranking", "0.500", "0.500", "0.501", "0.510"],
  ];
  s.addTable(
    [head.map((h) => ({ text: h, options: tblHead }))].concat(
      body.map((r, ri) =>
        r.map((c, ci) => ({
          text: c,
          options: {
            ...tblOpts,
            align: ci === 0 ? "left" : "center",
            bold: ri === 2,
            fill: { color: ri === 2 ? "E9F3F1" : ri === 3 ? "F7F9FC" : WHITE },
          },
        }))
      )
    ),
    { x: M, y: 1.65, w: 9.4, colW: [2.6, 1.7, 1.7, 1.7, 1.7], rowH: 0.42 }
  );
  s.addText([
    { text: "All 158 labelled buzz clips used as queries; every clip from the query's own folder excluded from the candidate pool.", options: { breakLine: true } },
    { text: "StandardScaler fitted on the cross-folder candidate pool only, then applied to both pool and query; vectors L2-normalised and ranked by cosine similarity.", options: { breakLine: true } },
    { text: "Folder-level values macro-averaged so folders with more queries do not dominate.", options: { breakLine: true } },
    { text: "Perch Precision@10 ranged 0.948 (buzzes_o queries) to 1.000 (buzzes_tb); folder-level AP ranged 0.750 to 0.955.", options: { breakLine: true } },
    { text: "Random baseline: 100 seeded permutations per query (seed 42), generator advancing between repetitions. Roughly balanced pools put random Precision@10 at ≈ 0.500 — easier than naturally rare field events.", options: {} },
  ], {
    isTextBox: true, x: M, y: 4.0, w: W - 2 * M, h: 2.4,
    fontFace: SANS, fontSize: 12, color: SLATE, lineSpacing: 20, margin: 0, valign: "top",
  });
  s.addNotes("Backup: full cross-folder similarity retrieval results and the retrieval protocol.");
}

// ---- B3 preprocessing sensitivity
{
  const s = backupSlide("BACKUP 3", "Preprocessing sensitivity");
  s.addChart(
    pres.ChartType.bar,
    [{ name: "Mean LOFO F1", labels: ["0.10 s", "0.15 s", "0.20 s", "0.25 s ✓", "0.50 s"], values: [0.655, 0.767, 0.802, 0.872, 0.994] }],
    {
      x: M - 0.1, y: 1.7, w: 6.6, h: 3.3,
      barDir: "col", barGapWidthPct: 55,
      chartColors: [ICE, ICE, ICE, TEAL, CORAL],
      varyColors: true, showLegend: false,
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000",
      dataLabelFontFace: SANS, dataLabelFontSize: 10, dataLabelColor: NAVY,
      showTitle: true, title: "Mean LOFO F1 by analysis-window duration",
      titleFontFace: SANS, titleFontSize: 12, titleColor: NAVY,
      valAxisMinVal: 0.6, valAxisMaxVal: 1.05,
      valAxisLabelFontFace: SANS, valAxisLabelFontSize: 10, valAxisLabelColor: SLATE,
      catAxisLabelFontFace: SANS, catAxisLabelFontSize: 11, catAxisLabelColor: NAVY,
      valGridLine: { color: "EDF1F7", size: 1 }, catGridLine: { style: "none" },
      valAxisLineShow: false, catAxisLineColor: BORDER,
    }
  );
  s.addText([
    { text: "Spectrogram resolution", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "1024 / 512 (used): LOFO mean 0.872, worst 0.727\n256 / 128: LOFO mean 0.881, worst 0.714\n1024 / 900: LOFO mean 0.864, worst 0.691", options: { color: SLATE, breakLine: true } },
    { text: "\nMain spectral-statistics settings", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "Periodic Tukey window (α = 0.25), nfft = 1024; 513 frequency bins × 186 time bins per clip; log10(magnitude + 1e-10) applied first. Crop position gave the same pattern.", options: { color: SLATE } },
  ], {
    isTextBox: true, x: 7.4, y: 1.75, w: 5.2, h: 3.2,
    fontFace: SANS, fontSize: 11.5, lineSpacing: 17, margin: 0, valign: "top",
  });
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 5.25, w: W - 2 * M, h: 1.3, rectRadius: 0.06,
    fill: { color: "FDF2EE" }, line: { color: "F5C7B8", width: 1 },
  });
  s.addText("0.50 s scores highest — and is exactly where the padding shortcut is total: all 158 buzz clips padded, all 158 non-buzz clips cropped. 0.25 s was retained as the compromise (127 buzz clips padded, 189 clips cropped). At 0.10 s, random-test F1 was 0.979 but worst-folder F1 collapsed to 0.050.", {
    isTextBox: true, x: M + 0.3, y: 5.25, w: W - 2 * M - 0.6, h: 1.3,
    fontFace: SANS, fontSize: 12.5, color: "9A4A32", lineSpacing: 19, margin: 0, valign: "middle",
  });
  s.addNotes("Backup: clip-duration and spectrogram-resolution sensitivity, and why the higher-scoring 0.50 s window was not used.");
}

// ---- B4 Kenya thresholds
{
  const s = backupSlide("BACKUP 4", "Kenya — thresholds, coverage and timing");
  const head = ["Detector", "≥ 0.50 windows", "≥ 0.80 windows", "≥ 0.95 windows", "Files with ≥ 0.95"];
  const body = [
    ["Baseline", "59,741 (22.11%)", "36,110 (13.37%)", "11,978 (4.43%)", "161"],
    ["Perch v2", "43,130 (15.96%)", "17,692 (6.55%)", "5,774 (2.14%)", "121"],
  ];
  s.addTable(
    [head.map((h) => ({ text: h, options: tblHead }))].concat(
      body.map((r, ri) =>
        r.map((c, ci) => ({
          text: c,
          options: { ...tblOpts, align: ci === 0 ? "left" : "center", bold: ri === 1, fill: { color: ri === 1 ? "E9F3F1" : WHITE } },
        }))
      )
    ),
    { x: M, y: 1.65, w: 10.6, colW: [2.2, 2.3, 2.3, 2.3, 1.5], rowH: 0.42 }
  );
  const blocks = [
    ["Spread across recordings", "At the lower two thresholds Perch windows were spread across more recordings despite being fewer in total — 466 files vs 343 at ≥ 0.50, and 328 vs 254 at ≥ 0.80."],
    ["Temporal pattern (EAT, UTC+3)", "Highest rates at 23:00 EAT — 30.14% / 17.57% / 7.71% at the 0.50, 0.80 and 0.95 thresholds. Highest daily rates on 24 October 2019. Hours without recordings are not treated as zero."],
  ];
  blocks.forEach(([h, b], i) => {
    const x = M + i * 6.2;
    s.addShape(pres.ShapeType.roundRect, {
      x: x, y: 3.35, w: 5.75, h: 1.5, rectRadius: 0.06,
      fill: { color: PALE }, line: { color: BORDER, width: 1 },
    });
    s.addText(h, {
      isTextBox: true, x: x + 0.28, y: 3.5, w: 5.2, h: 0.32,
      fontFace: SANS, fontSize: 13, bold: true, color: NAVY, margin: 0,
    });
    s.addText(b, {
      isTextBox: true, x: x + 0.28, y: 3.84, w: 5.2, h: 0.9,
      fontFace: SANS, fontSize: 11.5, color: SLATE, lineSpacing: 16, margin: 0, valign: "top",
    });
  });
  s.addText([
    { text: "Candidate selection and review   ", options: { bold: true, color: NAVY } },
    { text: "Route 1 — top 50 Perch windows, neighbouring high-scoring windows within 1 s grouped into one event, one representative window kept per event.  Route 2 — eight windows sampled from each of four score bands (0.95–1.00, 0.80–0.95, 0.50–0.80, 0.20–0.50).  De-duplicated to one candidate per one-minute recording: 53 retained plus 16 newly reviewed = 69 candidates from 69 distinct recordings. Each reviewed with its 0.25 s spectrogram, 1.25 s of context, pulse-timing structure and time-expanded audio.", options: { color: SLATE } },
  ], {
    isTextBox: true, x: M, y: 5.1, w: W - 2 * M, h: 1.5,
    fontFace: SANS, fontSize: 12, lineSpacing: 19, margin: 0, valign: "top",
  });
  s.addNotes("Backup: Kenya threshold counts, recording coverage, temporal pattern and the two-route candidate-selection procedure.");
}

// ---- B5 more reviewed candidates + implementation
{
  const s = backupSlide("BACKUP 5", "More reviewed Kenya candidates");
  const imgW = 5.55, imgH = imgW / 2.797;
  [[M, "kenya_B.jpg", "Buzz-like", "score 1.000", TEAL],
   [M + imgW + 0.82, "kenya_D.jpg", "Recording artefact", "score 0.857", SLATE]].forEach(([x, file, lab, sc, col]) => {
    s.addShape(pres.ShapeType.roundRect, {
      x: x - 0.14, y: 1.6, w: imgW + 0.28, h: imgH + 0.7, rectRadius: 0.06,
      fill: { color: PALE }, line: { color: BORDER, width: 1 },
    });
    s.addImage({ path: A(file), x: x, y: 1.72, w: imgW, h: imgH });
    s.addText([
      { text: lab, options: { bold: true, color: col } },
      { text: "   ·   " + sc, options: { color: SLATE } },
    ], { isTextBox: true, x: x, y: 1.8 + imgH, w: imgW, h: 0.34, fontFace: SANS, fontSize: 13, margin: 0, valign: "middle" });
  });
  caption(s, "Each panel: 1.25 s of context; the cyan band is the 0.25 s window scored by the detector.", M, 2.42 + imgH, 11.9, { size: 10.5 });

  const cols = [
    ["Environment", "Python 3.12.13\nSciPy 1.18.0\nscikit-learn 1.9.0\nPerch-Hoplite 1.0.1\nperch_v2_cpu (frozen)"],
    ["Detector", "StandardScaler, training data only\nLogistic regression, L2 penalty\nC = 1.0, solver lbfgs\nclass_weight = balanced\nrandom_state = 42, max_iter = 1000\nDecision threshold 0.5"],
    ["Field scoring", "Every 60 s recording peak-normalised\n0.25 s windows, 0.125 s hop\n479 windows per recording\n564 files → 270,156 windows\nPerch: 384→320 kHz, 80,000 samples\nread as 2.5 s"],
  ];
  cols.forEach(([h, b], i) => {
    const x = M + i * 4.05;
    s.addText(h, {
      isTextBox: true, x: x, y: 4.8, w: 3.75, h: 0.3,
      fontFace: SANS, fontSize: 12, bold: true, color: TEAL, charSpacing: 1.4, margin: 0,
    });
    s.addText(b, {
      isTextBox: true, x: x, y: 5.14, w: 3.75, h: 1.6,
      fontFace: SANS, fontSize: 11, color: SLATE, lineSpacing: 15, margin: 0, valign: "top",
    });
  });
  s.addNotes("Backup: the two remaining reviewed Kenya candidates, plus fixed model settings and Kenya analysis settings for reproducibility.");
}

const OUT = path.join(__dirname, "TAO_XINYI_EDS_presentation_v2.pptx");
pres.writeFile({ fileName: OUT }).then(() => console.log("written:", OUT));
