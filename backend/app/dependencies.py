from backend.app.services.ml_service import ml_service, MLService
from backend.app.services.space_ai_service import space_ai_service, SpaceAIService

def get_ml_service() -> MLService:
    """
    Dependency accessor returning global MLService singleton instance.
    """
    return ml_service

def get_space_ai_service() -> SpaceAIService:
    """
    Dependency accessor returning global SpaceAIService singleton instance.
    """
    return space_ai_service
