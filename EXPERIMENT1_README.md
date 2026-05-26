# Experiment 1: 44-class Penguin Baseline

This experiment trains a 44-class penguin identity classifier using the already split dataset:

```text
penguins_dataset_split/
  train/
  val/
  test/
```

The training script uses:

- `torchvision.datasets.ImageFolder`
- transfer learning with `resnet18` by default
- `WeightedRandomSampler` for imbalanced mini-batches
- class-weighted `CrossEntropyLoss`
- validation-based best checkpoint saving
- final test evaluation and prediction CSV export

## Install PyTorch

For an NVIDIA RTX 4060, install the CUDA build of PyTorch from the official PyTorch selector. A typical command is:

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install numpy pillow
```

If you are using a virtual environment, activate it first.

## Run Training

From `C:\Users\14773\Desktop\pgs`:

```powershell
python train_experiment1.py --data-dir penguins_dataset_split --epochs 30 --batch-size 32
```

Useful alternatives:

```powershell
python train_experiment1.py --model resnet50 --epochs 40 --batch-size 16
python train_experiment1.py --img-size 299 --epochs 30
```

## Outputs

The script saves results under:

```text
runs/exp1_baseline/
```

Important files:

- `best_model.pt`: best validation checkpoint
- `history.csv`: per-epoch train/val loss and accuracy
- `final_metrics.json`: best validation accuracy and final test accuracy
- `test_predictions.csv`: image-level predictions with confidence
- `per_class_test_metrics.csv`: per-penguin test accuracy
- `confusion_matrix.csv`: full test confusion matrix
- `class_to_idx.json`: mapping from penguin name to class index
