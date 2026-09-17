import io
import time
import logging
from PIL import Image, ImageOps
import numpy as np

from ml.src.inference import GalaxyZooInference
from ml.src.triage import ASTRATriageEngine
from ml.src.domain_gate import DomainGate
from ml.src.semantic_gate import SemanticDomainGate
from ml.src.object_identification import ObjectIdentificationService
from backend.app.config import settings

logger = logging.getLogger("astra.ml_service")

class MLService:
    """
    Singleton ML Service managing SemanticDomainGate, DomainGate V2, GalaxyZooInference, ObjectIdentificationService, and ASTRATriageEngine lifecycle.
    
    Model weights and reference distribution artifacts are loaded ONCE during backend startup.
    A dummy inference pass is performed during initialization to warm up PyTorch MPS/CUDA shaders.
    """
    def __init__(self):
        self.semantic_gate = None
        self.domain_gate = None
        self.object_id_service = None
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

        # 2. Instantiate Object Identification Service
        self.object_id_service = ObjectIdentificationService(semantic_gate=self.semantic_gate)

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

    def analyze_image(self, file_bytes: bytes, filename: str = "", user_selected_study_type: str = None) -> dict:
        """
        Process single image observation through Two-Stage Domain Validation & Object Identification:
        Stage 1: Universal Semantic Gate (CLIP prompt family ensemble)
        Stage 2: Domain Gate V2 (MobileNetV3-Small astronomy gate)
        Stage 3: Object Identification Service (OpenCLIP Zero-Shot Ensemble)
        
        Only when Stage 1 & 2 pass AND Stage 3 identifies GALAXY does the request proceed to Galaxy Zoo morphology.
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
        t_sem_0 = time.perf_counter()
        sem_result = self.semantic_gate.validate_pil_image(image)
        t_sem_1 = time.perf_counter()
        sem_ms = round((t_sem_1 - t_sem_0) * 1000.0, 2)

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
                "predicted_object_type": "INCOMPATIBLE",
                "object_type_confidence": None,
                "object_type_status": "UNAVAILABLE",
                "user_selected_study_type": user_selected_study_type,
                "object_type": "INCOMPATIBLE",
                "morphology": None,
                "explanation": "This image does not appear to contain astronomical observation data. No astronomical classification was performed.",
                "model_version": self.model_version_str,
                "inference_time_ms": sem_result.latency_ms,
                "total_triage_ms": round((t1 - t0) * 1000.0, 2),
                "score_interpretation": "Semantic validation failed; image is outside ASTRA astronomical observation domain.",
                "stage_timings_ms": {
                    "semantic_gate": sem_ms,
                    "domain_gate": 0.0,
                    "object_identification": 0.0,
                    "galaxy_morphology": 0.0,
                    "embedding_anomaly": 0.0,
                    "triage_calculation": 0.0,
                    "total_pipeline": round((t1 - t0) * 1000.0, 2)
                }
            }

        # STAGE 2: Execute Domain Gate V2
        t_dom_0 = time.perf_counter()
        v2_result = self.domain_gate.predict(image)
        t_dom_1 = time.perf_counter()
        dom_ms = round((t_dom_1 - t_dom_0) * 1000.0, 2)

        decision_v2 = v2_result.get("decision", "INCOMPATIBLE")

        # Override decision to UNCERTAIN if Semantic Gate was UNCERTAIN but not INCOMPATIBLE
        if sem_result.status == "SEMANTIC_UNCERTAIN" and decision_v2 == "COMPATIBLE":
            decision_v2 = "UNCERTAIN"
            v2_result["decision"] = "UNCERTAIN"

        # Attach semantic gate metadata to domain_validation
        v2_result["semantic_gate_status"] = sem_result.status
        v2_result["semantic_astronomical_score"] = sem_result.astronomical_score
        v2_result["semantic_competing_score"] = sem_result.competing_score
        v2_result["semantic_margin"] = sem_result.semantic_margin
        v2_result["semantic_reason"] = sem_result.reason
        v2_result["inference_time_ms"] = round(v2_result["inference_time_ms"] + sem_result.latency_ms, 2)

        # Rejection occurs ONLY when both Domain Gate V2 and Semantic Gate reject the payload as non-astronomical
        if decision_v2 == "INCOMPATIBLE" and sem_result.status == "SEMANTIC_INCOMPATIBLE":
            t1 = time.perf_counter()
            return {
                "domain_validation": v2_result,
                "predicted_object_type": "INCOMPATIBLE",
                "object_type_confidence": None,
                "object_type_status": "UNAVAILABLE",
                "user_selected_study_type": user_selected_study_type,
                "object_type": "INCOMPATIBLE",
                "morphology": None,
                "explanation": "This image does not appear to contain astronomical observation data. No astronomical classification was performed.",
                "model_version": self.model_version_str,
                "inference_time_ms": v2_result["inference_time_ms"],
                "total_triage_ms": round((t1 - t0) * 1000.0, 2),
                "score_interpretation": "Domain validation failed; image is outside ASTRA astronomical observation domain.",
                "stage_timings_ms": {
                    "semantic_gate": sem_ms,
                    "domain_gate": dom_ms,
                    "object_identification": 0.0,
                    "galaxy_morphology": 0.0,
                    "embedding_anomaly": 0.0,
                    "triage_calculation": 0.0,
                    "total_pipeline": round((t1 - t0) * 1000.0, 2)
                }
            }

        # STAGE 3: Autonomous Scientific Object Identification Router V2
        # Executes independent image structural analysis + OpenCLIP zero-shot similarity (WITHOUT Galaxy Zoo inputs)
        t_obj_0 = time.perf_counter()
        obj_id_res = self.object_id_service.classify_pil_image(
            image,
            filename=filename
        )
        t_obj_1 = time.perf_counter()
        obj_ms = round((t_obj_1 - t_obj_0) * 1000.0, 2)

        pred_obj_type = obj_id_res["predicted_object_type"]
        sim_score = obj_id_res.get("visual_similarity_score")
        obj_margin = obj_id_res.get("object_margin")
        obj_status = obj_id_res["object_type_status"]

        obj_type_info = {
            "label": pred_obj_type,
            "confidence": None,
            "status": obj_status,
            "predicted_object_type": pred_obj_type,
            "visual_similarity_score": sim_score,
            "object_margin": obj_margin,
            "object_confidence": None,
            "object_type_status": obj_status,
            "evidence_quality": obj_id_res.get("evidence_quality"),
            "object_evidence_source": obj_id_res.get("object_evidence_source"),
            "top_class": obj_id_res.get("top_class"),
            "top_score": obj_id_res.get("top_score"),
            "second_best_class": obj_id_res.get("second_best_class"),
            "margin_between_top_and_second": obj_id_res.get("margin_between_top_and_second"),
            "evidence": obj_id_res.get("evidence", [])
        }

        # STAGE 4: Conditional Galaxy Zoo Specialist Execution
        # Galaxy Zoo morphology specialist is invoked IF AND ONLY IF pred_obj_type == "GALAXY"
        if pred_obj_type == "GALAXY":
            t_gz_0 = time.perf_counter()
            triage_output = self.triage_engine.triage_single_image(image)
            t_gz_1 = time.perf_counter()
            gz_ms = round((t_gz_1 - t_gz_0) * 1000.0, 2)
            emb_ms = round(triage_output.get("inference_time_ms", gz_ms), 2)
            calc_ms = round(max(gz_ms - emb_ms, 0.01), 2)

            triage_output["morphology_info"] = {
                "label": triage_output.get("predicted_class"),
                "confidence": triage_output.get("class_confidence"),
                "status": "SUPPORTED"
            }
            triage_output["morphology"] = triage_output.get("predicted_class")
        else:
            # Non-galaxy object target (e.g. AMBIGUOUS_POINT_SOURCE, NEBULA_CANDIDATE, ASTRONOMICAL_SOURCE_AMBIGUOUS, UNKNOWN)
            # Galaxy Zoo morphology specialist is non-applicable and NOT executed.
            gz_ms = 0.0
            emb_ms = 0.0
            calc_ms = 0.0
            triage_output = {
                "predicted_class": None,
                "class_confidence": None,
                "class_probabilities": None,
                "scientific_attributes": None,
                "raw_embedding_distance": None,
                "raw_pred_class_distance": None,
                "nearest_reference_class": None,
                "novelty_score": None,
                "classification_entropy_bits": None,
                "uncertainty_score": None,
                "oddity_score": None,
                "experimental_triage_score": None,
                "priority_level": None,
                "explanation": f"Target identified as {pred_obj_type.replace('_', ' ')} ({obj_status}). Galaxy Zoo morphology specialist was not applied.",
                "model_version": self.model_version_str,
                "inference_time_ms": 0.0,
                "total_triage_ms": 0.0
            }
            triage_output["morphology_info"] = {
                "label": None,
                "confidence": None,
                "status": "NOT_APPLICABLE"
            }
            triage_output["morphology"] = None

        t1 = time.perf_counter()
        total_ms = round((t1 - t0) * 1000.0, 2)

        triage_output["domain_validation"] = v2_result
        triage_output["predicted_object_type"] = pred_obj_type
        triage_output["visual_similarity_score"] = sim_score
        triage_output["object_margin"] = obj_margin
        triage_output["object_confidence"] = None
        triage_output["object_type_confidence"] = None
        triage_output["object_type_status"] = obj_status
        triage_output["user_selected_study_type"] = user_selected_study_type
        triage_output["object_type"] = pred_obj_type
        triage_output["object_type_info"] = obj_type_info
        triage_output["score_interpretation"] = "Experimental prioritization heuristic; not a calibrated anomaly probability."
        triage_output["total_triage_ms"] = total_ms

        triage_output["stage_timings_ms"] = {
            "semantic_gate": sem_ms,
            "domain_gate": dom_ms,
            "object_identification": obj_ms,
            "galaxy_morphology": gz_ms,
            "embedding_anomaly": emb_ms,
            "triage_calculation": calc_ms,
            "total_pipeline": total_ms
        }

        return triage_output

# Global Singleton Instance
ml_service = MLService()
