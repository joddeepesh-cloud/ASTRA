import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.schemas import HealthResponse, TriageResponse, ErrorResponse, SpaceAIRequest, SpaceAIResponse
from backend.app.services.ml_service import ml_service, MLService
from backend.app.services.space_ai_service import SpaceAIService
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
    file: UploadFile = File(..., description="Astronomical image file (JPEG, PNG, or WEBP)"),
    service: MLService = Depends(get_ml_service)
):
    """
    Process single uploaded observation through the production Galaxy Zoo Multi-Head CNN
    and ASTRA Scientific Triage Engine.
    """
    t0 = time.perf_counter()

    if not service.is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "service_not_ready", "message": "ML Service is still initializing. Please try again shortly."}
        )

    # 1. Content-Type and Filename Validation
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

    # 2. Read File Bytes in Memory
    file_bytes = await file.read()

    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        logger.warning(f"Rejected oversized file upload: {len(file_bytes)} bytes > {settings.MAX_UPLOAD_SIZE_BYTES} limit")
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"error": "file_too_large", "message": f"Uploaded file exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB."}
        )

    # 3. Process through ML Service
    try:
        triage_output = service.analyze_image(file_bytes, filename=file.filename)
        t1 = time.perf_counter()
        proc_ms = round((t1 - t0) * 1000.0, 2)
        prio_str = triage_output.get("priority_level") or "N/A"
        class_str = triage_output.get("predicted_class") or "N/A"
        decision_str = triage_output.get("domain_validation", {}).get("decision", "N/A")
        logger.info(f"Successfully processed image '{file.filename}' in {proc_ms} ms (Domain: {decision_str}, Priority: {prio_str}, Class: {class_str})")
        return triage_output
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

