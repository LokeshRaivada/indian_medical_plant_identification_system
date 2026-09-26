import os

class AppConfig:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
    FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
    SAVED_MODELS_DIR = os.path.join(PROJECT_ROOT, "saved_models")
    OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
    MANIFESTS_DIR = os.path.join(PROJECT_ROOT, "dataset_manifests")
    
    DEFAULT_CONFIDENCE_THRESHOLD = 0.70
    DEFAULT_TOP_K = 5
    DEFAULT_BACKBONE = "mobilenet_v3_large"
    DEFAULT_COLORMAP = "JET"
    
    # Flask Server Port
    HOST = "127.0.0.1"
    PORT = 5000
    DEBUG = False
