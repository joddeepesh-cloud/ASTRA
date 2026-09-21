import os
import gc
import time
import json
import numpy as np
import torch

from ml.src.inference import GalaxyZooInference

class ASTRATriageEngine:
    """
    ASTRA Scientific Triage Engine & OOD / Novelty Layer.
    
    Consumes outputs from GalaxyZooInference to compute deterministic novelty,
    uncertainty, and scientific oddity scores, generating a overall experimental
    triage priority score and structured explanation for expert scientific review.
    
    ASTRA identifies observations that are statistically unusual or outside
    the learned distribution and prioritizes them for expert scientific review.
    It does NOT claim scientific discovery or anomaly confirmation.
    """
    def __init__(self, reference_path: str = None, inference_engine: GalaxyZooInference = None):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        if reference_path is None:
            reference_path = os.path.join(project_root, "ml", "artifacts", "triage_reference.json")

        if not os.path.exists(reference_path):
            raise FileNotFoundError(f"Triage reference artifact not found at: {reference_path}")

        with open(reference_path, "r") as f:
            ref_data = json.load(f)

        self.centroids_normalized = {
            k: np.array(v, dtype=np.float32)
            for k, v in ref_data["centroids_normalized"].items()
        }
        self.norm_bounds = ref_data["normalization_bounds"]
        self.priority_thresholds = ref_data["priority_thresholds"]
        del ref_data
        gc.collect()

        if inference_engine is None:
            self.inference_engine = GalaxyZooInference()
        else:
            self.inference_engine = inference_engine

        epoch = getattr(self.inference_engine, "model_epoch", "10")
        self.model_version = f"Epoch {epoch}"

    def triage_single_image(self, image_input) -> dict:
        """
        Perform complete scientific triage on a single image observation.
        
        :param image_input: File path string, PIL Image object, or numpy array.
        :return: Structured dict containing classification, continuous attributes,
                 novelty/uncertainty/oddity scores, triage score, priority level, and explanation.
        """
        t0 = time.perf_counter()

        # 1. Run Galaxy Zoo Model Inference
        inf_res = self.inference_engine.predict_single_image(image_input)

        pred_class = inf_res["predicted_class"]
        confidence = float(inf_res["class_confidence"])
        class_probs = inf_res["class_probabilities"]
        attributes = inf_res["scientific_attributes"]
        embedding = inf_res["embedding"]

        # 2. Embedding Sanity & Normalization
        if np.isnan(embedding).any() or np.isinf(embedding).any():
            raise ValueError("Invalid embedding produced: contains NaN or Infinity values")

        emb_norm = embedding / (np.linalg.norm(embedding) + 1e-12)

        # 3. Compute Cosine Distances to Training Class Centroids
        centroid_dists = {}
        for c_name, c_norm_vec in self.centroids_normalized.items():
            cos_d = 1.0 - float(np.dot(emb_norm, c_norm_vec))
            centroid_dists[c_name] = round(cos_d, 6)

        nearest_class = min(centroid_dists, key=centroid_dists.get)
        raw_nearest_distance = float(centroid_dists[nearest_class])
        raw_pred_distance = float(centroid_dists[pred_class])

        # Primary embedding distance signal: nearest training centroid distance
        raw_embedding_distance = raw_nearest_distance

        # 4. Transform into Bounded Novelty Score [0.0, 1.0] using Training Reference Bounds
        d_min = float(self.norm_bounds["cosine_dist_min"])
        d_max = float(self.norm_bounds["cosine_dist_max"])

        if d_max > d_min:
            novelty_score = float(np.clip((raw_embedding_distance - d_min) / (d_max - d_min), 0.0, 1.0))
        else:
            novelty_score = 0.0

        # 5. Compute Classification Uncertainty Score [0.0, 1.0] and Entropy
        prob_vec = np.array(list(class_probs.values()), dtype=np.float32)
        eps = 1e-12
        entropy_bits = float(-np.sum(prob_vec * np.log2(prob_vec + eps)))
        uncertainty_score = float(np.clip((1.0 - confidence) / 0.75, 0.0, 1.0))

        # 6. Compute Scientific Oddity Score [0.0, 1.0]
        oddity_score = float(np.clip(attributes.get("prob_odd", 0.0), 0.0, 1.0))

        # 7. Compute Experimental Triage Score
        experimental_triage_score = float(np.clip(
            0.35 * novelty_score + 0.35 * uncertainty_score + 0.30 * oddity_score,
            0.0, 1.0
        ))

        # 8. Assign Priority Level
        if experimental_triage_score >= 0.70:
            priority_level = "CRITICAL"
        elif experimental_triage_score >= 0.50:
            priority_level = "HIGH"
        elif experimental_triage_score >= 0.30:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"

        # 9. Generate Deterministic Scientific Explanation
        reasons = []
        if novelty_score >= 0.50:
            reasons.append("Embedding representation is distant from the learned reference distribution.")
        if uncertainty_score >= 0.50:
            reasons.append("Morphology classifier confidence is low, indicating classification ambiguity across classes.")
        if oddity_score >= 0.50:
            reasons.append("Galaxy Zoo-derived oddity attribute is elevated (prob_odd >= 0.50).")

        if len(reasons) == 3:
            explanation = "Observation combines elevated embedding novelty, classification uncertainty, and scientific oddity signals. Strongly prioritize for scientific review."
        elif len(reasons) > 0:
            explanation = " ".join(reasons) + f" Prioritize for scientific review ({priority_level} priority)."
        else:
            explanation = "Observation is consistent with the learned morphology distribution and exhibits low triage priority."

        t1 = time.perf_counter()
        total_triage_ms = round((t1 - t0) * 1000.0, 3)

        # 10. Pathological Sanity Assertions
        assert 0.0 <= novelty_score <= 1.0, f"Novelty score out of bounds: {novelty_score}"
        assert 0.0 <= uncertainty_score <= 1.0, f"Uncertainty score out of bounds: {uncertainty_score}"
        assert 0.0 <= oddity_score <= 1.0, f"Oddity score out of bounds: {oddity_score}"
        assert 0.0 <= experimental_triage_score <= 1.0, f"Triage score out of bounds: {experimental_triage_score}"

        return {
            "predicted_class": pred_class,
            "class_confidence": round(confidence, 4),
            "class_probabilities": class_probs,
            "scientific_attributes": attributes,
            "raw_embedding_distance": round(raw_embedding_distance, 6),
            "raw_pred_class_distance": round(raw_pred_distance, 6),
            "nearest_reference_class": nearest_class,
            "novelty_score": round(novelty_score, 4),
            "classification_entropy_bits": round(entropy_bits, 4),
            "uncertainty_score": round(uncertainty_score, 4),
            "oddity_score": round(oddity_score, 4),
            "experimental_triage_score": round(experimental_triage_score, 4),
            "priority_level": priority_level,
            "explanation": explanation,
            "model_version": f"Epoch {self.model_version}",
            "inference_time_ms": inf_res["inference_time_ms"],
            "total_triage_ms": total_triage_ms
        }
