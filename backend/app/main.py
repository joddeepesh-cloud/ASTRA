import time
import uuid
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, UploadFile, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.schemas import HealthResponse, TriageResponse, ErrorResponse, SpaceAIRequest, SpaceAIResponse, EvidenceResponse
from backend.app.services.ml_service import ml_service, MLService
from backend.app.services.space_ai_service import SpaceAIService
from backend.app.services.evidence.evidence_store import evidence_store
from backend.app.services.evidence.evidence_worker import run_background_evidence_enrichment
from backend.app.dependencies import get_ml_service, get_space_ai_service

# Configure lightweight structured logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("astra.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager.
    Loads PyTorch model and reference artifacts ONCE at startup and executes a warmup pass.
    """
    logger.info("Starting up ASTRA FastAPI Backend...")
    try:
        ml_service.initialize()
    except Exception as e:
        logger.error(f"Fatal error initializing ML Service: {e}", exc_info=True)
        raise e
    yield
    logger.info("Shutting down ASTRA FastAPI Backend...")

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "ASTRA identifies astronomical observations that differ from its learned "
        "reference distribution and prioritizes them for scientific review. "
        "Outputs provide experimental triage scores for prioritization and do NOT "
        "constitute confirmed anomaly discoveries."
    ),
    version=settings.BACKEND_VERSION,
    lifespan=lifespan
)

# CORS Setup
allowed_origins = list(dict.fromkeys(settings.ALLOWED_ORIGINS + [settings.FRONTEND_ORIGIN]))
logger.info(f"Configured CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=getattr(settings, "ALLOW_ORIGIN_REGEX", None),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get(
    f"{settings.API_V1_STR}/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Get service health & ML model readiness status"
)
async def get_health(service: MLService = Depends(get_ml_service)):
    """
    Expose backend health, readiness, selected PyTorch device, and model version.
    Does NOT execute model inference.
    """
    return HealthResponse(
        status="ok",
        service="ASTRA",
        ml_ready=service.is_ready,
        model_loaded=service.is_loaded,
        domain_gate_loaded=service.domain_gate_loaded,
        semantic_gate_loaded=getattr(service, "semantic_gate_loaded", True),
        model_version=service.model_version_str,
        domain_gate_model_version=service.domain_gate_model_version,
        semantic_gate_model_version=getattr(service, "semantic_gate_model_version", "open_clip_vit_b_32_laion2b"),
        device=service.device_str,
        backend_version=settings.BACKEND_VERSION,
        startup_duration_ms=service.startup_duration_ms
    )

@app.post(
    f"{settings.API_V1_STR}/triage",
    response_model=TriageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid image payload or unsupported format"},
        413: {"model": ErrorResponse, "description": "File upload exceeds maximum allowed size"},
        500: {"model": ErrorResponse, "description": "Unexpected ML inference error"}
    },
    tags=["Scientific Triage"],
    summary="Submit single astronomical image for scientific triage"
)
async def analyze_triage(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Astronomical image file (JPEG, PNG, or WEBP)"),
    user_selected_study_type: Optional[str] = Form(None, description="Optional user research study tag (does NOT affect triage result or model classification)"),
    ra: Optional[float] = Form(None, description="Optional Right Ascension (RA in degrees) for catalog evidence enrichment"),
    dec: Optional[float] = Form(None, description="Optional Declination (DEC in degrees) for catalog evidence enrichment"),
    observation_id: Optional[str] = Form(None, description="Optional unique observation identifier"),
    service: MLService = Depends(get_ml_service)
):
    """
    Process single image observation through Two-Stage Domain Validation and Object Identification:
    
    1. Universal Semantic Gate (Stage 1)
    2. Domain Gate V2 (Stage 2)
    3. Object Identification Service (OpenCLIP Zero-Shot Ensemble)
    4. Galaxy Zoo Morphology Model (ONLY invoked when object is GALAXY)
    5. Experimental Scientific Triage Engine
    6. Asynchronous Background Multi-Modal Evidence Enrichment (Non-blocking)
    
    Returns structured TriageResponse payload IMMEDIATELY.
    """
    t0 = time.perf_counter()

    if not service.is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "service_not_ready", "message": "ML Service is still initializing. Please try again shortly."}
        )

    # Content-Type and Filename Validation
    content_type = (file.content_type or "").lower()
    filename = (file.filename or "").lower()

    valid_exts = (".jpg", ".jpeg", ".png", ".webp")
    is_valid_type = (content_type in settings.ALLOWED_IMAGE_TYPES) or filename.endswith(valid_exts)

    if not is_valid_type:
        logger.warning(f"Rejected upload with unsupported format: filename='{file.filename}', content_type='{file.content_type}'")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "unsupported_format", "message": "Only JPEG, PNG, and WEBP image formats are supported."}
        )

    try:
        contents = await file.read()
    except Exception as e:
        logger.error(f"Error reading upload payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_image", "message": "Failed to read file payload."}
        )

    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        logger.warning(f"Rejected oversized file upload: {len(contents)} bytes > {settings.MAX_UPLOAD_SIZE_BYTES} limit")
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"error": "file_too_large", "message": f"Uploaded file exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB."}
        )

    try:
        result = service.analyze_image(contents, filename=file.filename, user_selected_study_type=user_selected_study_type)
        t1 = time.perf_counter()
        proc_ms = round((t1 - t0) * 1000.0, 2)
        prio_str = result.get("priority_level") or "N/A"
        class_str = result.get("predicted_class") or "N/A"
        decision_str = result.get("domain_validation", {}).get("decision", "N/A")

        # Generate observation_id if not supplied
        obs_id = observation_id or f"OBS-{uuid.uuid4().hex[:8].upper()}"
        initial_status = "PENDING" if (ra is not None and dec is not None) else "UNAVAILABLE"

        # Prepare structural image evidence payload for EvidenceFusionEngine
        obj_info = result.get("object_type_info") or {}
        image_evidence = {
            "predicted_object_type": result.get("predicted_object_type"),
            "visual_similarity_score": result.get("visual_similarity_score"),
            "object_margin": result.get("object_margin"),
            "object_type_status": result.get("object_type_status"),
            "morphology_label": result.get("morphology"),
            "morphology_confidence": result.get("class_confidence"),
            "evidence_quality": obj_info.get("evidence_quality"),
            "evidence": obj_info.get("evidence", [])
        }

        # Enqueue Asynchronous Background Evidence Enrichment (Non-blocking)
        background_tasks.add_task(
            run_background_evidence_enrichment,
            observation_id=obs_id,
            ra=ra,
            dec=dec,
            image_evidence=image_evidence
        )

        result["observation_id"] = obs_id
        result["evidence_status"] = initial_status
        result["ra"] = ra
        result["dec"] = dec

        logger.info(f"Successfully processed image '{file.filename}' in {proc_ms} ms (Domain: {decision_str}, Priority: {prio_str}, Class: {class_str}, ObsID: {obs_id}, EvidenceStatus: {initial_status})")
        return TriageResponse(**result)
    except ValueError as ve:
        logger.warning(f"Validation error processing image '{file.filename}': {ve}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "invalid_image", "message": str(ve)}
        )
    except Exception as e:
        logger.error(f"Unexpected inference failure processing '{file.filename}': {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "inference_failure", "message": "An unexpected error occurred during scientific triage analysis."}
        )

@app.get(
    f"{settings.API_V1_STR}/observations/{{observation_id}}/evidence",
    response_model=EvidenceResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Observation evidence record not found"}
    },
    tags=["Multi-Modal Evidence"],
    summary="Retrieve multi-modal catalog evidence fusion record for observation"
)
async def get_observation_evidence(observation_id: str):
    """
    Retrieve stored FusedEvidenceResult and catalog enrichment status for observation.
    Returns status: PENDING, COMPLETE, UNAVAILABLE, or ERROR.
    """
    record = evidence_store.get_evidence(observation_id)
    if record is None:
        # Check if no trusted coordinates supplied
        return EvidenceResponse(
            observation_id=observation_id,
            evidence_status="UNAVAILABLE",
            ra=None,
            dec=None,
            fused_object_type=None,
            evidence_level="NONE",
            match_quality="UNAVAILABLE",
            catalog_sources_queried=["Gaia DR3", "SDSS DR16", "ALLWISE", "TESS", "NASA Exoplanet Archive", "SIMBAD"],
            contributing_catalogs=[],
            explanation="Catalog enrichment unavailable — no trusted celestial coordinates were supplied.",
            provenance=[],
            conflicts=[],
            fused_result=None,
            updated_at=None
        )

    return EvidenceResponse(**record)

@app.post(
    f"{settings.API_V1_STR}/observations/{{observation_id}}/enrich",
    response_model=EvidenceResponse,
    tags=["Multi-Modal Evidence"],
    summary="Trigger asynchronous catalog evidence enrichment for observation coordinates"
)
async def trigger_observation_enrichment(
    observation_id: str,
    background_tasks: BackgroundTasks,
    ra: Optional[float] = Form(None),
    dec: Optional[float] = Form(None)
):
    """
    Trigger or re-run background catalog evidence enrichment for an observation with RA/Dec coordinates.
    """
    if ra is None or dec is None:
        existing = evidence_store.get_evidence(observation_id)
        if existing:
            ra = existing.get("ra")
            dec = existing.get("dec")

    if ra is None or dec is None:
        evidence_store.set_status(
            observation_id=observation_id,
            status="UNAVAILABLE",
            explanation="Catalog enrichment unavailable — no trusted celestial coordinates were supplied.",
            ra=None,
            dec=None
        )
        rec = evidence_store.get_evidence(observation_id)
        return EvidenceResponse(**rec)

    # Enqueue background enrichment
    background_tasks.add_task(
        run_background_evidence_enrichment,
        observation_id=observation_id,
        ra=ra,
        dec=dec,
        image_evidence=None
    )

    rec = evidence_store.get_evidence(observation_id) or {
        "observation_id": observation_id,
        "evidence_status": "PENDING",
        "ra": ra,
        "dec": dec,
        "fused_object_type": None,
        "evidence_level": "NONE",
        "match_quality": "NO_MATCH",
        "catalog_sources_queried": ["Gaia DR3", "SDSS DR16", "ALLWISE", "TESS", "NASA Exoplanet Archive", "SIMBAD"],
        "contributing_catalogs": [],
        "explanation": "Catalog evidence enrichment enqueued in background...",
        "provenance": [],
        "conflicts": [],
        "fused_result": None,
        "updated_at": None
    }
    return EvidenceResponse(**rec)


@app.post(
    f"{settings.API_V1_STR}/space-ai",
    response_model=SpaceAIResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid question format"},
        500: {"model": ErrorResponse, "description": "Unexpected Space Help AI processing error"}
    },
    tags=["Space Help AI"],
    summary="Ask ASTRA Space Help AI a specialized astronomy or observation question"
)
async def ask_space_ai(
    request: SpaceAIRequest,
    space_ai: SpaceAIService = Depends(get_space_ai_service)
):
    """
    ASTRA Space Help AI specialized astronomy assistant endpoint.
    Processes general astronomy and observation-specific questions using structured
    observation context payloads, off-topic guardrails, and LLM providers.
    """
    try:
        res = space_ai.answer_question(
            question=request.question,
            observation_context=request.observation_context,
            conversation_history=request.conversation_history,
            image_base64=request.image_base64
        )
        return SpaceAIResponse(**res)
    except Exception as e:
        logger.error(f"Error processing Space AI request: {e}", exc_info=True)
        return SpaceAIResponse(
            answer="ASTRA Space Help AI encountered an unexpected processing error. Please try again shortly.",
            scope="error",
            observation_id=request.observation_context.get("observation_id") if request.observation_context else None,
            grounded=False,
            available=False,
            error=str(e)
        )

