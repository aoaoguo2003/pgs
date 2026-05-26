"""
Step 2 (YOLO version): crop the belly spot region from penguin body crops
using a trained YOLOv8 detector.

Replaces crop_penguin_belly.py once you have a trained model.

Example single image:
  python crop_penguin_belly_yolo.py \
    --model runs/belly_detector/exp1/weights/best.pt \
    --image penguins_dataset_split_body/train/Medici/DSC_2480.jpeg \
    --output belly_preview.jpg --save-debug

Example full dataset:
  python crop_penguin_belly_yolo.py \
    --model runs/belly_detector/exp1/weights/best.pt \
    --input-dir penguins_dataset_split_body \
    --output-dir penguins_dataset_split_belly \
    --overwrite
"""

from __future__ import annotations

import argparse
import csv
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFile
from ultralytics import YOLO


ImageFile.LOAD_TRUNCATED_IMAGES = True
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass
class BellyCropResult:
    crop_box: tuple[int, int, int, int]
    detected_box: tuple[int, int, int, int] | None
    confidence: float
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crop penguin belly using a trained YOLOv8 detector."
    )
    parser.add_argument("--model", type=Path, required=True,
                        help="Path to trained YOLOv8 weights (best.pt)")
    parser.add_argument("--image", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--input-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path,
                        default=Path("penguins_dataset_split_belly"))
    parser.add_argument("--conf", type=float, default=0.25,
                        help="Minimum detection confidence (default 0.25)")
    parser.add_argument("--padding", type=float, default=0.05,
                        help="Fractional padding around the detected box (default 0.05)")
    parser.add_argument("--jpeg-quality", type=int, default=95)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--save-debug", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def clamp_box(
    box: tuple[int, int, int, int], width: int, height: int
) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    left   = max(0, min(width - 1, left))
    top    = max(0, min(height - 1, top))
    right  = max(left + 1, min(width, right))
    bottom = max(top + 1, min(height, bottom))
    return left, top, right, bottom


def expand_box(
    box: tuple[int, int, int, int], width: int, height: int, padding: float
) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    bw = right - left
    bh = bottom - top
    px = int(round(bw * padding))
    py = int(round(bh * padding))
    return clamp_box((left - px, top - py, right + px, bottom + py), width, height)


def detect_belly(
    image: Image.Image,
    model: YOLO,
    conf: float,
    padding: float,
) -> BellyCropResult:
    width, height = image.size
    rgb = np.array(image.convert("RGB"))

    results = model(rgb, conf=conf, verbose=False)

    if not results or len(results[0].boxes) == 0:
        # No detection: fall back to the central region of the image.
        cx, cy = width // 2, height // 2
        fallback = clamp_box(
            (int(width * 0.10), int(height * 0.25),
             int(width * 0.90), int(height * 0.80)),
            width, height,
        )
        return BellyCropResult(
            crop_box=fallback,
            detected_box=None,
            confidence=0.0,
            status="no_detection_fallback",
        )

    boxes = results[0].boxes
    best_idx = int(boxes.conf.argmax())
    x1, y1, x2, y2 = boxes.xyxy[best_idx].tolist()
    conf_score = float(boxes.conf[best_idx])

    detected = clamp_box((int(x1), int(y1), int(x2), int(y2)), width, height)
    crop_box = expand_box(detected, width, height, padding)

    return BellyCropResult(
        crop_box=crop_box,
        detected_box=detected,
        confidence=conf_score,
        status=f"yolo(conf={conf_score:.2f})",
    )


def draw_debug(
    image: Image.Image, result: BellyCropResult, output_path: Path
) -> None:
    debug = image.convert("RGB").copy()
    draw = ImageDraw.Draw(debug)
    if result.detected_box is not None:
        draw.rectangle(result.detected_box, outline="cyan", width=5)
    draw.rectangle(result.crop_box, outline="red", width=6)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    debug.save(output_path, quality=92)


def iter_images(input_dir: Path) -> list[Path]:
    return sorted(
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def process_one_image(
    source_path: Path,
    output_path: Path,
    model: YOLO,
    conf: float,
    padding: float,
    jpeg_quality: int,
    save_debug: bool,
) -> BellyCropResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source_path) as image:
        result = detect_belly(image, model, conf, padding)
        crop = image.convert("RGB").crop(result.crop_box)
        crop.save(output_path, quality=jpeg_quality)
        if save_debug:
            debug_path = output_path.with_name(output_path.stem + "_debug.jpg")
            draw_debug(image, result, debug_path)
    return result


def process_dataset(args: argparse.Namespace, model: YOLO) -> None:
    if args.input_dir is None:
        raise ValueError("Use --input-dir for dataset mode.")
    if not args.input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {args.input_dir}")
    if args.output_dir.exists():
        if not args.overwrite:
            raise FileExistsError(
                f"{args.output_dir} already exists. Use --overwrite to replace."
            )
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    image_paths = iter_images(args.input_dir)
    if args.limit is not None:
        image_paths = image_paths[: args.limit]

    metadata_path = args.output_dir / "belly_crop_metadata.csv"
    no_detect_count = 0

    with metadata_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "source_path", "output_path", "status", "confidence",
            "det_left", "det_top", "det_right", "det_bottom",
            "crop_left", "crop_top", "crop_right", "crop_bottom",
        ])

        for index, source_path in enumerate(image_paths, start=1):
            relative_path = source_path.relative_to(args.input_dir)
            output_path = args.output_dir / relative_path
            try:
                result = process_one_image(
                    source_path, output_path, model,
                    args.conf, args.padding, args.jpeg_quality, args.save_debug,
                )
                det = result.detected_box or ("", "", "", "")
                writer.writerow([
                    str(source_path), str(output_path),
                    result.status, f"{result.confidence:.3f}",
                    *det, *result.crop_box,
                ])
                if result.detected_box is None:
                    no_detect_count += 1
            except Exception as exc:
                writer.writerow([
                    str(source_path), str(output_path),
                    f"error: {exc}", "", "", "", "", "", "", "", "", "",
                ])

            if index % 50 == 0 or index == len(image_paths):
                print(f"Processed {index}/{len(image_paths)} images")

    total = len(image_paths)
    detected = total - no_detect_count
    print(f"\nDone. Detected: {detected}/{total} ({100*detected//total}%)")
    if no_detect_count:
        print(f"  {no_detect_count} images used fallback crop (no detection).")
        print(f"  Check metadata CSV for details: {metadata_path}")
    print(f"Output: {args.output_dir}")


def main() -> None:
    args = parse_args()

    if not args.model.exists():
        raise FileNotFoundError(
            f"Model not found: {args.model}\n"
            "Run train_belly_detector.py first."
        )

    print(f"Loading model: {args.model}")
    model = YOLO(str(args.model))

    if args.image is not None:
        if args.output is None:
            raise ValueError("Use --output with --image.")
        result = process_one_image(
            args.image, args.output, model,
            args.conf, args.padding, args.jpeg_quality, args.save_debug,
        )
        print(f"Saved belly crop to: {args.output}")
        print(f"Status:        {result.status}")
        print(f"Detected box:  {result.detected_box}")
        print(f"Crop box:      {result.crop_box}")
        return

    process_dataset(args, model)


if __name__ == "__main__":
    main()
