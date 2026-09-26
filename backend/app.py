import os
import sys
import io
import json
import logging
from PIL import Image

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from backend.config import AppConfig
from backend.services.inference_service import InferenceService
from backend.services.recommender_service import PlantRecommender

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize Flask App
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Lazy-loaded singletons
_inference_service = None
_recommender = None


def get_inference_service():
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService(
            confidence_threshold=AppConfig.DEFAULT_CONFIDENCE_THRESHOLD,
            backbone_name=AppConfig.DEFAULT_BACKBONE
        )
    return _inference_service


def get_recommender():
    global _recommender
    if _recommender is None:
        _recommender = PlantRecommender()
    return _recommender


@app.route("/api/health", methods=["GET"])
def health_check():
    import torch
    return jsonify({
        "status": "online",
        "service": "Indian Medicinal Plant DL & XAI Engine (Flask)",
        "cuda_available": torch.cuda.is_available(),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "num_classes": 93
    })


@app.route("/api/predict", methods=["POST"])
def predict_plant():
    """
    Accepts plant image upload and runs:
    - Preprocessing
    - PyTorch MobileNetV3-Large classification
    - Confidence-aware thresholding
    - Grad-CAM heatmap & overlay generation
    - Knowledge Base monograph attachment
    """
    if "file" not in request.files:
        return jsonify({"detail": "No image file provided in request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"detail": "Empty filename."}), 400

    try:
        image_bytes = file.read()
        pil_image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return jsonify({"detail": f"Failed to decode image: {str(e)}"}), 400

    threshold = request.form.get("threshold", default=None, type=float)
    top_k = request.form.get("top_k", default=5, type=int)

    service = get_inference_service()
    result = service.predict(pil_image=pil_image, threshold=threshold, top_k=top_k)
    return jsonify(result)


@app.route("/api/recommend", methods=["POST"])
def recommend_plants():
    """
    Recommends Indian medicinal plants based on symptoms, diseases, or body systems.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    part = data.get("part")
    system = data.get("system")
    max_results = data.get("max_results", 8)

    recommender = get_recommender()
    results = recommender.recommend(
        query=query,
        selected_part=part,
        selected_system=system,
        max_results=max_results
    )
    return jsonify({
        "query": query,
        "count": len(results),
        "recommendations": results
    })


@app.route("/api/plants", methods=["GET"])
def list_plants():
    """
    Returns full list of 93 medicinal species in the Herbarium.
    Supports filtering by search query, body system, part used, habit, and potency.
    """
    search = request.args.get("search", "").strip().lower()
    system = request.args.get("system", "").strip().lower()
    part = request.args.get("part", "").strip().lower()
    habit = request.args.get("habit", "").strip().lower()
    potency = request.args.get("potency", "").strip().lower()

    recommender = get_recommender()
    all_plants = recommender.get_all_plants_summary()

    filtered = all_plants
    if search:
        filtered = [
            p for p in filtered
            if search in p["botanical_name"].lower()
            or search in p["common_name_en"].lower()
            or search in p["common_name_hi"].lower()
            or search in p["common_name_sa"].lower()
            or search in p.get("sanskrit_name", "").lower()
            or search in p.get("family", "").lower()
        ]
    if system:
        filtered = [p for p in filtered if any(system in item.lower() for item in p.get("systems", []))]
    if part:
        filtered = [p for p in filtered if any(part in item.lower() for item in p.get("parts_used", []))]
    if habit:
        filtered = [p for p in filtered if habit in p.get("habit", "").lower()]
    if potency:
        filtered = [p for p in filtered if potency in p.get("potency", "").lower()]

    return jsonify({
        "total": len(filtered),
        "plants": filtered
    })


@app.route("/api/plants/<plant_id>", methods=["GET"])
def get_plant_detail(plant_id):
    """Returns detailed medicinal monograph for a specific plant."""
    recommender = get_recommender()
    plant = recommender.get_plant_detail(plant_id)
    if not plant:
        return jsonify({"detail": f"Plant '{plant_id}' not found."}), 404
    return jsonify(plant)


@app.route("/api/sample_image", methods=["GET"])
def get_sample_image():
    """Returns an authentic test image specimen for rapid UI demonstration."""
    class_id = request.args.get("class_id")
    if not class_id:
        return jsonify({"detail": "Missing class_id parameter."}), 400

    test_dir = os.path.join(AppConfig.PROJECT_ROOT, "test-20260921T080351Z-1-001", "test", class_id)
    if not os.path.exists(test_dir):
        return jsonify({"detail": f"Class directory {class_id} not found."}), 404

    files = [f for f in os.listdir(test_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        return jsonify({"detail": "No images found for this class."}), 404

    sample_path = os.path.join(test_dir, files[0])
    return send_file(sample_path, mimetype="image/jpeg")


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Returns dataset split stats, test metrics, and training history."""
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

    return jsonify({
        "dataset_stats": dataset_stats,
        "test_metrics": test_metrics,
        "training_history": training_history,
        "has_confusion_matrix": cm_exists,
        "has_training_curves": curves_exist
    })


@app.route("/api/config", methods=["GET", "POST"])
def handle_config():
    service = get_inference_service()
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        new_thresh = data.get("confidence_threshold")
        if new_thresh is not None:
            if 0.1 <= float(new_thresh) <= 0.99:
                service.confidence_threshold = float(new_thresh)
            else:
                return jsonify({"detail": "Threshold must be between 0.10 and 0.99"}), 400
        return jsonify({
            "message": "Configuration updated successfully",
            "confidence_threshold": service.confidence_threshold
        })

    return jsonify({
        "confidence_threshold": service.confidence_threshold,
        "backbone": service.backbone_name,
        "num_classes": service.num_classes,
        "device": service.device
    })


# Static route for outputs (confusion matrix & training curves)
@app.route("/outputs/<path:filename>")
def serve_output_file(filename):
    return send_from_directory(AppConfig.OUTPUTS_DIR, filename)


if __name__ == "__main__":
    app.run(host=AppConfig.HOST, port=AppConfig.PORT, debug=AppConfig.DEBUG)
