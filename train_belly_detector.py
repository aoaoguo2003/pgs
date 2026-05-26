"""
Train a YOLOv8 belly-region detector.

Prerequisites:
  pip install ultralytics
  (complete annotation with LabelImg first)

Usage:
  python train_belly_detector.py

The best model is saved to:
  runs/belly_detector/exp1/weights/best.pt
"""

from pathlib import Path
from ultralytics import YOLO


DATA_YAML = Path("belly_yolo_dataset/data.yaml")
MODEL_SIZE = "yolov8s.pt"   # s = small: good accuracy, fast on RTX 4060
PROJECT    = "runs/belly_detector"
NAME       = "exp1"


def train() -> None:
    if not DATA_YAML.exists():
        raise FileNotFoundError(
            f"{DATA_YAML} not found. Run prepare_belly_yolo_dataset.py first."
        )

    model = YOLO(MODEL_SIZE)

    results = model.train(
        data=str(DATA_YAML),
        epochs=100,
        imgsz=640,
        batch=16,
        device=0,            # GPU (RTX 4060)
        project=PROJECT,
        name=NAME,
        exist_ok=True,
        patience=20,         # early stopping

        # Augmentation — conservative for portrait-style penguin photos.
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.4,
        degrees=10.0,        # small rotation is realistic
        fliplr=0.5,          # horizontal flip is fine
        flipud=0.0,          # penguins are always upright — don't flip vertically
        scale=0.3,
        translate=0.1,
        mosaic=0.5,
    )

    best = Path(results.save_dir) / "weights" / "best.pt"
    print(f"\nTraining complete.")
    print(f"Best model: {best}")
    print(f"\nTo crop the full dataset, run:")
    print(f"  python crop_penguin_belly_yolo.py --model {best} "
          f"--input-dir penguins_dataset_split_body "
          f"--output-dir penguins_dataset_split_belly --overwrite")


if __name__ == "__main__":
    train()
