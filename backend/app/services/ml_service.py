import io
import time
import logging
from PIL import Image, ImageOps
import numpy as np

from ml.src.inference import GalaxyZooInference
from ml.src.triage import ASTRATriageEngine
from ml.src.domain_gate import DomainGate
from ml.src.semantic_gate import SemanticDomainGate
from backend.app.config import settings

logger = logging.getLogger("astra.ml_service")

class MLService:
    """
    Singleton ML Service managing SemanticDomainGate, DomainGate V2, GalaxyZooInference, and ASTRATriageEngine lifecycle.
    
    Model weights and reference distribution artifacts are loaded ONCE during backend startup.
    A dummy inference pass is performed during initialization to warm up PyTorch MPS/CUDA shaders.
    """
    def __init__(self):
        self.semantic_gate = None
        self.domain_gate = None
        self.inference_engine = None
        self.triage_engine = None
        self.is_loaded = False
        self.domain_gate_loaded = False
        self.semantic_gate_loaded = False
        self.is_ready = False
        self.startup_duration_ms = 0.0
        self.model_version_str = "galaxy-zoo-efficientnet-b0-epoch10"
        self.domain_gate_model_version = "mobilenet_v3_small_domain_gate_v2"
        self.semantic_gate_model_version = "open_clip_vit_b_32_laion2b"
        self.device_str = "cpu"

    def initialize(self):
        if self.is_ready:
            logger.info("MLService already initialized and ready.")
            return

        t0 = time.perf_counter()
        logger.info(f"Initializing MLService with Model: {settings.MODEL_PATH} and Domain Gate: {settings.DOMAIN_GATE_PATH}")

        # 1. Load Universal Semantic Gate (Stage 1)
        self.semantic_gate = SemanticDomainGate()
        self.semantic_gate_model_version = getattr(self.semantic_gate, "model_version", "open_clip_vit_b_32_laion2b")
        self.semantic_gate_loaded = True

        # 2. Load Domain Gate V2 (Stage 2)
        self.domain_gate = DomainGate(
            model_path=settings.DOMAIN_GATE_PATH
        )
        self.domain_gate_model_version = getattr(self.domain_gate, "model_version", "mobilenet_v3_small_domain_gate_v2")
        self.domain_gate_loaded = True

        # 3. Load Galaxy Zoo Inference Engine
        self.inference_engine = GalaxyZooInference(
            model_path=settings.MODEL_PATH
        )
        self.device_str = str(self.inference_engine.device)
        ckpt_epoch = self.inference_engine.checkpoint.get("epoch", 10)
        self.model_version_str = f"galaxy-zoo-efficientnet-b0-epoch{ckpt_epoch}"

        # 4. Load Triage Engine
        self.triage_engine = ASTRATriageEngine(
            reference_path=settings.TRIAGE_REF_PATH,
            inference_engine=self.inference_engine
        )

        self.is_loaded = True

        # 5. Perform Warmup Inference (Eliminate MPS/CUDA cold-start shader compilation penalty)
        logger.info("Executing PyTorch model warmup passes (Semantic Gate + Domain Gate + Galaxy Zoo Triage)...")
        t0_warm = time.perf_counter()
        dummy_img = Image.new("RGB", (224, 224), color=(128, 128, 128))
        _ = self.semantic_gate.validate_pil_image(dummy_img)
        _ = self.domain_gate.predict(dummy_img)
        _ = self.triage_engine.triage_single_image(dummy_img)
        t1_warm = time.perf_counter()
        warmup_ms = round((t1_warm - t0_warm) * 1000.0, 2)
        logger.info(f"Model warmup pass completed in {warmup_ms} ms.")

        t1 = time.perf_counter()
        self.startup_duration_ms = round((t1 - t0) * 1000.0, 2)
        self.is_ready = True

        logger.info(
            f"MLService initialized successfully on device '{self.device_str}' "
            f"in {self.startup_duration_ms} ms. Model: {self.model_version_str}, Domain Gate V2: {self.domain_gate_model_version}, Semantic Gate: {self.semantic_gate_model_version}"
        )

    def analyze_image(self, file_bytes: bytes, filename: str = "") -> dict:
        """
        Process single image observation through Two-Stage Domain Validation:
        Stage 1: Universal Semantic Gate (CLIP prompt family ensemble)
        Stage 2: Domain Gate V2 (MobileNetV3-Small astronomy gate)
        
        Only when BOTH gates agree COMPATIBLE does the request proceed to Galaxy Zoo morphology & Triage.
        """
        t0 = time.perf_counter()

        if not self.is_ready:
            raise RuntimeError("ML Service is not ready to process requests.")

        if not file_bytes:
            raise ValueError("Empty file payload received.")

        if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(f"File size ({len(file_bytes)} bytes) exceeds maximum upload limit of {settings.MAX_UPLOAD_SIZE_BYTES} bytes.")

        # Decode image in memory using PIL
        try:
            image = Image.open(io.BytesIO(file_bytes))
            image = ImageOps.exif_transpose(image).convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to decode image file '{filename}': {e}")
            raise ValueError(f"The uploaded file '{filename}' could not be decoded as a valid image.")

        # STAGE 1: Execute Universal Semantic Gate FIRST
        sem_result = self.semantic_gate.validate_pil_image(image)

        # Handle STAGE 1 INCOMPATIBLE
        if sem_result.status == "SEMANTIC_INCOMPATIBLE":
            t1 = time.perf_counter()
            dom_meta = {
                "probability_astronomical": float(sem_result.astronomical_score),
                "probability_non_astronomical": float(sem_result.competing_score),
                "decision": "INCOMPATIBLE",
                "model_version": self.domain_gate_model_version,
                "inference_time_ms": sem_result.latency_ms,
                "semantic_gate_status": sem_result.status,
                "semantic_astronomical_score": sem_result.astronomical_score,
                "semantic_competing_score": sem_result.competing_score,
                "semantic_margin": sem_result.semantic_margin,
                "semantic_reason": sem_result.reason
            }
            return {
                "domain_validation": dom_meta,
                "explanation": "This image does not appear to contain astronomical observation data. No astronomical classification was performed.",
                "model_version": self.model_version_str,
                "inference_time_ms": sem_result.latency_ms,
                "total_triage_ms": round((t1 - t0) * 1000.0, 2),
                "score_interpretation": "Semantic validation failed; image is outside ASTRA astronomical observation domain."
            }

        # Handle STAGE 1 UNCERTAIN
        if sem_result.status == "SEMANTIC_UNCERTAIN":
            t1 = time.perf_counter()
            dom_meta = {
                "probability_astronomical": float(sem_result.astronomical_score),
                "probability_non_astronomical": float(sem_result.competing_score),
                "decision": "UNCERTAIN",
                "model_version": self.domain_gate_model_version,
                "inference_time_ms": sem_result.latency_ms,
                "semantic_gate_status": sem_result.status,
                "semantic_astronomical_score": sem_result.astronomical_score,
                "semantic_competing_score": sem_result.competing_score,
                "semantic_margin": sem_result.semantic_margin,
                "semantic_reason": sem_result.reason
            }
            return {
                "domain_validation": dom_meta,
                "explanation": "This image could not be confidently verified as compatible with ASTRA's astronomical observation domain. No astronomical classification was performed.",
                "model_version": self.model_version_str,
                "inference_time_ms": sem_result.latency_ms,
                "total_triage_ms": round((t1 - t0) * 1000.0, 2),
                "score_interpretation": "Semantic validation uncertain; image cannot be verified as astronomical observation data."
            }

        # STAGE 2: Execute Domain Gate V2 (Only when Stage 1 is SEMANTIC_COMPATIBLE)
        v2_result = self.domain_gate.predict(image)
        decision_v2 = v2_result.get("decision", "INCOMPATIBLE")

        # Attach semantic gate metadata to domain_validation
        v2_result["semantic_gate_status"] = sem_result.status
        v2_result["semantic_astronomical_score"] = sem_result.astronomical_score
        v2_result["semantic_competing_score"] = sem_result.competing_score
        v2_result["semantic_margin"] = sem_result.semantic_margin
        v2_result["semantic_reason"] = sem_result.reason
        v2_result["inference_time_ms"] = round(v2_result["inference_time_ms"] + sem_result.latency_ms, 2)

        # Handle STAGE 2 INCOMPATIBLE
        if decision_v2 == "INCOMPATIBLE":
            t1 = time.perf_counter()
            return {
                "domain_validation": v2_result,
                "explanation": "This image does not appear to contain astronomical observation data. No astronomical classification was performed.",
                "model_version": self.model_version_str,
                "inference_time_ms": v2_result["inference_time_ms"],
                "total_triage_ms": round((t1 - t0) * 1000.0, 2),
                "score_interpretation": "Domain Gate V2 validation failed; image is outside ASTRA astronomical observation domain."
            }

        # Handle STAGE 2 UNCERTAIN
        if decision_v2 == "UNCERTAIN":
            t1 = time.perf_counter()
            return {
                "domain_validation": v2_result,
                "explanation": "This image could not be confidently verified as compatible with ASTRA's astronomical observation domain. No astronomical classification was performed.",
                "model_version": self.model_version_str,
                "inference_time_ms": v2_result["inference_time_ms"],
                "total_triage_ms": round((t1 - t0) * 1000.0, 2),
                "score_interpretation": "Domain Gate V2 validation uncertain; image cannot be verified as astronomical observation data."
            }

        # BOTH STAGES PASSED (SEMANTIC_COMPATIBLE + DOMAIN_GATE_V2_COMPATIBLE)
        triage_output = self.triage_engine.triage_single_image(image)

        triage_output["domain_validation"] = v2_result
        triage_output["explanation"] = (
            f"Two-stage domain validation passed. Proceeding with astronomical morphology and triage analysis. "
            f"{triage_output['explanation']}"
        )
        triage_output["score_interpretation"] = (
            "Experimental prioritization heuristic; not a calibrated anomaly probability."
        )

        t1 = time.perf_counter()
        triage_output["total_triage_ms"] = round((t1 - t0) * 1000.0, 2)

        return triage_output

# Global Singleton Instance
ml_service = MLService()
