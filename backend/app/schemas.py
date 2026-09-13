from pydantic import BaseModel, Field
from typing import Dict, Optional

class DomainValidation(BaseModel):
    probability_astronomical: float = Field(..., json_schema_extra={"example": 0.9985})
    probability_non_astronomical: float = Field(..., json_schema_extra={"example": 0.0015})
    decision: str = Field(..., json_schema_extra={"example": "COMPATIBLE"})
    model_version: str = Field(..., json_schema_extra={"example": "mobilenet_v3_small_domain_gate_v2"})
    inference_time_ms: float = Field(..., json_schema_extra={"example": 6.12})
    semantic_gate_status: Optional[str] = Field(default=None, json_schema_extra={"example": "SEMANTIC_COMPATIBLE"})
    semantic_astronomical_score: Optional[float] = Field(default=None, json_schema_extra={"example": 0.3079})
    semantic_competing_score: Optional[float] = Field(default=None, json_schema_extra={"example": 0.2814})
    semantic_margin: Optional[float] = Field(default=None, json_schema_extra={"example": 0.0264})
    semantic_reason: Optional[str] = Field(default=None, json_schema_extra={"example": "Image is semantically consistent with astronomical observation data."})

class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "ok"})
    service: str = Field(..., json_schema_extra={"example": "ASTRA"})
    ml_ready: bool = Field(..., json_schema_extra={"example": True})
    model_loaded: bool = Field(..., json_schema_extra={"example": True})
    domain_gate_loaded: bool = Field(default=True, json_schema_extra={"example": True})
    semantic_gate_loaded: bool = Field(default=True, json_schema_extra={"example": True})
    model_version: str = Field(..., json_schema_extra={"example": "galaxy-zoo-efficientnet-b0-epoch10"})
    domain_gate_model_version: str = Field(default="mobilenet_v3_small_domain_gate_v2", json_schema_extra={"example": "mobilenet_v3_small_domain_gate_v2"})
    semantic_gate_model_version: str = Field(default="open_clip_vit_b_32_laion2b", json_schema_extra={"example": "open_clip_vit_b_32_laion2b"})
    device: str = Field(..., json_schema_extra={"example": "mps"})
    backend_version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    startup_duration_ms: float = Field(..., json_schema_extra={"example": 191.21})

class TriageResponse(BaseModel):
    domain_validation: DomainValidation
    predicted_class: Optional[str] = Field(default=None, json_schema_extra={"example": "FEATURED_DISK"})
    class_confidence: Optional[float] = Field(default=None, json_schema_extra={"example": 0.7841})
    class_probabilities: Optional[Dict[str, float]] = Field(default=None)
    scientific_attributes: Optional[Dict[str, float]] = Field(default=None)
    raw_embedding_distance: Optional[float] = Field(default=None, json_schema_extra={"example": 0.5382})
    raw_pred_class_distance: Optional[float] = Field(default=None, json_schema_extra={"example": 0.5382})
    nearest_reference_class: Optional[str] = Field(default=None, json_schema_extra={"example": "FEATURED_DISK"})
    novelty_score: Optional[float] = Field(default=None, json_schema_extra={"example": 0.4643})
    classification_entropy_bits: Optional[float] = Field(default=None, json_schema_extra={"example": 1.1245})
    uncertainty_score: Optional[float] = Field(default=None, json_schema_extra={"example": 0.2879})
    oddity_score: Optional[float] = Field(default=None, json_schema_extra={"example": 0.5781})
    experimental_triage_score: Optional[float] = Field(default=None, json_schema_extra={"example": 0.4367})
    priority_level: Optional[str] = Field(default=None, json_schema_extra={"example": "MEDIUM"})
    explanation: str = Field(..., json_schema_extra={"example": "Domain validation passed. Proceeding with astronomical morphology and triage analysis."})
    model_version: str = Field(..., json_schema_extra={"example": "Epoch 10"})
    inference_time_ms: float = Field(..., json_schema_extra={"example": 15.615})
    total_triage_ms: float = Field(..., json_schema_extra={"example": 15.75})
    score_interpretation: str = Field(
        default="Experimental prioritization heuristic; not a calibrated anomaly probability.",
        json_schema_extra={"example": "Experimental prioritization heuristic; not a calibrated anomaly probability."}
    )

class ErrorResponse(BaseModel):
    error: str = Field(..., json_schema_extra={"example": "invalid_image"})
    message: str = Field(..., json_schema_extra={"example": "The uploaded file could not be decoded as a valid image."})
