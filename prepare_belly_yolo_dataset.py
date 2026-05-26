"""
Prepares the YOLO annotation dataset from the raw penguins_data folder.

Randomly samples images into train/val splits for annotation.
Run this ONCE before annotating:
  python prepare_belly_yolo_dataset.py
"""

import random
import shutil
from pathlib import Path

SRC       = Path("penguins_data")
DST       = Path("belly_yolo_dataset")
N_TRAIN   = 300
N_VAL     = 100
SEED      = 42
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def prepare() -> None:
    if not SRC.exists():
        raise FileNotFoundError(f"Source directory not found: {SRC}")

    all_images = sorted(
        p for p in SRC.rglob("*")
        if p.suffix.lower() in IMAGE_EXTS
    )
    print(f"Found {len(all_images)} images in {SRC}")

    random.seed(SEED)
    random.shuffle(all_images)

    train_imgs = all_images[:N_TRAIN]
    val_imgs   = all_images[N_TRAIN: N_TRAIN + N_VAL]

    for split, imgs in [("train", train_imgs), ("val", val_imgs)]:
        img_out = DST / "images" / split
        lbl_out = DST / "labels" / split
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        copied = 0
        for img_path in imgs:
            penguin = img_path.parent.name
            new_name = f"{penguin}__{img_path.stem}.jpg"
            dst_img = img_out / new_name
            if not dst_img.exists():
                shutil.copy2(img_path, dst_img)
            copied += 1

        print(f"  {split:5s}: {copied} images → {img_out}")

    # data.yaml
    yaml_path = DST / "data.yaml"
    yaml_path.write_text(
        f"path: {DST.resolve().as_posix()}\n"
        "train: images/train\n"
        "val:   images/val\n"
        "nc: 1\n"
        "names: ['belly']\n",
        encoding="utf-8",
    )
    print(f"  data.yaml → {yaml_path}")
    print(f"\n完成。共准备 {N_TRAIN} 张训练图 + {N_VAL} 张验证图。")
    print("现在运行标注工具：")
    print("  python annotate_belly.py        # 标注 train")
    print("  python annotate_belly.py val    # 标注 val")


if __name__ == "__main__":
    prepare()
