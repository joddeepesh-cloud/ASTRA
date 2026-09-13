import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "ASTRA Scientific Triage API"
    API_V1_STR: str = "/api/v1"
    BACKEND_VERSION: str = "1.0.0"
    
    # Path settings
    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    MODEL_PATH: str = os.path.join(PROJECT_ROOT, "ml", "models", "best_model.pt")
    DOMAIN_GATE_PATH: str = os.path.join(PROJECT_ROOT, "ml", "models", "domain_gate_v2_best.pt")
    TRIAGE_REF_PATH: str = os.path.join(PROJECT_ROOT, "ml", "artifacts", "triage_reference.json")
    
    # Security & Upload constraints
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:5179",
    ]
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_IMAGE_TYPES: set = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
