import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.dataset import MedicinalPlantDataset, get_val_test_transforms
from src.model import build_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def plot_confusion_matrix_heatmap(
    cm: np.ndarray,
    class_names: List[str],
    output_path: str,
    top_n: int = 25
):
    """
    Plots high-resolution confusion matrix heatmap.
    For 93 classes, plots a focused high-activity subset or top confused pairs to remain visually interpretable.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.figure(figsize=(16, 14))

    # Normalize confusion matrix
    cm_norm = cm.astype("float") / (cm.sum(axis=1)[:, np.newaxis] + 1e-9)

    # Plot top_n classes for clean academic presentation
    sub_cm = cm_norm[:top_n, :top_n]
    sub_labels = [c.split("_", 1)[-1].replace("_", " ") for c in class_names[:top_n]]

    sns.heatmap(
        sub_cm,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        xticklabels=sub_labels,
        yticklabels=sub_labels,
        cbar=True,
        linewidths=0.5
    )
    plt.title(f"Normalized Confusion Matrix (Top {top_n} Medicinal Species)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Predicted Botanical Class", fontsize=12)
    plt.ylabel("Ground Truth Class", fontsize=12)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Confusion matrix plot saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Medicinal Plant Classifier on Held-out Test Set")
    parser.add_argument("--checkpoint", type=str, default="saved_models/best_plant_model.pth")
    parser.add_argument("--backbone", type=str, default="mobilenet_v3_large")
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--max_test_samples", type=int, default=None, help="Optional sample limit for quick test pass")
    args = parser.parse_args()

    chk_path = os.path.join(PROJECT_ROOT, args.checkpoint)
    test_manifest_path = os.path.join(PROJECT_ROOT, "dataset_manifests", "test_manifest.json")
    idx_to_class_path = os.path.join(PROJECT_ROOT, "saved_models", "idx_to_class.json")

    with open(idx_to_class_path, "r", encoding="utf-8") as f:
        idx_to_class = json.load(f)
    class_names = [idx_to_class[str(i)] for i in range(len(idx_to_class))]

    with open(test_manifest_path, "r", encoding="utf-8") as f:
        test_records = json.load(f)

    if args.max_test_samples:
        test_records = test_records[:args.max_test_samples]
        logger.info(f"Evaluating on subset of {len(test_records)} test samples...")

    test_dataset = MedicinalPlantDataset(test_records, transform=get_val_test_transforms(224))
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=min(4, os.cpu_count() or 1), pin_memory=True)

    # Build and load model
    model = build_model(
        num_classes=len(class_names),
        backbone_name=args.backbone,
        pretrained=False,
        checkpoint_path=chk_path,
        device=args.device
    )
    model.eval()

    all_preds = []
    all_targets = []
    top5_correct = 0
    total = 0

    logger.info("Running evaluation over test dataset...")
    with torch.no_grad():
        for images, labels, _ in test_loader:
            images = images.to(args.device)
            labels = labels.to(args.device)

            outputs = model(images)
            _, preds = torch.max(outputs, 1)

            _, top5_preds = torch.topk(outputs, k=min(5, outputs.size(1)), dim=1)
            top5_correct += torch.sum(top5_preds == labels.unsqueeze(1)).item()

            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(labels.cpu().numpy())
            total += labels.size(0)

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    overall_acc = np.mean(all_preds == all_targets)
    top5_acc = top5_correct / total

    # Precision, Recall, F1
    precision, recall, f1, _ = precision_recall_fscore_support(all_targets, all_preds, average="weighted", zero_division=0)
    macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(all_targets, all_preds, average="macro", zero_division=0)

    logger.info("=" * 60)
    logger.info(f"TEST BENCHMARK RESULTS ({total} images across {len(class_names)} classes):")
    logger.info(f"  Top-1 Accuracy:       {overall_acc * 100:.2f}%")
    logger.info(f"  Top-5 Accuracy:       {top5_acc * 100:.2f}%")
    logger.info(f"  Weighted Precision:   {precision * 100:.2f}%")
    logger.info(f"  Weighted Recall:      {recall * 100:.2f}%")
    logger.info(f"  Weighted F1-Score:    {f1 * 100:.2f}%")
    logger.info(f"  Macro F1-Score:       {macro_f1 * 100:.2f}%")
    logger.info("=" * 60)

    # Per-class classification report
    labels_range = list(range(len(class_names)))
    report_dict = classification_report(all_targets, all_preds, labels=labels_range, target_names=class_names, output_dict=True, zero_division=0)
    cm = confusion_matrix(all_targets, all_preds, labels=labels_range)

    # Save metrics
    outputs_dir = os.path.join(PROJECT_ROOT, "outputs")
    metrics_summary = {
        "num_test_samples": total,
        "num_classes": len(class_names),
        "top1_accuracy": round(float(overall_acc), 4),
        "top5_accuracy": round(float(top5_acc), 4),
        "weighted_precision": round(float(precision), 4),
        "weighted_recall": round(float(recall), 4),
        "weighted_f1": round(float(f1), 4),
        "macro_f1": round(float(macro_f1), 4)
    }

    with open(os.path.join(outputs_dir, "test_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    # Export per-class dataframe
    per_class_df = pd.DataFrame(report_dict).transpose()
    per_class_df.to_csv(os.path.join(outputs_dir, "per_class_metrics.csv"))

    # Plot Confusion Matrix
    cm_path = os.path.join(outputs_dir, "confusion_matrix", "confusion_matrix.png")
    plot_confusion_matrix_heatmap(cm, class_names, cm_path, top_n=25)

    logger.info("Evaluation completed. All metrics saved to outputs/.")


if __name__ == "__main__":
    main()
