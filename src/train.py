import os
import sys
import json
import time
import argparse
import logging
from typing import Dict, Any, List

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.amp import autocast, GradScaler

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.dataset import MedicinalPlantDataset, get_train_transforms, get_val_test_transforms
from src.model import build_model, MedicinalPlantClassifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    scaler: GradScaler,
    device: str
) -> Dict[str, float]:
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    t_start = time.time()

    for step, (images, labels, _) in enumerate(loader):
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        optimizer.zero_grad()

        # Mixed precision forward pass
        with autocast(device_type="cuda" if "cuda" in device else "cpu"):
            outputs = model(images)
            loss = criterion(outputs, labels)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data).item()
        total += labels.size(0)

        if (step + 1) % 25 == 0 or (step + 1) == len(loader):
            speed = total / (time.time() - t_start)
            logger.info(f"  Step [{step+1}/{len(loader)}] - Batch Loss: {loss.item():.4f} | Running Acc: {correct/total*100:.1f}% ({speed:.1f} img/s)")

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return {"loss": epoch_loss, "accuracy": epoch_acc}


@torch.no_grad()
def evaluate_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: str
) -> Dict[str, float]:
    model.eval()
    running_loss = 0.0
    correct = 0
    top5_correct = 0
    total = 0

    for images, labels, _ in loader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        with autocast(device_type="cuda" if "cuda" in device else "cpu"):
            outputs = model(images)
            loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data).item()

        # Top-5 accuracy
        _, top5_preds = torch.topk(outputs, k=min(5, outputs.size(1)), dim=1)
        top5_correct += torch.sum(top5_preds == labels.unsqueeze(1)).item()

        total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    epoch_top5 = top5_correct / total
    return {"loss": epoch_loss, "accuracy": epoch_acc, "top5_accuracy": epoch_top5}


def plot_training_curves(history: Dict[str, List[float]], output_path: str):
    """Generates dual-panel training & validation loss and accuracy curves."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    epochs = range(1, len(history["train_loss"]) + 1)

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Loss plot
    ax1.plot(epochs, history["train_loss"], "o-", color="#10b981", label="Training Loss", linewidth=2)
    ax1.plot(epochs, history["val_loss"], "s--", color="#ef4444", label="Validation Loss", linewidth=2)
    ax1.set_title("Cross-Entropy Loss vs Epochs", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Epoch", fontsize=11)
    ax1.set_ylabel("Loss", fontsize=11)
    ax1.legend(frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Accuracy plot
    ax2.plot(epochs, [a * 100 for a in history["train_acc"]], "o-", color="#10b981", label="Train Accuracy (%)", linewidth=2)
    ax2.plot(epochs, [a * 100 for a in history["val_acc"]], "s--", color="#3b82f6", label="Val Accuracy (%)", linewidth=2)
    ax2.set_title("Classification Accuracy vs Epochs", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Epoch", fontsize=11)
    ax2.set_ylabel("Accuracy (%)", fontsize=11)
    ax2.legend(frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Training curves saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Train Medicinal Plant Identification Deep Learning Model")
    parser.add_argument("--backbone", type=str, default="mobilenet_v3_large", choices=["mobilenet_v3_large", "efficientnet_b0", "resnet50"])
    parser.add_argument("--epochs", type=int, default=10, help="Total training epochs")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size for training")
    parser.add_argument("--lr", type=float, default=1e-3, help="Initial learning rate")
    parser.add_argument("--unfreeze_at_epoch", type=int, default=3, help="Epoch to unfreeze backbone for fine-tuning")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--subsample_ratio", type=float, default=1.0, help="Optional dataset fraction for quick experiments")
    args = parser.parse_args()

    device = args.device
    logger.info(f"Starting training on device: {device} | Backbone: {args.backbone} | Batch size: {args.batch_size}")

    manifest_dir = os.path.join(PROJECT_ROOT, "dataset_manifests")
    train_manifest = os.path.join(manifest_dir, "train_manifest.json")
    val_manifest = os.path.join(manifest_dir, "val_manifest.json")

    # Load manifests
    with open(train_manifest, "r", encoding="utf-8") as f:
        train_records = json.load(f)
    with open(val_manifest, "r", encoding="utf-8") as f:
        val_records = json.load(f)

    if args.subsample_ratio < 1.0:
        n_train = int(len(train_records) * args.subsample_ratio)
        n_val = int(len(val_records) * args.subsample_ratio)
        train_records = train_records[:n_train]
        val_records = val_records[:n_val]
        logger.info(f"Subsampled datasets: Train={len(train_records)}, Val={len(val_records)}")

    train_dataset = MedicinalPlantDataset(train_records, transform=get_train_transforms(224))
    val_dataset = MedicinalPlantDataset(val_records, transform=get_val_test_transforms(224))

    num_workers = min(4, os.cpu_count() or 1)
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)

    # Initialize model
    model = build_model(
        num_classes=93,
        backbone_name=args.backbone,
        pretrained=True,
        device=device
    )

    # Phase 1: Freeze backbone, train classification head
    model.freeze_backbone()
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optimizer = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2, verbose=True)
    scaler = GradScaler(enabled=("cuda" in device))

    saved_models_dir = os.path.join(PROJECT_ROOT, "saved_models")
    best_model_path = os.path.join(saved_models_dir, "best_plant_model.pth")
    outputs_dir = os.path.join(PROJECT_ROOT, "outputs", "training_plots")

    best_val_acc = 0.0
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": [], "val_top5_acc": []}

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        # Unfreeze backbone for fine-tuning
        if epoch == args.unfreeze_at_epoch:
            logger.info("Unfreezing upper backbone layers for fine-tuning stage...")
            model.unfreeze_backbone(unfreeze_last_n_blocks=3)
            # Re-initialize optimizer with lower learning rate for fine-tuning
            optimizer = optim.AdamW([
                {"params": model.features.parameters(), "lr": args.lr * 0.1},
                {"params": model.classifier.parameters(), "lr": args.lr}
            ], weight_decay=1e-4)

        train_metrics = train_one_epoch(model, train_loader, criterion, optimizer, scaler, device)
        val_metrics = evaluate_epoch(model, val_loader, criterion, device)

        scheduler.step(val_metrics["accuracy"])
        elapsed = time.time() - t0

        history["train_loss"].append(train_metrics["loss"])
        history["train_acc"].append(train_metrics["accuracy"])
        history["val_loss"].append(val_metrics["loss"])
        history["val_acc"].append(val_metrics["accuracy"])
        history["val_top5_acc"].append(val_metrics["top5_accuracy"])

        logger.info(
            f"Epoch [{epoch}/{args.epochs}] ({elapsed:.1f}s) - "
            f"Train Loss: {train_metrics['loss']:.4f} | Train Acc: {train_metrics['accuracy']*100:.2f}% | "
            f"Val Loss: {val_metrics['loss']:.4f} | Val Acc: {val_metrics['accuracy']*100:.2f}% | "
            f"Val Top-5: {val_metrics['top5_accuracy']*100:.2f}%"
        )

        # Checkpoint best model
        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            checkpoint = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_accuracy": best_val_acc,
                "backbone": args.backbone,
                "num_classes": 93
            }
            torch.save(checkpoint, best_model_path)
            logger.info(f" Saved new best model checkpoint (Val Acc: {best_val_acc*100:.2f}%) to {best_model_path}")

    # Save history and curves
    with open(os.path.join(saved_models_dir, "training_history.json"), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    plot_training_curves(history, os.path.join(outputs_dir, "training_curves.png"))
    logger.info("Training pipeline completed successfully.")


if __name__ == "__main__":
    main()
