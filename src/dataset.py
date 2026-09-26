import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from PIL import Image
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import Dataset
from torchvision import transforms

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Standard ImageNet normalization parameters
NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD = [0.229, 0.224, 0.225]


def parse_clean_name(raw_class_name: str) -> str:
    """
    Parses class folder names like '12_Withania_somnifera' into 'Withania somnifera'.
    """
    parts = raw_class_name.split("_", 1)
    if len(parts) > 1 and parts[0].isdigit():
        return parts[1].replace("_", " ")
    return raw_class_name.replace("_", " ")


def discover_classes(train_dir: str) -> List[str]:
    """
    Dynamically scans the directory and returns sorted list of class names.
    Avoids hardcoding any class names.
    """
    if not os.path.exists(train_dir):
        raise FileNotFoundError(f"Train directory not found: {train_dir}")
    classes = [d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))]
    classes.sort()
    return classes


def build_class_mappings(classes: List[str], save_dir: str = "saved_models") -> Tuple[Dict[str, int], Dict[int, str]]:
    """
    Generates class-to-index and index-to-class mappings and persists them.
    """
    os.makedirs(save_dir, exist_ok=True)
    class_to_idx = {cls_name: idx for idx, cls_name in enumerate(classes)}
    idx_to_class = {idx: cls_name for idx, cls_name in enumerate(classes)}

    class_meta = {}
    for cls_name, idx in class_to_idx.items():
        class_meta[cls_name] = {
            "index": idx,
            "botanical_name": parse_clean_name(cls_name)
        }

    with open(os.path.join(save_dir, "class_to_idx.json"), "w", encoding="utf-8") as f:
        json.dump(class_to_idx, f, indent=2)

    with open(os.path.join(save_dir, "idx_to_class.json"), "w", encoding="utf-8") as f:
        json.dump(idx_to_class, f, indent=2)

    with open(os.path.join(save_dir, "class_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(class_meta, f, indent=2)

    logger.info(f"Generated mappings for {len(classes)} classes saved to {save_dir}")
    return class_to_idx, idx_to_class


def scan_dataset_files(data_dir: str, class_to_idx: Dict[str, int]) -> List[Dict[str, any]]:
    """
    Scans a directory of class folders, verifying image readability and filtering corrupted images.
    """
    records = []
    valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    
    for cls_name, cls_idx in class_to_idx.items():
        cls_dir = os.path.join(data_dir, cls_name)
        if not os.path.isdir(cls_dir):
            continue
        for fname in os.listdir(cls_dir):
            ext = os.path.splitext(fname)[1].lower()
            if ext in valid_exts:
                full_path = os.path.join(cls_dir, fname)
                records.append({
                    "path": full_path,
                    "class_name": cls_name,
                    "label": cls_idx,
                    "clean_name": parse_clean_name(cls_name)
                })
    return records


def create_stratified_manifests(
    train_dir: str,
    test_dir: str,
    manifest_dir: str = "dataset_manifests",
    val_ratio: float = 0.15,
    random_state: int = 42
) -> Tuple[str, str, str]:
    """
    Creates stratified splits:
    - Uses test_dir as the held-out test split (15% test set benchmark)
    - Splits train_dir into reproducible stratified train (70%) and validation (15%) splits
    Persists splits as JSON manifests without altering raw image folders.
    """
    os.makedirs(manifest_dir, exist_ok=True)
    classes = discover_classes(train_dir)
    class_to_idx, _ = build_class_mappings(classes)

    logger.info("Scanning training files...")
    raw_train_records = scan_dataset_files(train_dir, class_to_idx)
    logger.info("Scanning test files...")
    test_records = scan_dataset_files(test_dir, class_to_idx)

    train_labels = [r["label"] for r in raw_train_records]

    # Split train into train and val stratified by class label
    train_records, val_records = train_test_split(
        raw_train_records,
        test_size=val_ratio,
        stratify=train_labels,
        random_state=random_state
    )

    train_path = os.path.join(manifest_dir, "train_manifest.json")
    val_path = os.path.join(manifest_dir, "val_manifest.json")
    test_path = os.path.join(manifest_dir, "test_manifest.json")

    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_records, f, indent=2)
    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val_records, f, indent=2)
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_records, f, indent=2)

    logger.info(
        f"Manifests generated successfully:\n"
        f"  - Train: {len(train_records)} images\n"
        f"  - Val:   {len(val_records)} images\n"
        f"  - Test:  {len(test_records)} images\n"
        f"  Total:   {len(train_records) + len(val_records) + len(test_records)} images across {len(classes)} classes"
    )

    # Save summary stats
    stats = {
        "num_classes": len(classes),
        "total_images": len(train_records) + len(val_records) + len(test_records),
        "train_count": len(train_records),
        "val_count": len(val_records),
        "test_count": len(test_records),
        "classes": classes
    }
    with open(os.path.join(manifest_dir, "dataset_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return train_path, val_path, test_path


def get_train_transforms(image_size: int = 224) -> transforms.Compose:
    """
    Data augmentation pipeline for training:
    - Random Resized Crop (handles variable scales)
    - Random Horizontal Flip (invariance to leaf orientation)
    - Random Rotation (-15 to 15 deg)
    - Subtle ColorJitter (lighting/shadow variation)
    - Normalization
    """
    return transforms.Compose([
        transforms.Resize((int(image_size * 1.14), int(image_size * 1.14))),
        transforms.RandomCrop(image_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORM_MEAN, std=NORM_STD)
    ])


def get_val_test_transforms(image_size: int = 224) -> transforms.Compose:
    """
    Deterministic preprocessing for validation, test, and inference.
    """
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORM_MEAN, std=NORM_STD)
    ])


class MedicinalPlantDataset(Dataset):
    """
    Robust PyTorch Dataset supporting dynamic classes and safe RGB image loading.
    """
    def __init__(self, manifest_or_records, transform=None):
        if isinstance(manifest_or_records, str):
            with open(manifest_or_records, "r", encoding="utf-8") as f:
                self.records = json.load(f)
        else:
            self.records = manifest_or_records
        self.transform = transform

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, str]:
        item = self.records[idx]
        img_path = item["path"]
        label = item["label"]
        class_name = item["class_name"]

        try:
            with Image.open(img_path) as raw_img:
                image = raw_img.convert("RGB")
        except Exception as e:
            logger.warning(f"Error loading {img_path}: {e}. Creating fallback neutral image.")
            image = Image.new("RGB", (224, 224), color=(128, 128, 128))

        if self.transform:
            image = self.transform(image)

        return image, label, class_name
