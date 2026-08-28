// Custom, native-pptx graphics (editable shapes, not images).
const L = require("./lib.js");
const { C, F, W, H, M } = L;

// ---------------------------------------------------------------------------
// The inference path a photograph takes. Vertical chevron flow with two
// off-ramps on the right (the two ways the system refuses).
// ---------------------------------------------------------------------------
function pipeline(slide, { x, y, w, stepH = 0.62, gap = 0.2 }) {
  const steps = [
    { t: "Photograph", s: "one uncropped image", kind: "in" },
    { t: "ResNet18 embedding", s: "ArcFace-trained · 512-d · L2-normalised", kind: "box" },
    { t: "Search 81 enrolled identities", s: "FAISS · cosine vs class prototypes", kind: "box" },
    { t: "Open-set threshold  0.938", s: "accept · or refuse", kind: "gate" },
    { t: "Ranked shortlist for a keeper", s: "identity + alternatives, human confirms", kind: "out" },
  ];
  const bw = w * 0.62;
  let yy = y;
  steps.forEach((st, i) => {
    const isEnd = st.kind === "in" || st.kind === "out";
    const fill = st.kind === "gate" ? C.orange : isEnd ? C.navy : C.blue;
    slide.addShape("roundRect", {
      x, y: yy, w: bw, h: stepH,
      fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.06,
    });
    slide.addText(st.t, {
      x: x + 0.18, y: yy + 0.06, w: bw - 0.36, h: 0.3,
      fontFace: F.body, fontSize: 13.5, bold: true, color: C.white,
      isTextBox: true, margin: 0, valign: "middle",
    });
    slide.addText(st.s, {
      x: x + 0.18, y: yy + 0.33, w: bw - 0.36, h: 0.24,
      fontFace: F.body, fontSize: 10, color: "DDE6F2",
      isTextBox: true, margin: 0, valign: "middle",
    });
    if (i < steps.length - 1) {
      slide.addShape("downArrow", {
        x: x + bw / 2 - 0.075, y: yy + stepH + 0.02, w: 0.15, h: gap - 0.04,
        fill: { color: C.rule }, line: { color: C.rule, width: 0 },
      });
    }
    yy += stepH + gap;
  });

  // the two refusal off-ramps
  const ramps = [
    { at: 3, label: "best score below 0.938", out: "“not a bird I know”" },
    { at: 2, label: "no confident match", out: "shortlist, not a name" },
  ];
  const r = ramps[0];
  const ry = y + r.at * (stepH + gap);
  slide.addShape("rightArrow", {
    x: x + bw + 0.05, y: ry + stepH / 2 - 0.09, w: 0.42, h: 0.18,
    fill: { color: C.orange }, line: { color: C.orange, width: 0 },
  });
  slide.addText(r.out, {
    x: x + bw + 0.52, y: ry + 0.02, w: w - bw - 0.52, h: 0.3,
    fontFace: F.body, fontSize: 12, bold: true, color: C.orange,
    isTextBox: true, margin: 0, valign: "middle",
  });
  slide.addText(r.label, {
    x: x + bw + 0.52, y: ry + 0.3, w: w - bw - 0.52, h: 0.26,
    fontFace: F.body, fontSize: 10, color: C.muted,
    isTextBox: true, margin: 0, valign: "middle",
  });
  return yy;
}

// ---------------------------------------------------------------------------
// The descending staircase: each step is a more honest question, each answer
// is lower. Steps descend left to right.
// ---------------------------------------------------------------------------
function staircase(slide, { x, y, w, h, steps }) {
  const n = steps.length;
  const gap = 0.14;
  const cw = (w - gap * (n - 1)) / n;
  const maxV = Math.max(...steps.map(s => s.v));
  const barMax = h - 1.55;
  steps.forEach((s, i) => {
    const bx = x + i * (cw + gap);
    const bh = Math.max(0.22, (s.v / maxV) * barMax);
    const by = y + barMax - bh;
    const col = s.color || (i === 0 ? C.faint : i === n - 1 ? C.orange : C.blue);
    slide.addShape("rect", {
      x: bx, y: by, w: cw, h: bh,
      fill: { color: col }, line: { color: col, width: 0 },
    });
    slide.addText(s.v.toFixed(3), {
      x: bx, y: by - 0.46, w: cw, h: 0.42,
      fontFace: F.head, fontSize: 24, bold: true, color: col, align: "center",
      isTextBox: true, margin: 0, valign: "bottom",
    });
    slide.addText(s.q, {
      x: bx, y: y + barMax + 0.1, w: cw, h: 0.62,
      fontFace: F.body, fontSize: 12, bold: true, color: C.ink, align: "center",
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 0.95,
    });
    slide.addText(s.note, {
      x: bx, y: y + barMax + 0.74, w: cw, h: 0.7,
      fontFace: F.body, fontSize: 9.5, color: C.muted, align: "center",
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 0.95,
    });
  });
}

// ---------------------------------------------------------------------------
// The loss x augmentation 2x2, drawn as a real 2x2 so the interaction reads.
// ---------------------------------------------------------------------------
function grid2x2(slide, { x, y, w, h, cells, rowLabels, colLabels }) {
  const lw = 1.28, lh = 0.42;                 // label gutters
  const cw = (w - lw) / 2, ch = (h - lh) / 2;
  colLabels.forEach((t, j) => {
    slide.addText(t, {
      x: x + lw + j * cw, y, w: cw, h: lh,
      fontFace: F.body, fontSize: 12.5, bold: true, color: C.ink, align: "center",
      isTextBox: true, margin: 0, valign: "middle",
    });
  });
  rowLabels.forEach((t, i) => {
    slide.addText(t, {
      x, y: y + lh + i * ch, w: lw - 0.12, h: ch,
      fontFace: F.body, fontSize: 12.5, bold: true, color: C.ink, align: "right",
      isTextBox: true, margin: 0, valign: "middle",
    });
  });
  cells.forEach(c => {
    const cx = x + lw + c.j * cw, cy = y + lh + c.i * ch;
    const best = !!c.best;
    slide.addShape("roundRect", {
      x: cx + 0.05, y: cy + 0.05, w: cw - 0.1, h: ch - 0.1,
      fill: { color: best ? C.blue : C.panel },
      line: { color: best ? C.blue : C.rule, width: best ? 0 : 1 },
      rectRadius: 0.05,
    });
    slide.addText(c.v, {
      x: cx + 0.05, y: cy + 0.12, w: cw - 0.1, h: ch * 0.6,
      fontFace: F.head, fontSize: 34, bold: true,
      color: best ? C.white : C.ink, align: "center",
      isTextBox: true, margin: 0, valign: "middle",
    });
    if (c.tag) {
      slide.addText(c.tag, {
        x: cx + 0.05, y: cy + ch * 0.66, w: cw - 0.1, h: 0.3,
        fontFace: F.body, fontSize: 10.5,
        color: best ? "D6E4F7" : C.muted, align: "center",
        isTextBox: true, margin: 0, valign: "top",
      });
    }
  });
}

// ---------------------------------------------------------------------------
// Nicki vs Gonzo: same photo count, different number of capture sessions.
// The session-dot motif carries the whole argument.
// ---------------------------------------------------------------------------
function sessionCompare(slide, { x, y, w, birds, rowH = 1.7 }) {
  birds.forEach((b, i) => {
    const yy = y + i * rowH;
    // row 1: name on the left, accuracy on the right
    slide.addText(b.name, {
      x, y: yy, w: w - 1.7, h: 0.46,
      fontFace: F.head, fontSize: 21, bold: true, color: C.navy,
      isTextBox: true, margin: 0, valign: "middle",
    });
    slide.addText(b.acc, {
      x: x + w - 1.7, y: yy - 0.04, w: 1.7, h: 0.54,
      fontFace: F.head, fontSize: 32, bold: true, color: b.color, align: "right",
      isTextBox: true, margin: 0, valign: "middle",
    });
    // row 2: the two counts, side by side, so the contrast is one line
    slide.addText([
      { text: `${b.photos}`, options: { bold: true, color: C.ink } },
      { text: " photographs   ·   ", options: { color: C.muted } },
      { text: `${b.sessions}`, options: { bold: true, color: b.color } },
      { text: ` capture session${b.sessions > 1 ? "s" : ""}`, options: { color: C.muted } },
    ], {
      x, y: yy + 0.48, w, h: 0.3,
      fontFace: F.body, fontSize: 12.5,
      isTextBox: true, margin: 0, valign: "middle",
    });
    // row 3: one dot per capture session - the motif carries the argument
    L.dots(slide, { x, y: yy + 0.9, n: b.sessions, color: b.color, d: 0.17, gap: 0.1 });
  });
}

module.exports = { pipeline, staircase, grid2x2, sessionCompare };
