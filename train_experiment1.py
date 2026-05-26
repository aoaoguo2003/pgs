"""
Experiment 1: 44-class Humboldt penguin individual recognition baseline.

Expected dataset layout:

penguins_dataset_split/
  train/<penguin_name>/*.jpg
  val/<penguin_name>/*.jpg
  test/<penguin_name>/*.jpg

The script trains a transfer-learning baseline with ResNet-18 by default.
It handles class imbalance with both:
  1. WeightedRandomSampler for the training DataLoader.
  2. Class-weighted CrossEntropyLoss.

Example:
  python train_experiment1.py --data-dir penguins_dataset_split --epochs 30
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import ImageFile
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, models, transforms


ImageFile.LOAD_TRUNCATED_IMAGES = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train Experiment 1 44-class penguin ID baseline."
    )
    parser.add_argument("--data-dir", type=Path, default=Path("penguins_dataset_split"))
    parser.add_argument("--output-dir", type=Path, default=Path("runs") / "exp1_baseline")
    parser.add_argument("--model", choices=["resnet18", "resnet50"], default="resnet18")
    parser.add_argument("--img-size", type=int, default=224)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--no-pretrained", action="store_true")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = True


def build_transforms(img_size: int) -> dict[str, transforms.Compose]:
    imagenet_mean = [0.485, 0.456, 0.406]
    imagenet_std = [0.229, 0.224, 0.225]

    train_tfms = transforms.Compose(
        [
            transforms.Resize((img_size, img_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
            transforms.ColorJitter(
                brightness=0.15,
                contrast=0.15,
                saturation=0.10,
                hue=0.02,
            ),
            transforms.ToTensor(),
            transforms.Normalize(imagenet_mean, imagenet_std),
        ]
    )

    eval_tfms = transforms.Compose(
        [
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(imagenet_mean, imagenet_std),
        ]
    )

    return {"train": train_tfms, "val": eval_tfms, "test": eval_tfms}


def load_datasets(
    data_dir: Path, img_size: int
) -> tuple[dict[str, datasets.ImageFolder], list[str]]:
    tfms = build_transforms(img_size)
    split_dirs = {split: data_dir / split for split in ["train", "val", "test"]}

    missing = [str(path) for path in split_dirs.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing split folders: {missing}")

    image_datasets = {
        split: datasets.ImageFolder(split_dirs[split], transform=tfms[split])
        for split in ["train", "val", "test"]
    }

    class_names = image_datasets["train"].classes
    if len(class_names) != 44:
        print(
            f"Warning: expected 44 classes for Experiment 1, found {len(class_names)}."
        )

    for split in ["val", "test"]:
        if image_datasets[split].classes != class_names:
            raise ValueError(
                f"Class folders in {split} do not match train class folders."
            )

    return image_datasets, class_names


def compute_class_weights(train_dataset: datasets.ImageFolder) -> torch.Tensor:
    targets = torch.tensor(train_dataset.targets, dtype=torch.long)
    class_counts = torch.bincount(targets, minlength=len(train_dataset.classes)).float()
    class_weights = class_counts.sum() / (len(class_counts) * class_counts)
    return class_weights


def build_dataloaders(
    image_datasets: dict[str, datasets.ImageFolder],
    batch_size: int,
    num_workers: int,
) -> tuple[dict[str, DataLoader], torch.Tensor]:
    train_dataset = image_datasets["train"]
    class_weights = compute_class_weights(train_dataset)

    sample_weights = [class_weights[target].item() for target in train_dataset.targets]
    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True,
    )

    dataloaders = {
        "train": DataLoader(
            train_dataset,
            batch_size=batch_size,
            sampler=sampler,
            num_workers=num_workers,
            pin_memory=True,
        ),
        "val": DataLoader(
            image_datasets["val"],
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True,
        ),
        "test": DataLoader(
            image_datasets["test"],
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True,
        ),
    }
    return dataloaders, class_weights


def build_model(model_name: str, num_classes: int, pretrained: bool) -> nn.Module:
    def make_resnet(constructor: Any, weights_enum_name: str) -> nn.Module:
        weights_enum = getattr(models, weights_enum_name, None)
        if weights_enum is not None:
            weights = weights_enum.DEFAULT if pretrained else None
            return constructor(weights=weights)

        # Older torchvision versions use pretrained=True/False instead of weights=...
        return constructor(pretrained=pretrained)

    if model_name == "resnet18":
        model = make_resnet(models.resnet18, "ResNet18_Weights")
    elif model_name == "resnet50":
        model = make_resnet(models.resnet50, "ResNet50_Weights")
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)
    return model


def run_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: optim.Optimizer | None = None,
) -> dict[str, float]:
    is_train = optimizer is not None
    model.train(is_train)

    running_loss = 0.0
    running_correct = 0
    total = 0

    for inputs, labels in dataloader:
        inputs = inputs.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        if is_train:
            optimizer.zero_grad(set_to_none=True)

        with torch.set_grad_enabled(is_train):
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            preds = outputs.argmax(dim=1)

            if is_train:
                loss.backward()
                optimizer.step()

        batch_size = labels.size(0)
        running_loss += loss.item() * batch_size
        running_correct += (preds == labels).sum().item()
        total += batch_size

    return {
        "loss": running_loss / max(total, 1),
        "accuracy": running_correct / max(total, 1),
    }


def evaluate_with_predictions(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[dict[str, float], list[int], list[int], list[float]]:
    model.eval()
    running_loss = 0.0
    running_correct = 0
    total = 0
    all_true: list[int] = []
    all_pred: list[int] = []
    all_conf: list[float] = []

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            probs = torch.softmax(outputs, dim=1)
            confs, preds = probs.max(dim=1)

            batch_size = labels.size(0)
            running_loss += loss.item() * batch_size
            running_correct += (preds == labels).sum().item()
            total += batch_size

            all_true.extend(labels.cpu().tolist())
            all_pred.extend(preds.cpu().tolist())
            all_conf.extend(confs.cpu().tolist())

    metrics = {
        "loss": running_loss / max(total, 1),
        "accuracy": running_correct / max(total, 1),
    }
    return metrics, all_true, all_pred, all_conf


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_history(path: Path, history: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)


def save_predictions(
    path: Path,
    dataset: datasets.ImageFolder,
    class_names: list[str],
    y_true: list[int],
    y_pred: list[int],
    conf: list[float],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "image_path",
                "true_index",
                "true_name",
                "pred_index",
                "pred_name",
                "confidence",
                "correct",
            ]
        )
        for sample, true_idx, pred_idx, score in zip(
            dataset.samples, y_true, y_pred, conf
        ):
            writer.writerow(
                [
                    sample[0],
                    true_idx,
                    class_names[true_idx],
                    pred_idx,
                    class_names[pred_idx],
                    f"{score:.6f}",
                    int(true_idx == pred_idx),
                ]
            )


def save_evaluation_tables(
    output_dir: Path,
    class_names: list[str],
    y_true: list[int],
    y_pred: list[int],
) -> None:
    num_classes = len(class_names)
    confusion = np.zeros((num_classes, num_classes), dtype=int)

    for true_idx, pred_idx in zip(y_true, y_pred):
        confusion[true_idx, pred_idx] += 1

    confusion_path = output_dir / "confusion_matrix.csv"
    with confusion_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["true/pred", *class_names])
        for idx, class_name in enumerate(class_names):
            writer.writerow([class_name, *confusion[idx].tolist()])

    per_class_path = output_dir / "per_class_test_metrics.csv"
    with per_class_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "class_index",
                "class_name",
                "support",
                "correct",
                "accuracy",
            ]
        )
        for idx, class_name in enumerate(class_names):
            support = int(confusion[idx].sum())
            correct = int(confusion[idx, idx])
            accuracy = correct / support if support else 0.0
            writer.writerow(
                [
                    idx,
                    class_name,
                    support,
                    correct,
                    f"{accuracy:.6f}",
                ]
            )


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    image_datasets, class_names = load_datasets(args.data_dir, args.img_size)
    dataloaders, class_weights = build_dataloaders(
        image_datasets,
        args.batch_size,
        args.num_workers,
    )

    save_json(args.output_dir / "class_to_idx.json", image_datasets["train"].class_to_idx)
    save_json(
        args.output_dir / "class_counts_train.json",
        {
            class_name: image_datasets["train"].targets.count(idx)
            for idx, class_name in enumerate(class_names)
        },
    )

    model = build_model(
        model_name=args.model,
        num_classes=len(class_names),
        pretrained=not args.no_pretrained,
    ).to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    optimizer = optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=3,
    )

    save_json(
        args.output_dir / "config.json",
        {
            **vars(args),
            "data_dir": str(args.data_dir),
            "output_dir": str(args.output_dir),
            "device": str(device),
            "num_classes": len(class_names),
            "classes": class_names,
            "imbalance_handling": [
                "WeightedRandomSampler",
                "Class-weighted CrossEntropyLoss",
            ],
        },
    )

    best_val_acc = 0.0
    best_epoch = 0
    epochs_without_improvement = 0
    history: list[dict[str, Any]] = []
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        train_metrics = run_one_epoch(
            model,
            dataloaders["train"],
            criterion,
            device,
            optimizer=optimizer,
        )
        val_metrics = run_one_epoch(model, dataloaders["val"], criterion, device)
        scheduler.step(val_metrics["accuracy"])

        row = {
            "epoch": epoch,
            "train_loss": train_metrics["loss"],
            "train_accuracy": train_metrics["accuracy"],
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
            "lr": optimizer.param_groups[0]["lr"],
        }
        history.append(row)

        print(
            f"Epoch {epoch:03d}/{args.epochs} | "
            f"train loss {train_metrics['loss']:.4f}, "
            f"train acc {train_metrics['accuracy']:.4f} | "
            f"val loss {val_metrics['loss']:.4f}, "
            f"val acc {val_metrics['accuracy']:.4f}"
        )

        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            best_epoch = epoch
            epochs_without_improvement = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "class_to_idx": image_datasets["train"].class_to_idx,
                    "class_names": class_names,
                    "val_accuracy": best_val_acc,
                    "args": vars(args),
                },
                args.output_dir / "best_model.pt",
            )
        else:
            epochs_without_improvement += 1

        save_history(args.output_dir / "history.csv", history)

        if epochs_without_improvement >= args.patience:
            print(f"Early stopping at epoch {epoch}. Best epoch: {best_epoch}.")
            break

    checkpoint = torch.load(args.output_dir / "best_model.pt", map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])

    test_metrics, y_true, y_pred, conf = evaluate_with_predictions(
        model,
        dataloaders["test"],
        criterion,
        device,
    )

    elapsed_minutes = (time.time() - start_time) / 60
    final_metrics = {
        "best_epoch": best_epoch,
        "best_val_accuracy": best_val_acc,
        "test_loss": test_metrics["loss"],
        "test_accuracy": test_metrics["accuracy"],
        "elapsed_minutes": elapsed_minutes,
    }
    save_json(args.output_dir / "final_metrics.json", final_metrics)
    save_predictions(
        args.output_dir / "test_predictions.csv",
        image_datasets["test"],
        class_names,
        y_true,
        y_pred,
        conf,
    )
    save_evaluation_tables(args.output_dir, class_names, y_true, y_pred)

    print("\nTraining complete.")
    print(f"Best val accuracy: {best_val_acc:.4f} at epoch {best_epoch}")
    print(f"Test accuracy: {test_metrics['accuracy']:.4f}")
    print(f"Outputs saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
