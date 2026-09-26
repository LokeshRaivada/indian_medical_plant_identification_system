import io
import base64
import numpy as np
import cv2
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Dict, Any, Optional


class GradCAM:
    """
    Explainable AI: Gradient-weighted Class Activation Mapping (Grad-CAM)
    computes visual explanations from the final convolutional feature maps.
    """
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None
        self._hooks = []
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        self._hooks.append(self.target_layer.register_forward_hook(forward_hook))
        self._hooks.append(self.target_layer.register_full_backward_hook(backward_hook))

    def remove_hooks(self):
        for hook in self._hooks:
            hook.remove()
        self._hooks.clear()

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None
    ) -> Tuple[np.ndarray, int, float]:
        """
        Generates 2D normalized Grad-CAM heatmap for the given input tensor.
        Returns (heatmap_np, class_idx, confidence_prob).
        """
        self.model.eval()
        input_tensor.requires_grad_(True)

        logits = self.model(input_tensor)
        probabilities = F.softmax(logits, dim=1)

        if target_class is None:
            target_class = torch.argmax(logits, dim=1).item()

        score = logits[0, target_class]
        confidence = probabilities[0, target_class].item()

        self.model.zero_grad()
        score.backward(retain_graph=True)

        # Gradients shape: [1, Channels, H, W]
        # Activations shape: [1, Channels, H, W]
        gradients = self.gradients
        activations = self.activations

        # Global average pooling of gradients over spatial dimensions
        alpha = torch.mean(gradients, dim=(2, 3), keepdim=True)
        weighted_activations = alpha * activations

        # Weighted combination across channels
        cam = torch.sum(weighted_activations, dim=1, keepdim=True)
        # Apply ReLU to retain only features that have a positive influence on the class
        cam = F.relu(cam)

        cam_np = cam.squeeze().cpu().numpy()

        # Normalize to [0, 1]
        cam_min, cam_max = np.min(cam_np), np.max(cam_np)
        if cam_max - cam_min > 1e-8:
            heatmap = (cam_np - cam_min) / (cam_max - cam_min)
        else:
            heatmap = np.zeros_like(cam_np)

        return heatmap, target_class, confidence


def overlay_heatmap(
    original_img_rgb: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.55,
    colormap: int = cv2.COLORMAP_JET
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Overlays normalized Grad-CAM heatmap onto the original RGB image.
    Returns (colored_heatmap_rgb, overlay_rgb).
    """
    h, w = original_img_rgb.shape[:2]
    # Resize heatmap to match image dimensions
    heatmap_resized = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)
    heatmap_uint8 = np.uint8(255 * heatmap_resized)

    # Apply colormap (OpenCV returns BGR)
    colored_bgr = cv2.applyColorMap(heatmap_uint8, colormap)
    colored_rgb = cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2RGB)

    # Blend original and heatmap
    overlay = cv2.addWeighted(original_img_rgb, 1.0 - alpha, colored_rgb, alpha, 0)
    return colored_rgb, overlay


def create_side_by_side_visualization(
    original_rgb: np.ndarray,
    colored_heatmap: np.ndarray,
    overlay_rgb: np.ndarray,
    predicted_label: str,
    confidence: float
) -> np.ndarray:
    """
    Creates an academic-ready side-by-side composite:
    [Original Image] | [Grad-CAM Heatmap] | [Overlay]
    with label header.
    """
    h, w, c = original_rgb.shape
    # Add top banner
    banner_height = 50
    composite_width = w * 3 + 20
    composite = np.zeros((h + banner_height, composite_width, 3), dtype=np.uint8)
    composite[:] = (20, 24, 28)  # sleek dark background

    # Insert images
    composite[banner_height:, 0:w] = original_rgb
    composite[banner_height:, w + 10:w * 2 + 10] = colored_heatmap
    composite[banner_height:, w * 2 + 20:composite_width] = overlay_rgb

    # Draw header text
    title_text = f"Pred: {predicted_label} | Confidence: {confidence * 100:.1f}%"
    cv2.putText(composite, title_text, (15, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (240, 240, 240), 2, cv2.LINE_AA)

    # Sub-labels
    cv2.putText(composite, "Original", (15, banner_height + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(composite, "Grad-CAM Heatmap", (w + 25, banner_height + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(composite, "Overlay", (w * 2 + 35, banner_height + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

    return composite


def ndarray_to_base64(img_array: np.ndarray, format: str = "JPEG") -> str:
    """Encodes numpy RGB image to Base64 data URL string."""
    pil_img = Image.fromarray(img_array)
    buffer = io.BytesIO()
    pil_img.save(buffer, format=format, quality=92)
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    mime = "image/jpeg" if format.upper() == "JPEG" else "image/png"
    return f"data:{mime};base64,{b64_str}"
