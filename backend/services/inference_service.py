import os
import json
import logging
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from typing import Dict, Any, Optional, Tuple, List

from src.model import build_model, MedicinalPlantClassifier
from src.gradcam import GradCAM, overlay_heatmap, create_side_by_side_visualization, ndarray_to_base64
from src.dataset import get_val_test_transforms
from backend.services.recommender_service import PlantRecommender

logger = logging.getLogger(__name__)


class InferenceService:
    """
    Confidence-Aware Plant Identification & Explainable AI (Grad-CAM) Service.
    """
    def __init__(
        self,
        model_path: Optional[str] = None,
        backbone_name: str = "mobilenet_v3_large",
        num_classes: int = 93,
        confidence_threshold: float = 0.70,
        device: Optional[str] = None
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.backbone_name = backbone_name
        self.num_classes = num_classes
        self.confidence_threshold = confidence_threshold

        # Paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.saved_models_dir = os.path.join(os.path.dirname(base_dir), "saved_models")
        self.outputs_dir = os.path.join(os.path.dirname(base_dir), "outputs")

        # Load mappings
        self.idx_to_class = self._load_json(os.path.join(self.saved_models_dir, "idx_to_class.json"))
        self.class_to_idx = self._load_json(os.path.join(self.saved_models_dir, "class_to_idx.json"))

        # Recommender & Knowledge Base
        self.recommender = PlantRecommender()
        safety_path = os.path.join(base_dir, "knowledge_base", "safety_database.json")
        self.safety_db = self._load_json(safety_path)

        # Build / Load Model
        if model_path is None:
            default_chk = os.path.join(self.saved_models_dir, "best_plant_model.pth")
            model_path = default_chk if os.path.exists(default_chk) else None

        self.model = build_model(
            num_classes=self.num_classes,
            backbone_name=self.backbone_name,
            pretrained=(model_path is None),
            checkpoint_path=model_path,
            device=self.device
        )
        self.model.eval()

        # Setup Grad-CAM
        self.target_layer = self.model.get_gradcam_target_layer()
        self.gradcam = GradCAM(self.model, self.target_layer)

        # Preprocessing transforms
        self.transform = get_val_test_transforms(image_size=224)
        logger.info(f"InferenceService initialized on {self.device} with backbone {self.backbone_name}.")

    def _load_json(self, path: str) -> Dict:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def predict(
        self,
        pil_image: Image.Image,
        threshold: Optional[float] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Executes end-to-end inference:
        1. Preprocessing & Tensor conversion
        2. Model forward pass
        3. Confidence calculation & thresholding
        4. Grad-CAM generation & overlay blending
        5. Botanical & Ayurvedic profile attachment
        """
        current_threshold = threshold if threshold is not None else self.confidence_threshold

        # Ensure RGB
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        orig_w, orig_h = pil_image.size
        orig_np = np.array(pil_image)

        # Preprocess for model
        input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)

        # Model forward pass
        with torch.no_grad():
            logits = self.model(input_tensor)
            probabilities = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        # Top-K predictions
        top_indices = np.argsort(probabilities)[::-1][:top_k]
        top_k_list = []
        for idx in top_indices:
            cls_name = self.idx_to_class.get(str(idx), f"class_{idx}")
            kb_entry = self.recommender.get_plant_detail(cls_name) or {}
            top_k_list.append({
                "class_index": int(idx),
                "class_id": cls_name,
                "botanical_name": kb_entry.get("botanical_name", cls_name.replace("_", " ")),
                "common_name": kb_entry.get("common_names", {}).get("english") or kb_entry.get("common_names", {}).get("hindi", ""),
                "confidence": float(round(probabilities[idx], 4)),
                "confidence_percent": float(round(probabilities[idx] * 100, 2))
            })

        best_idx = int(top_indices[0])
        best_class = self.idx_to_class.get(str(best_idx), f"class_{best_idx}")
        best_confidence = float(probabilities[best_idx])
        is_confident = (best_confidence >= current_threshold)
        status = "CONFIDENT" if is_confident else "UNCERTAIN"

        # -------------------------------------------------------------
        # 1. TOXIC PLANT TOP-K CHECK (Architecture Diagram: Step 6)
        # Compare all Top-K predicted classes against Safety Database
        # -------------------------------------------------------------
        toxic_matches = []
        for rank, cand in enumerate(top_k_list, start=1):
            cid = cand["class_id"]
            if cid in self.safety_db:
                tox_info = self.safety_db[cid]
                toxic_matches.append({
                    "rank": rank,
                    "class_id": cid,
                    "botanical_name": tox_info.get("botanical_name", cand["botanical_name"]),
                    "sanskrit_name": tox_info.get("sanskrit_name", ""),
                    "toxicity_level": tox_info.get("toxicity_level", "TOXIC"),
                    "severity": tox_info.get("severity", "HIGH"),
                    "warning_title": tox_info.get("warning_title", "TOXIC PLANT WARNING"),
                    "clinical_warning": tox_info.get("clinical_warning", ""),
                    "ayurvedic_safety": tox_info.get("ayurvedic_safety", ""),
                    "confidence_percent": cand["confidence_percent"]
                })

        toxic_found = (len(toxic_matches) > 0)
        has_critical = any(t["severity"] == "CRITICAL" for t in toxic_matches)

        toxic_check_result = {
            "toxic_found": toxic_found,
            "status": "SAFETY_ALERT" if toxic_found else "NO_TOXIC_FOUND",
            "alert_level": "CRITICAL" if has_critical else ("WARNING" if toxic_found else "SAFE"),
            "toxic_count": len(toxic_matches),
            "toxic_plants": toxic_matches,
            "alert_message": (
                f"SAFETY ALERT: {len(toxic_matches)} potentially toxic/poisonous species detected in Top-K candidates! Verify specimen authenticity and consult qualified practitioners before any handling or use."
                if toxic_found else "No toxic or hazardous plant species found in candidate predictions."
            )
        }

        # -------------------------------------------------------------
        # 2. CONFUSED-CLASS CHECK (Architecture Diagram: Step 8)
        # Check if Top-1 and Top-2 predictions are close (margin < 15%)
        # -------------------------------------------------------------
        confused_check_result = {"is_confused": False}
        if len(top_indices) >= 2:
            second_idx = int(top_indices[1])
            second_class = self.idx_to_class.get(str(second_idx), f"class_{second_idx}")
            second_confidence = float(probabilities[second_idx])
            margin = best_confidence - second_confidence
            is_confused = (margin < 0.15)

            p1_meta = self.recommender.get_plant_detail(best_class) or {}
            p2_meta = self.recommender.get_plant_detail(second_class) or {}

            confused_check_result = {
                "is_confused": is_confused,
                "confidence_margin_percent": round(margin * 100, 2),
                "top1_class": best_class,
                "top2_class": second_class,
                "candidate_1": {
                    "class_id": best_class,
                    "botanical_name": p1_meta.get("botanical_name", best_class),
                    "sanskrit_name": p1_meta.get("sanskrit_name") or p1_meta.get("common_names", {}).get("sanskrit", ""),
                    "family": p1_meta.get("family", "Unknown"),
                    "habit": p1_meta.get("habit", "Unknown"),
                    "dosage": p1_meta.get("dosage", "N/A"),
                    "virya": p1_meta.get("ayurvedic_properties", {}).get("virya", "N/A"),
                    "confidence_percent": round(best_confidence * 100, 2)
                },
                "candidate_2": {
                    "class_id": second_class,
                    "botanical_name": p2_meta.get("botanical_name", second_class),
                    "sanskrit_name": p2_meta.get("sanskrit_name") or p2_meta.get("common_names", {}).get("sanskrit", ""),
                    "family": p2_meta.get("family", "Unknown"),
                    "habit": p2_meta.get("habit", "Unknown"),
                    "dosage": p2_meta.get("dosage", "N/A"),
                    "virya": p2_meta.get("ayurvedic_properties", {}).get("virya", "N/A"),
                    "confidence_percent": round(second_confidence * 100, 2)
                },
                "differential_guidance": (
                    f"Top-1 ({p1_meta.get('sanskrit_name') or best_class}) and Top-2 ({p2_meta.get('sanskrit_name') or second_class}) "
                    f"share close visual predictions (margin: {margin * 100:.1f}%). "
                    f"Distinguishing keys: Family differences ({p1_meta.get('family')} vs {p2_meta.get('family')}), "
                    f"habit difference ({p1_meta.get('habit')} vs {p2_meta.get('habit')}), and leaf venation should be examined."
                ) if is_confused else "Top candidate dominates prediction; minimal morphological ambiguity."
            }

        # -------------------------------------------------------------
        # 3. GRAD-CAM COMPUTATION (Architecture Diagram: Step 10)
        # -------------------------------------------------------------
        heatmap, _, _ = self.gradcam.generate_heatmap(input_tensor, target_class=best_idx)

        # Resize original image for visualization display (limit max dimension to 600px for responsive UI speed)
        max_dim = 600
        if max(orig_w, orig_h) > max_dim:
            scale = max_dim / max(orig_w, orig_h)
            disp_w, disp_h = int(orig_w * scale), int(orig_h * scale)
            display_orig_rgb = np.array(pil_image.resize((disp_w, disp_h), Image.Resampling.BILINEAR))
        else:
            display_orig_rgb = orig_np

        # Overlay heatmap
        colored_heatmap_rgb, overlay_rgb = overlay_heatmap(
            original_img_rgb=display_orig_rgb,
            heatmap=heatmap,
            alpha=0.55
        )

        composite = create_side_by_side_visualization(
            original_rgb=display_orig_rgb,
            colored_heatmap=colored_heatmap_rgb,
            overlay_rgb=overlay_rgb,
            predicted_label=best_class,
            confidence=best_confidence
        )

        # Base64 encodings for UI
        original_b64 = ndarray_to_base64(display_orig_rgb, format="JPEG")
        heatmap_b64 = ndarray_to_base64(colored_heatmap_rgb, format="JPEG")
        overlay_b64 = ndarray_to_base64(overlay_rgb, format="JPEG")
        composite_b64 = ndarray_to_base64(composite, format="JPEG")

        # -------------------------------------------------------------
        # 4. BOTANICAL & AYURVEDIC KNOWLEDGE MONOGRAPH (Step 11)
        # -------------------------------------------------------------
        plant_profile = self.recommender.get_plant_detail(best_class) or {}

        # Explanation diagnostic summary
        if is_confident:
            explanation_text = (
                f"The model identified this specimen as {plant_profile.get('botanical_name', best_class)} "
                f"({plant_profile.get('sanskrit_name', '')}) with {best_confidence * 100:.1f}% confidence. "
                f"Grad-CAM visual explanation indicates high activation on key diagnostic morphological structures."
            )
            warning_text = None
        else:
            explanation_text = (
                f"The model's highest candidate is {plant_profile.get('botanical_name', best_class)}, "
                f"but confidence ({best_confidence * 100:.1f}%) is below the required safety threshold ({current_threshold * 100:.1f}%)."
            )
            warning_text = (
                "Identification uncertain → Please upload a clearer image of the plant leaf or stem with good natural lighting, minimal background clutter, and sharp focus."
            )

        return {
            "predicted_class": best_class,
            "botanical_name": plant_profile.get("botanical_name", best_class.replace("_", " ")),
            "sanskrit_name": plant_profile.get("sanskrit_name", ""),
            "family": plant_profile.get("family", "Unknown"),
            "habit": plant_profile.get("habit", "Unknown"),
            "dosage": plant_profile.get("dosage", "N/A"),
            "common_names": plant_profile.get("common_names", {}),
            "confidence": round(best_confidence, 4),
            "confidence_percent": round(best_confidence * 100, 2),
            "confidence_threshold": current_threshold,
            "status": status,
            "is_confident": is_confident,
            "explanation": explanation_text,
            "warning": warning_text,
            "toxic_check": toxic_check_result,
            "confused_check": confused_check_result,
            "top_predictions": top_k_list,
            "plant_profile": plant_profile,
            "visualizations": {
                "original": original_b64,
                "heatmap": heatmap_b64,
                "overlay": overlay_b64,
                "composite": composite_b64
            }
        }
