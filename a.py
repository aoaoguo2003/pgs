from pathlib import Path
import shutil
import random
import pandas as pd

# =========================
# 1. Edit these paths
# =========================
SOURCE_DIR = Path("penguins_data_over15")
OUTPUT_DIR = Path("penguins_dataset_split")

# =========================
# 2. Split ratios
# =========================
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

RANDOM_SEED = 42

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

random.seed(RANDOM_SEED)

# If the output folder already exists, remove it first to avoid duplicate copies
if OUTPUT_DIR.exists():
    shutil.rmtree(OUTPUT_DIR)

for split in ["train", "val", "test"]:
    (OUTPUT_DIR / split).mkdir(parents=True, exist_ok=True)

summary = []

# =========================
# 3. Split each penguin (class) separately
# =========================
for penguin_folder in SOURCE_DIR.iterdir():
    if not penguin_folder.is_dir():
        continue

    penguin_name = penguin_folder.name

    image_files = [
        file for file in penguin_folder.iterdir()
        if file.suffix.lower() in IMAGE_EXTENSIONS
    ]

    image_files = sorted(image_files)
    random.shuffle(image_files)

    n = len(image_files)

    train_end = int(n * TRAIN_RATIO)
    val_end = int(n * (TRAIN_RATIO + VAL_RATIO))

    train_files = image_files[:train_end]
    val_files = image_files[train_end:val_end]
    test_files = image_files[val_end:]

    split_dict = {
        "train": train_files,
        "val": val_files,
        "test": test_files
    }

    for split_name, files in split_dict.items():
        target_class_dir = OUTPUT_DIR / split_name / penguin_name
        target_class_dir.mkdir(parents=True, exist_ok=True)

        for img_path in files:
            shutil.copy2(img_path, target_class_dir / img_path.name)

    summary.append({
        "penguin_name": penguin_name,
        "total_images": n,
        "train_images": len(train_files),
        "val_images": len(val_files),
        "test_images": len(test_files)
    })

# =========================
# 4. Save the split-summary table
# =========================
df = pd.DataFrame(summary)
df = df.sort_values(by="total_images", ascending=False)

summary_path = OUTPUT_DIR / "split_summary.csv"
df.to_csv(summary_path, index=False)

print("Dataset split completed.")
print(f"Output folder: {OUTPUT_DIR}")
print(f"Summary saved to: {summary_path}")
print()
print(df)