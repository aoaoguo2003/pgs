# -*- coding: utf-8 -*-
"""
Regenerate the image assets the slide deck embeds, from files already in this repo.

Everything written here is derived; nothing is hand-edited. Run this before
`node build_deck.js`.

  python presentation/prepare_assets.py
  cd presentation && node build_deck.js

Four kinds of asset:

  fig/*.jpg     the analysis figures with their small-print footnote block cropped
                off. The footnotes are unreadable when projected, so the slide
                writes its own caption at a legible size; figure 12 also loses its
                title, because the slide title already says it.
  bands.jpg     the colony's flipper-band chart, cropped to the name and band
                columns. The ARKS and microchip columns are deliberately cropped
                away -- they are institutional record numbers with no place on a
                projected slide.
  pg/*.jpg      named photographs of individual colony members, recovered from
                the YOLO mosaics with the detector's boxes and labels painted out
                (penguin_photos.py). The boxes come from a preliminary chest
                detector that is not part of the identification path, so removing
                them makes the slides show the archive as photographed.
  title_bg.jpg, spot*.jpg, strip*.jpg
                crops of those photographs, framed for the slide that uses them:
                the hero on the title slide, three ventral close-ups, and the
                seven-bird strip that shows the archive's range of conditions.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

import penguin_photos as pp

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
FIGS = ROOT / "figures"

# y at which each figure's footnote block starts; everything below is dropped.
# Figure 12 is also cropped from the top to remove its own title.
FIGURE_CROPS = {
    "06_leakage_random_vs_session.png": (0, 1258),
    "10_open_set_dir_far.png": (0, 1228),
    "12_loss_x_augmentation.png": (100, 1290),
    "13_colony_sessions_per_individual.png": (0, 1085),
    "14_photos_vs_sessions.png": (0, 1300),
}


def main() -> None:
    figdir = OUT / "fig"
    figdir.mkdir(exist_ok=True)

    for name, (top, bottom) in FIGURE_CROPS.items():
        src = Image.open(FIGS / name).convert("RGB")
        src.crop((0, top, src.width, bottom)).save(
            figdir / name.replace(".png", ".jpg"), quality=94
        )

    # this one carries no footnote, so it goes across whole
    Image.open(FIGS / "05_dataset_distribution.png").convert("RGB").save(
        figdir / "05_dataset_distribution.jpg", quality=94
    )

    bands = Image.open(ROOT / "Color_Bands1.jpg").crop((270, 180, 1615, 2380))
    bands.thumbnail((1000, 1640), Image.LANCZOS)
    bands.save(OUT / "bands.jpg", quality=92)

    lib = pp.build_library(OUT / "pg")
    title_background(lib["ping"])

    # slide 2 -- the marking the bird already carries
    for i, (name, cy) in enumerate([("ronnie", 0.52), ("phineas", 0.52), ("gopher", 0.52)]):
        pp.closeup(lib[name], frac=0.55, cy=cy).resize((520, 520), Image.LANCZOS) \
          .save(OUT / f"spot{i + 1}.jpg", quality=94)

    # slide 3 -- the archive's range of birds, poses, light and backgrounds
    strip = ["tiger", "lizzie", "mcvitie", "jaz", "kermit", "chompy", "pong"]
    for i, name in enumerate(strip):
        pp.crop_ratio(lib[name], 0.78, cy=0.46).resize((410, 526), Image.LANCZOS) \
          .save(OUT / f"strip{i + 1}.jpg", quality=94)

    print(f"assets written to {OUT}")


def title_background(hero: Image.Image) -> None:
    """Navy field with one bird bled off the right edge, dissolving into it."""
    W, H = 2560, 1440
    navy = (16, 44, 74)
    bg = Image.new("RGB", (W, H), navy)

    pw = int(W * 0.46)
    photo = pp.crop_ratio(hero, pw / H, cy=0.46).resize((pw, H), Image.LANCZOS)
    # the source tile is only ~320px wide and carries the scars of the removed
    # annotation, so soften it: at this size it should read as atmosphere
    photo = photo.filter(ImageFilter.GaussianBlur(2.4))
    photo = ImageEnhance.Brightness(ImageEnhance.Color(photo).enhance(0.80)).enhance(0.95)
    photo = Image.blend(photo, Image.new("RGB", photo.size, navy), 0.20)

    fade = int(pw * 0.42)                      # dissolve the photo's left edge
    alpha = Image.new("L", (pw, H), 255)
    ramp = alpha.load()
    for x in range(fade):
        v = int(255 * (x / fade) ** 1.5)
        for y in range(H):
            ramp[x, y] = v
    bg.paste(photo, (W - pw, 0), alpha)
    bg.save(OUT / "title_bg.jpg", quality=91)


if __name__ == "__main__":
    main()
