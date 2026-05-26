"""
Quick evaluation script for a saved best_model.pt checkpoint.
Usage:
  python eval_checkpoint.py \
    --checkpoint runs/exp2_belly_resnet18/best_model.pt \
    --data-dir penguins_dataset_split_belly
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import ImageFile
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


ImageFile.LOAD_TRUNCATED_IMAGES = True


def build_transforms(img_size: int):
    return transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])


def build_model(num_classes: int) -> nn.Module:
    weights_enum = getattr(models, "ResNet18_Weights", None)
    if weights_enum is not None:
        model = models.resnet18(weights=None)
    else:
        model = models.resnet18(pretrained=False)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def evaluate(model, dataloader, device):
    model.eval()
    correct = 0
    total = 0
    all_true, all_pred, all_conf = [], [], []

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            outputs = model(inputs)
            probs = torch.softmax(outputs, dim=1)
            confs, preds = probs.max(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
            all_true.extend(labels.cpu().tolist())
            all_pred.extend(preds.cpu().tolist())
            all_conf.extend(confs.cpu().tolist())

    return correct / max(total, 1), all_true, all_pred, all_conf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--img-size", type=int, default=224)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    class_names = checkpoint["class_names"]
    num_classes = len(class_names)
    print(f"Loaded checkpoint: epoch {checkpoint['epoch']}, val_acc {checkpoint['val_accuracy']:.4f}")
    print(f"Classes: {num_classes}")

    tfm = build_transforms(args.img_size)
    test_dataset = datasets.ImageFolder(args.data_dir / "test", transform=tfm)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)

    model = build_model(num_classes).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])

    acc, y_true, y_pred, conf = evaluate(model, test_loader, device)
    print(f"\nTest accuracy: {acc:.4f}  ({acc*100:.1f}%)")
    print(f"Test samples:  {len(y_true)}")

    out_dir = args.checkpoint.parent
    metrics = {
        "best_epoch": checkpoint["epoch"],
        "best_val_accuracy": checkpoint["val_accuracy"],
        "test_accuracy": acc,
        "test_samples": len(y_true),
    }
    with (out_dir / "final_metrics.json").open("w") as f:
        json.dump(metrics, f, indent=2)

    with (out_dir / "test_predictions.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image_path", "true_name", "pred_name", "confidence", "correct"])
        for sample, ti, pi, sc in zip(test_dataset.samples, y_true, y_pred, conf):
            writer.writerow([sample[0], class_names[ti], class_names[pi], f"{sc:.4f}", int(ti == pi)])

    num_classes = len(class_names)
    confusion = np.zeros((num_classes, num_classes), dtype=int)
    for ti, pi in zip(y_true, y_pred):
        confusion[ti, pi] += 1

    with (out_dir / "confusion_matrix.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["true/pred", *class_names])
        for idx, name in enumerate(class_names):
            writer.writerow([name, *confusion[idx].tolist()])

    with (out_dir / "per_class_test_metrics.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["class_name", "support", "correct", "accuracy"])
        for idx, name in enumerate(class_names):
            support = int(confusion[idx].sum())
            correct = int(confusion[idx, idx])
            writer.writerow([name, support, correct, f"{correct/support:.4f}" if support else "0.0000"])

    print(f"Results saved to: {out_dir}")


if __name__ == "__main__":
    main()
