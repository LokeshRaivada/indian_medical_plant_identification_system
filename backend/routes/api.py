import os
import io
import json
import logging
from typing import Optional, List, Dict, Any
from PIL import Image

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query
from pydantic import BaseModel

from backend.config import AppConfig
from backend.services.inference_service import InferenceService
from backend.services.recommender_service import PlantRecommender

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# Lazy-loaded singletons
_inference_service: Optional[InferenceService] = None
_recommender: Optional[PlantRecommender] = None


def get_inference_service() -> InferenceService:
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService(
            confidence_threshold=AppConfig.DEFAULT_CONFIDENCE_THRESHOLD,
            backbone_name=AppConfig.DEFAULT_BACKBONE
        )
    return _inference_service


def get_recommender() -> PlantRecommender:
    global _recommender
    if _recommender is None:
        _recommender = PlantRecommender()
    return _recommender


class RecommendRequest(BaseModel):
    query: str
    part: Optional[str] = None
    system: Optional[str] = None
    max_results: Optional[int] = 6


class ConfigUpdateRequest(BaseModel):
    confidence_threshold: Optional[float] = None
    top_k: Optional[int] = None


@router.get("/health")
def health_check():
    import torch
    return {
        "status": "online",
        "service": "Indian Medicinal Plant DL & XAI Engine",
        "cuda_available": torch.cuda.is_available(),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "num_classes": 93
    }


@router.get("/sample_image")
def get_sample_image(class_id: str):
    """
    Returns a sample test image for demonstration from the test directory.
    """
    test_dir = os.path.join(AppConfig.PROJECT_ROOT, "test-20260921T080351Z-1-001", "test", class_id)
    if not os.path.exists(test_dir):
        raise HTTPException(status_code=404, detail=f"Class directory {class_id} not found in test set.")
    
    files = [f for f in os.listdir(test_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise HTTPException(status_code=404, detail="No sample images found for this class.")
    
    sample_file = os.path.join(test_dir, files[0])
    from fastapi.responses import FileResponse
    return FileResponse(sample_file, media_type="image/jpeg")


@router.post("/predict")
async def predict_plant(
    file: UploadFile = File(...),
    threshold: Optional[float] = Form(None),
    top_k: Optional[int] = Form(5)
):
    """
    Accepts an uploaded plant image (leaf or whole-plant) and executes:
    - Preprocessing
    - Transfer learning classification
    - Confidence-aware evaluation
    - Grad-CAM heatmap & overlay generation
    - Plant knowledge monograph retrieval
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image (JPEG/PNG/WebP)")

    try:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode image: {str(e)}")

    service = get_inference_service()
    result = service.predict(pil_image=pil_image, threshold=threshold, top_k=top_k)
    return result


@router.post("/recommend")
def recommend_plants(request: RecommendRequest):
    """
    Recommends candidate Indian medicinal plants matching user symptoms,
    diseases, or bodily ailments with match scores and preparation rationale.
    """
    recommender = get_recommender()
    results = recommender.recommend(
        query=request.query,
        selected_part=request.part,
        selected_system=request.system,
        max_results=request.max_results or 6
    )
    return {
        "query": request.query,
        "count": len(results),
        "recommendations": results
    }


@router.get("/plants")
def list_plants(
    search: Optional[str] = Query(None),
    system: Optional[str] = Query(None),
    part: Optional[str] = Query(None)
):
    """
    Returns the complete list of 93 medicinal species in the Herbarium.
    Supports filtering by search query, body system, and part used.
    """
    recommender = get_recommender()
    all_plants = recommender.get_all_plants_summary()

    filtered = all_plants
    if search:
        s = search.lower()
        filtered = [
            p for p in filtered
            if s in p["botanical_name"].lower()
            or s in p["common_name_en"].lower()
            or s in p["common_name_hi"].lower()
            or s in p["common_name_sa"].lower()
        ]
    if system:
        sys_lower = system.lower()
        filtered = [p for p in filtered if any(sys_lower in item.lower() for item in p["systems"])]
    if part:
        part_lower = part.lower()
        filtered = [p for p in filtered if any(part_lower in item.lower() for item in p["parts_used"])]

    return {
        "total": len(filtered),
        "plants": filtered
    }


@router.get("/plants/{plant_id}")
def get_plant_details(plant_id: str):
    """Returns the full knowledge monograph for an individual plant."""
    recommender = get_recommender()
    plant = recommender.get_plant_detail(plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail=f"Plant '{plant_id}' not found in knowledge base.")
    return plant


@router.get("/stats")
def get_academic_stats():
    """
    Returns dataset stats, training history, and test evaluation metrics for academic reviews.
    """
    manifest_dir = AppConfig.MANIFESTS_DIR
    outputs_dir = AppConfig.OUTPUTS_DIR
    saved_models_dir = AppConfig.SAVED_MODELS_DIR

    stats_path = os.path.join(manifest_dir, "dataset_stats.json")
    metrics_path = os.path.join(outputs_dir, "test_metrics.json")
    history_path = os.path.join(saved_models_dir, "training_history.json")

    dataset_stats = {}
    if os.path.exists(stats_path):
        with open(stats_path, "r", encoding="utf-8") as f:
            dataset_stats = json.load(f)

    test_metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            test_metrics = json.load(f)

    training_history = {}
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            training_history = json.load(f)

    cm_exists = os.path.exists(os.path.join(outputs_dir, "confusion_matrix", "confusion_matrix.png"))
    curves_exist = os.path.exists(os.path.join(outputs_dir, "training_plots", "training_curves.png"))

    return {
        "dataset_stats": dataset_stats,
        "test_metrics": test_metrics,
        "training_history": training_history,
        "has_confusion_matrix": cm_exists,
        "has_training_curves": curves_exist
    }


@router.get("/config")
def get_config():
    service = get_inference_service()
    return {
        "confidence_threshold": service.confidence_threshold,
        "backbone": service.backbone_name,
        "num_classes": service.num_classes,
        "device": service.device
    }


@router.post("/config")
def update_config(req: ConfigUpdateRequest):
    service = get_inference_service()
    if req.confidence_threshold is not None:
        if not (0.1 <= req.confidence_threshold <= 0.99):
            raise HTTPException(status_code=400, detail="Confidence threshold must be between 0.10 and 0.99")
        service.confidence_threshold = req.confidence_threshold
    return {
        "message": "Configuration updated successfully",
        "confidence_threshold": service.confidence_threshold
    }
