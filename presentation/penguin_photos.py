# -*- coding: utf-8 -*-
"""Cut named penguin photographs out of the YOLO validation mosaics and remove the
detector's drawn annotations, so the slides show the archive as photographed.

Two kinds of annotation are painted over: the thin box outline, and the solid
label patch with its white text. The patch is found by eroding the blue mask
until only thick regions survive, then taking each surviving component's
bounding box -- so the box *interior* is never touched.
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def blue_mask(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    return (b > 110) & (b - r > 45) & (b - g > 35)


def _shift_or(m: np.ndarray) -> np.ndarray:
    p = np.pad(m, 1, constant_values=False)
    return p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:] | m


def dilate(m: np.ndarray, k: int) -> np.ndarray:
    for _ in range(k):
        m = _shift_or(m)
    return m


def erode(m: np.ndarray, k: int) -> np.ndarray:
    return ~dilate(~m, k)


def component_boxes(m: np.ndarray, pad: int = 4) -> np.ndarray:
    """Mask covering the bounding box of every connected component of m."""
    out = np.zeros_like(m)
    seen = np.zeros_like(m)
    ys, xs = np.nonzero(m)
    h, w = m.shape
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        stack, pix = [(y0, x0)], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            pix.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        py = [p[0] for p in pix]
        px = [p[1] for p in pix]
        out[max(0, min(py) - pad):max(py) + 1 + pad,
            max(0, min(px) - pad):max(px) + 1 + pad] = True
    return out


def _sweep(vals: np.ndarray, bad: np.ndarray, axis: int):
    """Nearest valid value and its distance along one axis, both directions."""
    n = vals.shape[axis]
    val = np.moveaxis(vals.copy(), axis, 0)
    dist = np.moveaxis(np.where(bad, 1e6, 0.0).copy(), axis, 0)
    for forward in (True, False):
        rng = range(1, n) if forward else range(n - 2, -1, -1)
        step = -1 if forward else 1
        for i in rng:
            j = i + step
            better = dist[j] + 1 < dist[i]
            dist[i] = np.where(better, dist[j] + 1, dist[i])
            val[i] = np.where(better[..., None], val[j], val[i])
    return np.moveaxis(val, 0, axis), np.moveaxis(dist, 0, axis)


def inpaint(rgb: np.ndarray, mask: np.ndarray, seed: int = 0) -> np.ndarray:
    """Distance-weighted blend of the nearest valid pixel in each of four
    directions: exact for thin lines, a plausible soft fill for the label patch."""
    img = rgb.astype(np.float64)
    acc = np.zeros_like(img)
    wsum = np.zeros(img.shape[:2])
    for axis in (0, 1):
        v, d = _sweep(img, mask, axis)
        w = 1.0 / np.maximum(d, 0.5) ** 2
        acc += v * w[..., None]
        wsum += w
    out = img.copy()
    filled = acc / np.maximum(wsum, 1e-9)[..., None]
    out[mask] = filled[mask]
    rng = np.random.default_rng(seed)          # grain, so a fill is not a plastic blob
    noise = rng.normal(0, 2.5, size=out.shape)
    out[mask] += noise[mask]
    return np.clip(out, 0, 255).astype(np.uint8)


def component_rects(m: np.ndarray, pad: int = 4):
    """Bounding rectangles of every connected component of m."""
    rects = []
    seen = np.zeros_like(m)
    h, w = m.shape
    for y0, x0 in zip(*np.nonzero(m)):
        if seen[y0, x0]:
            continue
        stack, pix = [(y0, x0)], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            pix.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        py = [p[0] for p in pix]
        px = [p[1] for p in pix]
        rects.append((max(0, min(py) - pad), min(h, max(py) + 1 + pad),
                      max(0, min(px) - pad), min(w, max(px) + 1 + pad)))
    return rects


def mirror_fill(img: np.ndarray, rects, mask: np.ndarray) -> np.ndarray:
    """Fill each label rectangle by mirroring the strip of pixels next to it.

    A diffusion fill smears across the chest/background boundary the label often
    straddles; a mirrored strip keeps real texture and a continuous seam.
    """
    out = img.copy()
    H = img.shape[0]
    for y0, y1, x0, x1 in rects:
        h = y1 - y0
        below, above = y1 + h, y0 - h
        if below <= H and not mask[y1:below, x0:x1].any():
            src = img[y1:below, x0:x1][::-1]
        elif above >= 0 and not mask[above:y0, x0:x1].any():
            src = img[above:y0, x0:x1][::-1]
        else:
            continue
        ramp = np.linspace(0, 1, h)[:, None, None]      # feather the seam
        base = out[y0:y1, x0:x1].astype(np.float64)
        out[y0:y1, x0:x1] = (src * (0.82 + 0.18 * ramp) + base * (0.18 - 0.18 * ramp))
    return out


def clean(tile: Image.Image, seed: int = 0) -> Image.Image:
    rgb = np.array(tile.convert("RGB"))
    blue = blue_mask(rgb)
    solid = erode(blue, 3)                      # thin outlines vanish; the patch survives
    mask = dilate(blue, 2)
    rects = []
    if solid.any():
        rects = component_rects(dilate(solid, 2), pad=4)
        mask |= component_boxes(dilate(solid, 2), pad=4)
    out = inpaint(rgb, mask, seed).astype(np.float64)
    if rects:
        out = mirror_fill(out, rects, dilate(blue, 2))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# --------------------------------------------------------------- photo library

from pathlib import Path

EXP = Path(__file__).resolve().parent.parent / "runs/detect/runs/belly_detector/exp1"
CAPTION_H = 46          # the filename band YOLO draws at the top of every tile

# Only the *validation* mosaics are used. One val tile is one photograph of one
# named bird, so the drawn filename identifies it. The train mosaics apply mosaic
# augmentation -- four different birds are stitched into a single labelled tile --
# so a photograph taken from there cannot be attributed to the bird in its label.
# That rules out Gonzo, who appears only in train batches.
BIRDS = {
    "gopher":  ("val_batch1_labels.jpg", 0, 0),
    "olive":   ("val_batch1_labels.jpg", 0, 1),
    "tiger":   ("val_batch1_labels.jpg", 0, 2),
    "niknak":  ("val_batch1_labels.jpg", 0, 3),
    "ping":    ("val_batch1_labels.jpg", 1, 0),
    "beau":    ("val_batch1_labels.jpg", 1, 1),
    "tang":    ("val_batch1_labels.jpg", 1, 2),
    "ronnie":  ("val_batch1_labels.jpg", 1, 3),
    "kermit":  ("val_batch1_labels.jpg", 2, 1),
    "mcvitie": ("val_batch1_labels.jpg", 2, 2),
    "robin":   ("val_batch1_labels.jpg", 2, 3),
    "phineas": ("val_batch1_labels.jpg", 3, 1),
    "nicki":   ("val_batch1_labels.jpg", 3, 2),
    "chompy":  ("val_batch1_labels.jpg", 3, 3),
    "medici":  ("val_batch2_labels.jpg", 0, 0),
    "cooper":  ("val_batch2_labels.jpg", 0, 1),
    "jaz":     ("val_batch2_labels.jpg", 1, 1),
    "ray":     ("val_batch2_labels.jpg", 1, 2),
    "lenny":   ("val_batch2_labels.jpg", 2, 3),
    "pong":    ("val_batch2_labels.jpg", 3, 2),
    "lizzie":  ("val_batch0_labels.jpg", 0, 1),
    "spider":  ("val_batch0_labels.jpg", 1, 2),
    "marley":  ("val_batch0_labels.jpg", 3, 3),
}


def _tile(mosaic: str, r: int, c: int) -> Image.Image:
    im = Image.open(EXP / mosaic).convert("RGB")
    tw, th = im.width // 4, im.height // 4
    return im.crop((c * tw, r * th, (c + 1) * tw, (r + 1) * th))


def _trim(img: Image.Image) -> Image.Image:
    """Drop the caption band, then eat inward from each edge while that edge is
    flat letterbox padding -- edges only, so uniform sky inside a photo survives."""
    a = np.array(img)[CAPTION_H:]

    def flat(line: np.ndarray) -> bool:
        return bool(line.reshape(-1, 3).std(0).max() < 6)

    t, b, l, r = 0, a.shape[0], 0, a.shape[1]
    while b - t > 40 and flat(a[t, l:r]):
        t += 1
    while b - t > 40 and flat(a[b - 1, l:r]):
        b -= 1
    while r - l > 40 and flat(a[t:b, l]):
        l += 1
    while r - l > 40 and flat(a[t:b, r - 1]):
        r -= 1
    return Image.fromarray(a[t:b, l:r])


def build_library(out: Path) -> dict:
    out.mkdir(exist_ok=True, parents=True)
    lib = {}
    for i, (name, (mosaic, r, c)) in enumerate(BIRDS.items()):
        img = clean(_trim(_tile(mosaic, r, c)), seed=i)
        img.save(out / f"{name}.jpg", quality=95)
        lib[name] = img
    return lib


def crop_ratio(img: Image.Image, ratio: float, cy: float = 0.46) -> Image.Image:
    """Largest crop of the given width:height ratio, centred horizontally and at
    the fraction cy down the frame (the chest, for a standing bird)."""
    w, h = img.size
    cw, ch = (w, w / ratio) if w / ratio <= h else (h * ratio, h)
    x = (w - cw) / 2
    y = min(max(cy * h - ch / 2, 0), h - ch)
    return img.crop((int(x), int(y), int(x + cw), int(y + ch)))


def closeup(img: Image.Image, frac: float = 0.6, cx: float = 0.5, cy: float = 0.55,
            ratio: float = 1.0) -> Image.Image:
    """A tighter crop, sized as a fraction of the frame and placed by (cx, cy)."""
    w, h = img.size
    ch = frac * h
    cw = ch * ratio
    if cw > w:
        cw, ch = w, w / ratio
    x = min(max(cx * w - cw / 2, 0), w - cw)
    y = min(max(cy * h - ch / 2, 0), h - ch)
    return img.crop((int(x), int(y), int(x + cw), int(y + ch)))
