from backend.app.services.ml_service import ml_service, MLService

def get_ml_service() -> MLService:
    """
    Dependency accessor returning global MLService singleton instance.
    """
    return ml_service
