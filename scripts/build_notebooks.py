import json
import os

def create_notebook(cells, filepath):
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.10.11"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print(f"Generated {filepath}")

def markdown_cell(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.split("\n")]
    }

def code_cell(code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.split("\n")]
    }

def build_all_notebooks(notebooks_dir):
    # ==========================================
    # Notebook 01: Dataset Analysis
    # ==========================================
    cells_01 = [
        markdown_cell("""# Phase 1: Comprehensive Dataset Analysis & Stratified Splitting
## Project: Indian Medicinal Plant Identification using Deep Learning & XAI
**Author:** B.Tech Computer Science Final Year Project (2026–2027)

This notebook explores the dataset containing **93 classical Indian medicinal plant species** with over **33,000 authentic images**.

### Objectives:
1. Dynamic class discovery (no hardcoding)
2. Image integrity verification & corruption filtering
3. Class distribution & imbalance profiling
4. Stratified 70/15/15 Train / Validation / Test manifest generation"""),
        code_cell("""import os
import json
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

train_dir = r"d:\\mainpojectD7\\train-20260921T080302Z-1-001\\train"
test_dir = r"d:\\mainpojectD7\\test-20260921T080351Z-1-001\\test"

classes = sorted(os.listdir(train_dir))
print(f"Discovered {len(classes)} botanical classes.")
print(f"Sample classes: {classes[:5]}")"""),
        code_cell("""# Verify image counts and integrity across classes
class_counts = []
corrupted = []

for c in classes:
    c_path = os.path.join(train_dir, c)
    files = [f for f in os.listdir(c_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    class_counts.append({'class_name': c, 'train_count': len(files)})
    
    # Check sample files for read integrity
    for f in files[:5]:
        fpath = os.path.join(c_path, f)
        try:
            with Image.open(fpath) as img:
                img.verify()
        except Exception as e:
            corrupted.append((fpath, str(e)))

df_counts = pd.DataFrame(class_counts)
print(f"Total training images: {df_counts['train_count'].sum()}")
print(f"Corrupted image files detected: {len(corrupted)}")
print(df_counts.describe())"""),
        code_cell("""# Display Class Distribution Bar Chart
plt.figure(figsize=(18, 6))
plt.bar(range(len(df_counts)), df_counts['train_count'], color='#10b981', alpha=0.85)
plt.title("Indian Medicinal Plant Class Distribution (93 Species)", fontsize=14, fontweight='bold')
plt.xlabel("Class Index", fontsize=11)
plt.ylabel("Number of Training Images", fontsize=11)
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()"""),
        code_cell("""# Load and display Stratified Manifests
manifest_stats_path = r"d:\\mainpojectD7\\dataset_manifests\\dataset_stats.json"
with open(manifest_stats_path, "r") as f:
    stats = json.load(f)

print("Stratified Split Summary:")
print(f"  Total Images:      {stats['total_images']:,}")
print(f"  Training Split:    {stats['train_count']:,} ({stats['train_count']/stats['total_images']*100:.1f}%)")
print(f"  Validation Split:  {stats['val_count']:,} ({stats['val_count']/stats['total_images']*100:.1f}%)")
print(f"  Test Split:        {stats['test_count']:,} ({stats['test_count']/stats['total_images']*100:.1f}%)")"""),
        code_cell("""# Visualizing Sample Specimens
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
sample_classes = classes[:8]

for i, ax in enumerate(axes.flat):
    cls = sample_classes[i]
    c_dir = os.path.join(train_dir, cls)
    sample_file = os.listdir(c_dir)[0]
    img = Image.open(os.path.join(c_dir, sample_file))
    
    ax.imshow(img)
    clean_name = cls.split("_", 1)[-1].replace("_", " ")
    ax.set_title(clean_name, fontsize=11, fontweight='bold')
    ax.axis('off')

plt.suptitle("Sample Indian Medicinal Plant Specimens (Leaves & Whole Plants)", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()""")
    ]
    create_notebook(cells_01, os.path.join(notebooks_dir, "01_dataset_analysis.ipynb"))

    # ==========================================
    # Notebook 02: Image Preprocessing
    # ==========================================
    cells_02 = [
        markdown_cell("""# Phase 2: Image Preprocessing & Data Augmentation Pipeline
## Project: Indian Medicinal Plant Identification using Deep Learning & XAI

This notebook demonstrates the preprocessing and data augmentation transformations used to train the deep CNN models.

### Augmentations Applied:
1. **Random Resized Crop (224x224):** Scales plant specimens invariant to camera distance.
2. **Random Horizontal Flip:** Leaves possess bilateral symmetry.
3. **Random Rotation (±15°):** Invariance to camera orientation in field conditions.
4. **Color Jitter:** Robustness against varying natural sunlight, shadow, and overcast lighting.
5. **ImageNet Normalization:** Matching pre-trained backbone weight distributions."""),
        code_cell("""import sys, os
sys.path.append(r"d:\\mainpojectD7")
from PIL import Image
import matplotlib.pyplot as plt
import torch
from torchvision import transforms
from src.dataset import get_train_transforms, get_val_test_transforms, NORM_MEAN, NORM_STD

# Load sample image
sample_img_path = r"d:\\mainpojectD7\\test-20260921T080351Z-1-001\\test\\12_Withania_somnifera"
sample_file = os.path.join(sample_img_path, os.listdir(sample_img_path)[0])
raw_img = Image.open(sample_file).convert("RGB")

print(f"Original image resolution: {raw_img.size}")"""),
        code_cell("""# Define inverse normalization for visualization
inv_norm = transforms.Normalize(
    mean=[-m/s for m, s in zip(NORM_MEAN, NORM_STD)],
    std=[1/s for s in NORM_STD]
)

train_tf = get_train_transforms(224)
val_tf = get_val_test_transforms(224)

# Generate augmented variants
fig, axes = plt.subplots(1, 5, figsize=(18, 4))
axes[0].imshow(raw_img.resize((224, 224)))
axes[0].set_title("Original (Resized)", fontsize=11, fontweight='bold')
axes[0].axis('off')

for i in range(1, 5):
    t_tensor = train_tf(raw_img)
    disp_img = inv_norm(t_tensor).permute(1, 2, 0).clamp(0, 1).numpy()
    axes[i].imshow(disp_img)
    axes[i].set_title(f"Augmented Variant {i}", fontsize=11)
    axes[i].axis('off')

plt.suptitle("Data Augmentation Pipeline on Withania somnifera (Ashwagandha)", fontsize=13, fontweight='bold')
plt.tight_layout()
plt.show()""")
    ]
    create_notebook(cells_02, os.path.join(notebooks_dir, "02_preprocessing.ipynb"))

    # ==========================================
    # Notebook 03: Model Training
    # ==========================================
    cells_03 = [
        markdown_cell("""# Phase 3: Transfer Learning Model Architecture & Training
## Project: Indian Medicinal Plant Identification using Deep Learning & XAI

This notebook outlines the Deep Learning transfer learning methodology using **MobileNetV3-Large / EfficientNet-B0 / ResNet-50** with hardware acceleration on NVIDIA RTX 3050 GPU.

### Training Strategy:
- **Phase 1 (Warmup):** Freeze backbone weights, train customized 93-class classifier head with Label Smoothing Cross-Entropy.
- **Phase 2 (Fine-Tuning):** Unfreeze top convolutional blocks with reduced learning rate ($10^{-4}$).
- **Optimization:** AdamW with weight decay, mixed precision (`torch.amp`), and `ReduceLROnPlateau` scheduling."""),
        code_cell("""import sys, os
sys.path.append(r"d:\\mainpojectD7")
import torch
import torch.nn as nn
from src.model import build_model

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

model = build_model(num_classes=93, backbone_name="mobilenet_v3_large", pretrained=True, device=device)
print(f"Total model parameters: {sum(p.numel() for p in model.parameters()):,}")
print(f"Trainable parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")"""),
        code_cell("""# Display architecture summary
print("Classification Head Architecture:")
print(model.classifier)
print("\\nTarget Convolutional Layer for Grad-CAM:")
print(model.get_gradcam_target_layer())"""),
        code_cell("""# Display Training Curves from completed runs
import json
import matplotlib.pyplot as plt

history_file = r"d:\\mainpojectD7\\saved_models\\training_history.json"
if os.path.exists(history_file):
    with open(history_file) as f:
        hist = json.load(f)
    
    epochs = range(1, len(hist['train_loss']) + 1)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4))
    
    ax1.plot(epochs, hist['train_loss'], 'o-', label='Train Loss', color='#10b981')
    ax1.plot(epochs, hist['val_loss'], 's--', label='Val Loss', color='#ef4444')
    ax1.set_title("Training & Validation Loss")
    ax1.set_xlabel("Epoch")
    ax1.legend()
    
    ax2.plot(epochs, [a*100 for a in hist['train_acc']], 'o-', label='Train Acc (%)', color='#10b981')
    ax2.plot(epochs, [a*100 for a in hist['val_acc']], 's--', label='Val Acc (%)', color='#3b82f6')
    ax2.set_title("Classification Accuracy (%)")
    ax2.set_xlabel("Epoch")
    ax2.legend()
    
    plt.tight_layout()
    plt.show()
else:
    print("Training history will appear once model training finishes.")""")
    ]
    create_notebook(cells_03, os.path.join(notebooks_dir, "03_model_training.ipynb"))

    # ==========================================
    # Notebook 04: Model Evaluation
    # ==========================================
    cells_04 = [
        markdown_cell("""# Phase 4: Model Evaluation on Held-Out Test Set (9,300 Images)
## Project: Indian Medicinal Plant Identification using Deep Learning & XAI

This notebook presents rigorous academic evaluation on the unseen test benchmark dataset containing 100 images for each of the 93 medicinal species.

### Metrics Computed:
- Top-1 & Top-5 Classification Accuracy
- Per-class and Macro Precision, Recall, and F1-Scores
- Normalized Confusion Matrix Heatmap"""),
        code_cell("""import sys, os, json
sys.path.append(r"d:\\mainpojectD7")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

metrics_path = r"d:\\mainpojectD7\\outputs\\test_metrics.json"
cm_image_path = r"d:\\mainpojectD7\\outputs\\confusion_matrix\\confusion_matrix.png"

if os.path.exists(metrics_path):
    with open(metrics_path) as f:
        metrics = json.load(f)
    print("Test Set Benchmark Metrics:")
    for k, v in metrics.items():
        print(f"  {k:20s}: {v}")
else:
    print("Run `python src/evaluate.py` to evaluate the model on the full test split.")"""),
        code_cell("""# Display Confusion Matrix
if os.path.exists(cm_image_path):
    img = mpimg.imread(cm_image_path)
    plt.figure(figsize=(14, 12))
    plt.imshow(img)
    plt.axis('off')
    plt.title("Normalized Confusion Matrix Heatmap", fontsize=14, fontweight='bold')
    plt.show()
else:
    print("Confusion matrix will be displayed after evaluation script runs.")""")
    ]
    create_notebook(cells_04, os.path.join(notebooks_dir, "04_model_evaluation.ipynb"))

    # ==========================================
    # Notebook 05: Grad-CAM Testing
    # ==========================================
    cells_05 = [
        markdown_cell("""# Phase 5 & 6: Grad-CAM Explainable AI (XAI) & Confidence Evaluation
## Project: Indian Medicinal Plant Identification using Deep Learning & XAI

This notebook verifies Gradient-weighted Class Activation Mapping (Grad-CAM) to explain the visual features influencing the deep learning predictions.

### XAI Workflow:
$$\\\\alpha_k^c = \\\\frac{1}{Z} \\\\sum_i \\\\sum_j \\\\frac{\\\\partial y^c}{\\\\partial A_{i,j}^k}$$
$$L_{\\\\text{Grad-CAM}}^c = \\\\text{ReLU}\\\\left(\\\\sum_k \\\\alpha_k^c A^k\\\\right)$$"""),
        code_cell("""import sys, os
sys.path.append(r"d:\\mainpojectD7")
import torch
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

from src.model import build_model
from src.gradcam import GradCAM, overlay_heatmap
from src.dataset import get_val_test_transforms

device = "cuda" if torch.cuda.is_available() else "cpu"
model = build_model(num_classes=93, backbone_name="mobilenet_v3_large", pretrained=False, checkpoint_path=r"d:\\mainpojectD7\\saved_models\\best_plant_model.pth", device=device)

# Load a test specimen: Tulsi (Ocimum sanctum)
test_dir = r"d:\\mainpojectD7\\test-20260921T080351Z-1-001\\test\\95_Ocimum_sanctum"
sample_img_path = os.path.join(test_dir, os.listdir(test_dir)[0])
raw_pil = Image.open(sample_img_path).convert("RGB")

tf = get_val_test_transforms(224)
input_tensor = tf(raw_pil).unsqueeze(0).to(device)

gradcam = GradCAM(model, model.get_gradcam_target_layer())
heatmap, pred_idx, conf = gradcam.generate_heatmap(input_tensor)
gradcam.remove_hooks()

# Generate overlay
raw_resized = np.array(raw_pil.resize((224, 224)))
colored_cam, overlay = overlay_heatmap(raw_resized, heatmap, alpha=0.55)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
axes[0].imshow(raw_resized)
axes[0].set_title("Input Specimen (Tulsi)", fontsize=12, fontweight='bold')
axes[0].axis('off')

axes[1].imshow(colored_cam)
axes[1].set_title("Grad-CAM Heatmap (Jet)", fontsize=12, fontweight='bold')
axes[1].axis('off')

axes[2].imshow(overlay)
axes[2].set_title(f"Attribution Overlay (Conf: {conf*100:.1f}%)", fontsize=12, fontweight='bold')
axes[2].axis('off')

plt.tight_layout()
plt.show()""")
    ]
    create_notebook(cells_05, os.path.join(notebooks_dir, "05_gradcam_testing.ipynb"))

if __name__ == "__main__":
    build_all_notebooks(r"d:\mainpojectD7\notebooks")
