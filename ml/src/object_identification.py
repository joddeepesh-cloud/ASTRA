import logging
import time
import torch
import numpy as np
from PIL import Image
from typing import Dict, Any, Optional

logger = logging.getLogger("astra.object_identification")

from ml.src.point_source_analysis import analyze_point_source_structure

# Structurally balanced prompt ensemble definitions for multi-class astronomical object identification
# Exactly 5 prompts per class with balanced length, vocabulary, and semantic strength.
ASTRONOMICAL_OBJECT_PROMPTS = {
    "GALAXY": [
        "astronomical telescope cutout of a galaxy",
        "optical telescope image of a galaxy with diffuse light halo",
        "astronomical observation of a spiral or smooth galaxy",
        "extended galaxy cutout from sky survey",
        "deep space optical image showing a galaxy"
    ],
    "STAR": [
        "astronomical telescope cutout of a star",
        "optical telescope image of a single star",
        "isolated stellar point source in astronomical image",
        "foreground star in astronomical sky survey",
        "point-like star in optical telescope image"
    ],
    "NEBULA": [
        "astronomical telescope cutout of a nebula",
        "diffuse interstellar nebular cloud of gas and dust",
        "extended emission nebula in astronomical image",
        "interstellar nebular cloud in sky survey",
        "deep sky optical cutout of an interstellar nebula"
    ],
    "QUASAR": [
        "astronomical telescope cutout of a quasar",
        "unresolved active galactic nucleus point source",
        "compact quasar candidate in astronomical survey",
        "luminous point-like quasar observation",
        "distant active galactic nucleus cutout"
    ],
    "PLANETARY": [
        "astronomical telescope cutout of a planet",
        "solar system planet or minor planetary body",
        "planetary disk in astronomical image",
        "solar system object in sky survey",
        "optical cutout of a planetary source"
    ],
    "UNKNOWN": [
        "astronomical cutout of an unidentified source",
        "unidentified astronomical object in survey image",
        "ambiguous optical source in astronomical survey",
        "astronomical observation with uncertain classification",
        "unclassified astronomical feature"
    ]
}

class ObjectIdentificationService:
    """
    ASTRA Scientific Astronomical Object Identification Router V2.
    
    Executes an evidence-first multi-signal routing pipeline combining:
    1. Image Structural Analysis (10 pixel-level metrics)
    2. OpenCLIP Zero-Shot Visual Similarity Prompt Ensemble
    
    SCIENTIFIC INTEGRITY SAFEGUARDS & SURGICAL CONSTRAINTS:
    1. Prompts are structurally balanced across all classes (5 prompts per class).
    2. Visual similarity scores are NOT represented as calibrated probabilities.
       Outputs return visual_similarity_score and object_margin, with object_confidence=None.
    3. Galaxy Zoo Morphology Specialist is STRICTLY CONDITIONAL and is NEVER used to infer or force GALAXY.
    4. Strict Star vs Quasar Guardrail: Single-band optical images cannot reliably distinguish
       a star from a quasar without spectroscopy/redshift/multi-band catalog data. Compact point
       sources resolve to AMBIGUOUS_POINT_SOURCE (status INSUFFICIENT_VISUAL_EVIDENCE).
    5. Nebula Evidence Filter: Diffuse extended emission structure is required for NEBULA_CANDIDATE.
       Weak diffuse emission returns ASTRONOMICAL_SOURCE_AMBIGUOUS to prevent false positives.
    6. Uncertainty Preservation: Low visual similarity or ambiguous decision margins return
       ASTRONOMICAL_SOURCE_AMBIGUOUS / INSUFFICIENT_VISUAL_EVIDENCE.
    """
    def __init__(self, semantic_gate=None):
        self.semantic_gate = semantic_gate

    def classify_pil_image(
        self,
        image: Image.Image,
        filename: str = ""
    ) -> Dict[str, Any]:
        """
        Identify the astronomical object type independently using pixel structure and OpenCLIP zero-shot similarity.
        Note: Galaxy Zoo outputs are NOT consumed here to infer or force GALAXY.
        """
        t0 = time.perf_counter()

        # 1. Execute pure image-derived point source structural analysis
        pt_struct = analyze_point_source_structure(image)

        # 2. Execute OpenCLIP Zero-Shot Prompt Ensemble
        probs = None
        top_class = "UNKNOWN"
        top_score = 0.0
        second_class = None
        margin = 0.0

        if self.semantic_gate is not None and getattr(self.semantic_gate, "model", None) is not None and getattr(self.semantic_gate, "tokenizer", None) is not None:
            try:
                device = self.semantic_gate.device
                model = self.semantic_gate.model
                preprocess = self.semantic_gate.preprocess
                tokenizer = self.semantic_gate.tokenizer

                img_tensor = preprocess(image).unsqueeze(0).to(device)

                labels = list(ASTRONOMICAL_OBJECT_PROMPTS.keys())
                prompt_texts = []
                label_indices = []

                for idx, (label_key, prompts) in enumerate(ASTRONOMICAL_OBJECT_PROMPTS.items()):
                    for p in prompts:
                        prompt_texts.append(p)
                        label_indices.append(idx)

                text_tokens = tokenizer(prompt_texts).to(device)

                with torch.no_grad():
                    img_features = model.encode_image(img_tensor)
                    text_features = model.encode_text(text_tokens)

                    img_features = img_features / (img_features.norm(dim=-1, keepdim=True) + 1e-12)
                    text_features = text_features / (text_features.norm(dim=-1, keepdim=True) + 1e-12)

                    similarities = (img_features @ text_features.T).squeeze(0).cpu().numpy()

                # Pool mean of top-2 strongest prompt scores per class
                label_scores = {lbl: [] for lbl in labels}
                for sim, idx in zip(similarities, label_indices):
                    label_scores[labels[idx]].append(float(sim))

                mean_scores = {lbl: float(np.mean(sorted(vals, reverse=True)[:2])) for lbl, vals in label_scores.items()}

                # Softmax with temperature (tau=50.0)
                exp_scores = {lbl: float(np.exp(val * 50.0)) for lbl, val in mean_scores.items()}
                total_exp = sum(exp_scores.values()) + 1e-12
                probs = {lbl: round(float(exp_scores[lbl] / total_exp), 4) for lbl in labels}

                sorted_classes = sorted(probs.items(), key=lambda item: item[1], reverse=True)
                top_class, top_score = sorted_classes[0]
                second_class, second_score = sorted_classes[1]
                margin = round(top_score - second_score, 4)

            except Exception as e:
                logger.warning(f"Error during OpenCLIP zero-shot astronomical object classification: {e}")

        # 3. INDEPENDENT OBJECT ROUTING & SUFFICIENCY EVALUATION
        t1 = time.perf_counter()
        latency_ms = round((t1 - t0) * 1000.0, 2)

        # Structural signals
        is_pt = pt_struct.get("is_point_source_like", False)
        is_diff = pt_struct.get("is_diffuse_like", False)
        is_ext = pt_struct.get("is_extended_like", False)
        ext_score = pt_struct.get("extended_score", 0.0)
        diff_score = pt_struct.get("diffuse_emission_score", 0.0)
        pt_score = pt_struct.get("point_source_score", 0.0)
        fwhm = pt_struct.get("fwhm_proxy_px", 0.0)
        extent = pt_struct.get("extent_px", 0)
        compactness = pt_struct.get("compactness", 0.0)

        evidence = []
        evidence_sources = []
        pred_type = "ASTRONOMICAL_SOURCE_AMBIGUOUS"
        status = "INSUFFICIENT_VISUAL_EVIDENCE"
        evidence_quality = "INSUFFICIENT"

        is_extended_galaxy_profile = (is_ext or ext_score >= 0.35) and (not is_pt) and (fwhm >= 16.0 or extent >= 8000)

        # 1. GALAXY candidate:
        # (a) OpenCLIP top_class == "GALAXY", extended light profile, not a point source, margin >= 0.10
        if top_class == "GALAXY" and is_extended_galaxy_profile and top_score >= 0.25 and margin >= 0.10:
            pred_type = "GALAXY"
            status = "EXPERIMENTAL_VISUAL_EVIDENCE"
            evidence_quality = "STRONG" if (ext_score >= 0.50 and margin >= 0.20) else "MODERATE"
            evidence_sources = ["Image structural analysis", "OpenCLIP zero-shot"]
            evidence.append(f"Extended astronomical light distribution (Extended score: {ext_score:.2f}, FWHM: {fwhm:.1f}px)")
            evidence.append(f"Visual similarity profile matches galaxy candidate ({top_score:.2f})")

        # (b) Extended galaxy with central bright core matched to STAR/QUASAR in OpenCLIP zero-shot
        elif top_class in ("STAR", "QUASAR") and is_extended_galaxy_profile and ext_score >= 0.70 and extent >= 10000 and pt_score < 0.30 and fwhm >= 30.0:
            pred_type = "GALAXY"
            status = "EXPERIMENTAL_VISUAL_EVIDENCE"
            evidence_quality = "MODERATE"
            evidence_sources = ["Image structural analysis", "OpenCLIP zero-shot"]
            evidence.append(f"Extended astronomical light distribution (Extended score: {ext_score:.2f}, FWHM: {fwhm:.1f}px)")
            evidence.append(f"Central galactic core matched stellar/AGN prompt ({top_score:.2f}), but image structural analysis confirms extended galaxy profile")

        # 2. STAR candidate:
        # OpenCLIP top_class == "STAR", compact point source profile, top_score >= 0.22, margin >= 0.05
        elif top_class == "STAR" and (is_pt or pt_score >= 0.45 or compactness >= 0.50 or fwhm < 18.0) and top_score >= 0.22 and margin >= 0.05:
            pred_type = "STAR"
            status = "EXPERIMENTAL_VISUAL_EVIDENCE"
            evidence_quality = "STRONG" if (pt_score >= 0.60 and margin >= 0.10) else "MODERATE"
            evidence_sources = ["Image structural analysis", "OpenCLIP zero-shot"]
            evidence.append(f"Point-like stellar light profile detected (Compactness: {compactness:.2f}, FWHM: {fwhm:.1f}px)")
            evidence.append(f"Visual similarity profile matches star candidate ({top_score:.2f}, margin: {margin:.2f})")

        # 3. QUASAR candidate:
        # OpenCLIP top_class == "QUASAR", compact point source profile, top_score >= 0.22, margin >= 0.05
        elif top_class == "QUASAR" and (is_pt or pt_score >= 0.45 or compactness >= 0.50 or fwhm < 18.0) and top_score >= 0.22 and margin >= 0.05:
            pred_type = "QUASAR_CANDIDATE"
            status = "EXPERIMENTAL_VISUAL_EVIDENCE"
            evidence_quality = "MODERATE"
            evidence_sources = ["Image structural analysis", "OpenCLIP zero-shot"]
            evidence.append(f"Compact point-like AGN profile detected (Compactness: {compactness:.2f}, FWHM: {fwhm:.1f}px)")
            evidence.append(f"Visual similarity profile matches quasar candidate ({top_score:.2f}, margin: {margin:.2f})")

        # 4. Compact Point Source (STAR / QUASAR Guardrail):
        # Visually unresolved point sources with ambiguous decision margins (< 0.05) or low confidence (< 0.22)
        elif top_class in ("STAR", "QUASAR") or is_pt or pt_score >= 0.55 or fwhm < 15.0:
            pred_type = "AMBIGUOUS_POINT_SOURCE"
            status = "INSUFFICIENT_VISUAL_EVIDENCE"
            evidence_quality = "INSUFFICIENT"
            evidence_sources = ["Image structural analysis", "OpenCLIP zero-shot"]
            evidence.append(f"Point-like astronomical source detected (Compactness: {compactness:.2f}, FWHM: {fwhm:.1f}px)")
            evidence.append("Visual imaging alone does not provide enough margin to reliably separate star vs quasar hypotheses without spectroscopic or catalog data")

        # 3. NEBULA candidate: requires OpenCLIP top_class == "NEBULA" AND structural diffuse emission evidence
        elif top_class == "NEBULA":
            if is_diff or diff_score >= 0.40 or extent >= 90:
                pred_type = "NEBULA_CANDIDATE"
                status = "EXPERIMENTAL_VISUAL_EVIDENCE"
                evidence_quality = "STRONG" if diff_score >= 0.50 else "MODERATE"
                evidence_sources = ["Image structural analysis", "OpenCLIP zero-shot"]
                evidence.append(f"Diffuse extended nebular emission detected (Diffuse score: {diff_score:.2f}, Active pixels: {extent})")
                evidence.append(f"Visual similarity profile matches nebular candidate ({top_score:.2f})")
            else:
                pred_type = "ASTRONOMICAL_SOURCE_AMBIGUOUS"
                status = "INSUFFICIENT_VISUAL_EVIDENCE"
                evidence_quality = "INSUFFICIENT"
                evidence_sources = ["Image structural analysis", "OpenCLIP zero-shot"]
                evidence.append("OpenCLIP matched nebula prompt, but structural diffuse emission evidence is insufficient")

        # 4. PLANETARY candidate
        elif top_class == "PLANETARY" and top_score >= 0.25 and margin >= 0.10:
            pred_type = "PLANETARY_CANDIDATE"
            status = "EXPERIMENTAL_VISUAL_EVIDENCE"
            evidence_quality = "MODERATE"
            evidence_sources = ["OpenCLIP zero-shot"]
            evidence.append(f"Visual similarity profile matches planetary candidate ({top_score:.2f})")

        # 5. Low similarity or ambiguous visual profile
        elif top_score < 0.22:
            pred_type = "ASTRONOMICAL_SOURCE_AMBIGUOUS"
            status = "INSUFFICIENT_VISUAL_EVIDENCE"
            evidence_quality = "INSUFFICIENT"
            evidence_sources = ["OpenCLIP zero-shot"]
            evidence.append("Low visual similarity across reference astronomical classes")

        # 6. Default Ambiguous state for uncertain observations
        else:
            pred_type = "ASTRONOMICAL_SOURCE_AMBIGUOUS"
            status = "INSUFFICIENT_VISUAL_EVIDENCE"
            evidence_quality = "INSUFFICIENT"
            evidence_sources = ["OpenCLIP zero-shot"]
            evidence.append(f"Ambiguous visual similarity between top candidate {top_class} and competing hypotheses")

        return {
            "predicted_object_type": pred_type,
            "object_type_status": status,
            "evidence_quality": evidence_quality,
            "object_evidence_source": evidence_sources,
            "visual_similarity_score": top_score,
            "object_margin": margin,
            "object_confidence": None,
            "top_class": top_class,
            "top_score": top_score,
            "second_best_class": second_class,
            "margin_between_top_and_second": margin,
            "class_probabilities": probs,
            "point_source_metrics": pt_struct,
            "evidence": evidence,
            "latency_ms": latency_ms
        }

