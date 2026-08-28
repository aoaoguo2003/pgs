// Design system for the penguin re-ID final presentation.
// Palette is sampled from the project's own matplotlib figures so plots sit
// seamlessly on the slides (bg FCFCFB, series 2A78D6 / EB6834, grid E1E0D9).

const C = {
  bg:      "FCFCFB",   // exact background of every figure in figures/
  navy:    "0E2A47",   // dark slides, titles
  navy2:   "163A5F",   // dark slide gradient-ish second tone (flat blocks only)
  ink:     "24303C",   // body text on light
  muted:   "6E7681",   // captions, secondary
  faint:   "A9AEB5",
  blue:    "2A78D6",   // "the model" / method
  orange:  "EB6834",   // "the honest number" / warning
  panel:   "F1F0EC",   // light panel fill
  rule:    "E1E0D9",   // matches figure gridlines
  white:   "FFFFFF",
  green:   "2F7D4F",
};

const F = { head: "Cambria", body: "Calibri" };

const W = 13.333, H = 7.5;      // LAYOUT_WIDE
const M = 0.62;                 // page margin

function newDeck(pptxgen, meta) {
  const p = new pptxgen();
  p.layout = "LAYOUT_WIDE";
  p.author = meta.author || "";
  p.title = meta.title || "";
  p.subject = meta.subject || "";
  return p;
}

// --- motif: a row of "capture session" dots -------------------------------
function dots(slide, { x, y, n, color = C.blue, d = 0.13, gap = 0.075, max = 24 }) {
  const k = Math.min(n, max);
  for (let i = 0; i < k; i++) {
    slide.addShape("ellipse", {
      x: x + i * (d + gap), y, w: d, h: d,
      fill: { color }, line: { color, width: 0 },
    });
  }
  return x + k * (d + gap);
}

// --- slide chrome ----------------------------------------------------------
function darkSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.navy };
  return s;
}

function lightSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.bg };
  return s;
}

// Assertion title at the top of a content slide. Returns the y where content
// may begin.
function title(slide, text, opts = {}) {
  const size = opts.size || 27;
  const y = opts.y != null ? opts.y : 0.42;
  slide.addText(text, {
    x: M, y, w: W - 2 * M, h: opts.h || 0.72,
    fontFace: F.head, fontSize: size, bold: true, color: opts.color || C.navy,
    align: "left", valign: "top", isTextBox: true, margin: 0,
    lineSpacingMultiple: 0.95,
  });
  return y + (opts.h || 0.72) + (opts.gap != null ? opts.gap : 0.12);
}

// small uppercase kicker above the title
function kicker(slide, text, opts = {}) {
  slide.addText(text.toUpperCase(), {
    x: M, y: opts.y != null ? opts.y : 0.16, w: W - 2 * M, h: 0.24,
    fontFace: F.body, fontSize: 11, bold: true, color: opts.color || C.orange,
    charSpacing: 1.6, isTextBox: true, margin: 0, valign: "middle",
  });
}

// bottom-right slide number + short running foot
function foot(slide, n, label) {
  if (label) {
    slide.addText(label, {
      x: M, y: H - 0.46, w: 8.5, h: 0.28,
      fontFace: F.body, fontSize: 10, color: C.faint, isTextBox: true, margin: 0, valign: "middle",
    });
  }
  slide.addText(String(n), {
    x: W - M - 0.6, y: H - 0.46, w: 0.6, h: 0.28,
    fontFace: F.body, fontSize: 10, color: C.faint, align: "right",
    isTextBox: true, margin: 0, valign: "middle",
  });
}

// --- content blocks --------------------------------------------------------
function bullets(slide, items, { x, y, w, h, size = 15, color = C.ink, space = 9 }) {
  slide.addText(
    items.map((t, i) => ({
      text: t,
      options: { bullet: { code: "2022" }, breakLine: i !== items.length - 1 },
    })),
    {
      x, y, w, h, fontFace: F.body, fontSize: size, color,
      isTextBox: true, margin: 0, valign: "top",
      paraSpaceAfter: space, lineSpacingMultiple: 1.05,
    }
  );
}

// A big number with a label under it. labelH must cover however many lines the
// label wraps to, or the sub-line lands on top of it.
function stat(slide, { x, y, w, value, label, sub, color = C.navy, size = 54,
                       labelSize = 12, labelH = 0.26 }) {
  slide.addText(value, {
    x, y, w, h: size / 58,
    fontFace: F.head, fontSize: size, bold: true, color,
    isTextBox: true, margin: 0, valign: "bottom", align: "left",
  });
  let yy = y + size / 58 + 0.04;
  slide.addText(label, {
    x, y: yy, w, h: labelH,
    fontFace: F.body, fontSize: labelSize, bold: true, color: C.ink,
    isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.0,
  });
  if (sub) {
    slide.addText(sub, {
      x, y: yy + labelH, w, h: 0.62,
      fontFace: F.body, fontSize: 10.5, color: C.muted,
      isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 0.95,
    });
  }
}

// A soft card. No edge stripes, no accent bars - fill + optional shadow only.
function card(slide, { x, y, w, h, fill = C.panel, shadow = false, radius = 0.06 }) {
  const opt = {
    x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 },
    rectRadius: radius,
  };
  if (shadow) opt.shadow = { type: "outer", color: "9AA0A6", blur: 8, offset: 1.5, angle: 90, opacity: 0.18 };
  slide.addShape("roundRect", opt);
}

function caption(slide, text, { x, y, w, size = 10.5, color = C.muted, align = "left" }) {
  slide.addText(text, {
    x, y, w, h: 0.5,
    fontFace: F.body, fontSize: size, color, align,
    isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 0.95,
  });
}

// Intrinsic pixel size of a PNG or JPEG, read from the file. Hard-coding these
// silently mis-scales every figure the moment prepare_assets.py changes a crop.
const fs = require("fs");
function imageSize(file) {
  const b = fs.readFileSync(file);
  if (b.length > 24 && b.toString("ascii", 1, 4) === "PNG") {
    return [b.readUInt32BE(16), b.readUInt32BE(20)];
  }
  if (b[0] === 0xff && b[1] === 0xd8) {                 // JPEG: walk to a SOFn
    let i = 2;
    while (i < b.length) {
      if (b[i] !== 0xff) { i++; continue; }
      const marker = b[i + 1];
      const len = b.readUInt16BE(i + 2);
      if (marker >= 0xc0 && marker <= 0xcf &&
          ![0xc4, 0xc8, 0xcc].includes(marker)) {
        return [b.readUInt16BE(i + 7), b.readUInt16BE(i + 5)];
      }
      i += 2 + len;
    }
  }
  throw new Error(`cannot read image dimensions: ${file}`);
}

// Fit an image inside a box, centred, preserving aspect ratio.
function fitImage(slide, path, box, dims) {
  const [iw, ih] = dims || imageSize(path);
  const s = Math.min(box.w / iw, box.h / ih);
  const w = iw * s, h = ih * s;
  slide.addImage({
    path,
    x: box.x + (box.w - w) / 2,
    y: box.y + (box.h - h) / 2,
    w, h,
  });
  return { x: box.x + (box.w - w) / 2, y: box.y + (box.h - h) / 2, w, h };
}

module.exports = {
  imageSize,
  C, F, W, H, M,
  newDeck, dots, darkSlide, lightSlide, title, kicker, foot,
  bullets, stat, card, caption, fitImage,
};
