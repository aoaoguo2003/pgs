# -*- coding: utf-8 -*-
"""
Regenerate the image assets the slide deck embeds, from files already in this repo.

Everything written here is derived; nothing is hand-edited. Run this before
`node build_deck.js`.

  python presentation/prepare_assets.py
  cd presentation && node build_deck.js

Three kinds of asset:

  fig/*.jpg     the analysis figures with their small-print footnote block cropped
                off. The footnotes are unreadable when projected, so the slide
                writes its own caption at a legible size; figure 12 also loses its
                title, because the slide title already says it.
  bands.jpg     the colony's flipper-band chart, cropped to the name and band
                columns. The ARKS and microchip columns are deliberately cropped
                away -- they are institutional record numbers with no place on a
                projected slide.
  title_bg.jpg  a blurred, darkened montage for the title slide. Blurred hard
                enough to read as texture rather than as a claim about the
                pipeline: the boxes in it come from the preliminary chest
                detector, which is not part of the identification path.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

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

    mosaic = Image.open(
        ROOT / "runs/detect/runs/belly_detector/exp1/val_batch0_labels.jpg"
    ).convert("RGB")
    bg = mosaic.crop((0, 0, 1920, 1080)).resize((2560, 1440), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(5))
    bg = ImageEnhance.Color(bg).enhance(0.35)
    bg = Image.blend(bg, Image.new("RGB", bg.size, (16, 44, 74)), 0.86)
    ImageEnhance.Brightness(bg).enhance(0.94).save(OUT / "title_bg.jpg", quality=90)

    print(f"assets written to {OUT}")


if __name__ == "__main__":
    main()
