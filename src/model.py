import os
import torch
import torch.nn as nn
from torchvision import models
from torchvision.models import (
    MobileNet_V3_Large_Weights,
    EfficientNet_B0_Weights,
    ResNet50_Weights
)
from typing import Tuple, Optional


class MedicinalPlantClassifier(nn.Module):
    """
    Modular Transfer-Learning CNN for Indian Medicinal Plant Identification.
    Supports MobileNetV3-Large, EfficientNet-B0, and ResNet-50 backbones.
    """
    def __init__(
        self,
        num_classes: int = 93,
        backbone_name: str = "mobilenet_v3_large",
        pretrained: bool = True,
        dropout_rate: float = 0.3
    ):
        super().__init__()
        self.num_classes = num_classes
        self.backbone_name = backbone_name.lower()
        self.dropout_rate = dropout_rate

        if self.backbone_name == "mobilenet_v3_large":
            weights = MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
            base_model = models.mobilenet_v3_large(weights=weights)
            self.features = base_model.features
            in_features = base_model.classifier[0].in_features
            self.pooling = nn.AdaptiveAvgPool2d(1)
            self.classifier = nn.Sequential(
                nn.Flatten(),
                nn.Linear(in_features, 512),
                nn.BatchNorm1d(512),
                nn.Hardswish(inplace=True),
                nn.Dropout(p=dropout_rate),
                nn.Linear(512, num_classes)
            )
            self.target_layer = self.features[-1]

        elif self.backbone_name == "efficientnet_b0":
            weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
            base_model = models.efficientnet_b0(weights=weights)
            self.features = base_model.features
            in_features = base_model.classifier[1].in_features
            self.pooling = nn.AdaptiveAvgPool2d(1)
            self.classifier = nn.Sequential(
                nn.Flatten(),
                nn.Linear(in_features, 512),
                nn.BatchNorm1d(512),
                nn.SiLU(inplace=True),
                nn.Dropout(p=dropout_rate),
                nn.Linear(512, num_classes)
            )
            self.target_layer = self.features[-1]

        elif self.backbone_name == "resnet50":
            weights = ResNet50_Weights.DEFAULT if pretrained else None
            base_model = models.resnet50(weights=weights)
            # Remove fc and avgpool
            self.features = nn.Sequential(
                base_model.conv1,
                base_model.bn1,
                base_model.relu,
                base_model.maxpool,
                base_model.layer1,
                base_model.layer2,
                base_model.layer3,
                base_model.layer4
            )
            in_features = base_model.fc.in_features
            self.pooling = nn.AdaptiveAvgPool2d(1)
            self.classifier = nn.Sequential(
                nn.Flatten(),
                nn.Linear(in_features, 512),
                nn.BatchNorm1d(512),
                nn.ReLU(inplace=True),
                nn.Dropout(p=dropout_rate),
                nn.Linear(512, num_classes)
            )
            self.target_layer = base_model.layer4[-1]

        else:
            raise ValueError(f"Unsupported backbone: {backbone_name}. Choose from mobilenet_v3_large, efficientnet_b0, resnet50.")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.pooling(x)
        logits = self.classifier(x)
        return logits

    def freeze_backbone(self):
        """Freezes all feature extractor backbone parameters."""
        for param in self.features.parameters():
            param.requires_grad = False

    def unfreeze_backbone(self, unfreeze_last_n_blocks: Optional[int] = None):
        """
        Unfreezes backbone parameters. If unfreeze_last_n_blocks is specified,
        only the top layers are unfrozen for fine-tuning.
        """
        if unfreeze_last_n_blocks is None:
            for param in self.features.parameters():
                param.requires_grad = True
        else:
            for param in self.features.parameters():
                param.requires_grad = False
            # Unfreeze the last n children in features
            children = list(self.features.children())
            for child in children[-unfreeze_last_n_blocks:]:
                for param in child.parameters():
                    param.requires_grad = True

    def get_gradcam_target_layer(self) -> nn.Module:
        """Returns the final convolutional layer for Grad-CAM hook registration."""
        return self.target_layer


def build_model(
    num_classes: int = 93,
    backbone_name: str = "mobilenet_v3_large",
    pretrained: bool = True,
    checkpoint_path: Optional[str] = None,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
) -> MedicinalPlantClassifier:
    """
    Model factory helper function.
    """
    model = MedicinalPlantClassifier(
        num_classes=num_classes,
        backbone_name=backbone_name,
        pretrained=pretrained
    )

    if checkpoint_path and os.path.exists(checkpoint_path):
        state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
        # Handle state_dict wrapped in a checkpoint dictionary
        if "model_state_dict" in state_dict:
            model.load_state_dict(state_dict["model_state_dict"])
        else:
            model.load_state_dict(state_dict)

    model.to(device)
    return model
