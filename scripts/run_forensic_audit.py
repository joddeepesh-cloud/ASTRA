#!/usr/bin/env python3
"""
ASTRA Object Identification Forensic Audit — Diagnostic Script ONLY
This script performs a non-modifying diagnostic sweep of local repository images.
It compares:
1. Raw OpenCLIP zero-shot ranking (before any rules/guardrails/overrides)
2. Galaxy Zoo specialist prediction & confidence
3. Image structural metrics
4. Current production pipeline final decision
5. Simulated pipeline decision WITHOUT Galaxy Zoo override / Rule A

DO NOT USE TO MODIFY BEHAVIOR. DIAGNOSTIC ONLY.
"""

import os
import glob
import torch
import numpy as np
from PIL import Image

from backend.app.services.ml_service import ml_service
from ml.src.point_source_analysis import analyze_point_source_structure
from ml.src.object_identification import ASTRONOMICAL_OBJECT_PROMPTS

def run_audit():
    ml_service.initialize()

    # Find sample images from various repository directories
    image_samples = []

    # Galaxies from GZ2 dataset
    gz_images = sorted(glob.glob("ml/data/processed/galaxy_zoo/images/*.jpg"))[:5]
    for path in gz_images:
        image_samples.append(("GALAXY (GZ2)", path))

    # Stellar fields
    stellar_images = sorted(glob.glob("ml/data/domain_gate/adversarial_positive/stellar_fields/*.jpg"))[:5]
    for path in stellar_images:
        image_samples.append(("STELLAR_FIELD", path))

    # Nebular fields
    nebular_images = sorted(glob.glob("ml/data/domain_gate/adversarial_positive/nebular_fields/*.jpg"))[:5]
    for path in nebular_images:
        image_samples.append(("NEBULAR_FIELD", path))

    # Survey cutouts
    survey_images = sorted(glob.glob("ml/data/domain_gate/adversarial_positive/survey_cutouts/*.jpg"))[:5]
    for path in survey_images:
        image_samples.append(("SURVEY_CUTOUT", path))

    # Demo images
    demo_images = sorted(glob.glob("ml/data/demo/*.jpg"))
    for path in demo_images:
        image_samples.append(("DEMO_IMAGE", path))

    # Non-astronomical images
    non_astro = sorted(glob.glob("ml/data/domain_gate/non_astronomical/*.jpg"))[:3]
    for path in non_astro:
        image_samples.append(("NON_ASTRONOMICAL", path))

    print("================================================================================")
    print(" ASTRA OBJECT IDENTIFICATION FORENSIC AUDIT — DIAGNOSTIC SWEEP")
    print("================================================================================")

    audit_records = []

    for category, path in image_samples:
        fname = os.path.basename(path)
        img = Image.open(path).convert("RGB")

        # 1. Run Domain Gate Stage 1 & Stage 2
        sem_res = ml_service.semantic_gate.validate_pil_image(img)
        v2_res = ml_service.domain_gate.predict(img) if sem_res.status == "SEMANTIC_COMPATIBLE" else {"decision": "INCOMPATIBLE"}
        is_compatible = (sem_res.status == "SEMANTIC_COMPATIBLE" and v2_res.get("decision") == "COMPATIBLE")

        # 2. Extract Raw OpenCLIP Zero-Shot Ranking (BEFORE ANY RULES / OVERRIDES)
        raw_clip_scores = {}
        if ml_service.semantic_gate and ml_service.semantic_gate.model:
            device = ml_service.semantic_gate.device
            model = ml_service.semantic_gate.model
            preprocess = ml_service.semantic_gate.preprocess
            tokenizer = ml_service.semantic_gate.tokenizer

            img_tensor = preprocess(img).unsqueeze(0).to(device)

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

            label_scores = {lbl: [] for lbl in labels}
            for sim, idx in zip(similarities, label_indices):
                label_scores[labels[idx]].append(float(sim))

            mean_scores = {lbl: float(np.mean(sorted(vals, reverse=True)[:2])) for lbl, vals in label_scores.items()}
            exp_scores = {lbl: float(np.exp(val * 50.0)) for lbl, val in mean_scores.items()}
            total_exp = sum(exp_scores.values()) + 1e-12
            raw_clip_scores = {lbl: round(float(exp_scores[lbl] / total_exp), 4) for lbl in labels}

        sorted_raw_clip = sorted(raw_clip_scores.items(), key=lambda x: x[1], reverse=True) if raw_clip_scores else []
        raw_top_class = sorted_raw_clip[0][0] if sorted_raw_clip else "N/A"
        raw_top_score = sorted_raw_clip[0][1] if sorted_raw_clip else 0.0

        # 3. Galaxy Zoo Output
        gz_out = ml_service.triage_engine.triage_single_image(img) if is_compatible else {}
        gz_pred = gz_out.get("predicted_class", "N/A")
        gz_conf = gz_out.get("class_confidence", 0.0)

        # 4. Image Structure
        pt_struct = analyze_point_source_structure(img)

        # 5. Full Production Decision
        prod_res = ml_service.object_id_service.classify_pil_image(img, filename=fname, galaxy_zoo_output=gz_out) if is_compatible else {"predicted_object_type": "INCOMPATIBLE", "object_type_status": "UNAVAILABLE"}
        prod_final_class = prod_res.get("predicted_object_type")
        prod_status = prod_res.get("object_type_status")

        # 6. Simulated Decision WITHOUT Galaxy Zoo Override (Rule A bypassed)
        sim_res = ml_service.object_id_service.classify_pil_image(img, filename=fname, galaxy_zoo_output=None) if is_compatible else {"predicted_object_type": "INCOMPATIBLE"}
        sim_final_class = sim_res.get("predicted_object_type")

        # Identify if Rule A forced GALAXY
        rule_a_forced_galaxy = bool(is_compatible and gz_pred in ["SPIRAL", "SMOOTH", "FEATURED_DISK", "EDGE_ON"] and prod_final_class == "GALAXY" and raw_top_class != "GALAXY")

        print(f"\n[{category}] File: {fname}")
        print(f"  Domain Compatible:   {is_compatible}")
        print(f"  Raw OpenCLIP Top-1:  {raw_top_class} ({raw_top_score:.4f})")
        print(f"  Raw Ranking:         {sorted_raw_clip[:3]}")
        print(f"  Galaxy Zoo Pred:     {gz_pred} ({f'{gz_conf*100:.1f}%' if gz_conf else 'N/A'})")
        print(f"  Structure Metrics:   Conc={pt_struct['concentration_ratio']}, Compact={pt_struct['compactness']}, ExtScore={pt_struct['extended_score']}, DiffScore={pt_struct['diffuse_emission_score']}")
        print(f"  CURRENT PRODUCTION:  {prod_final_class} ({prod_status})")
        print(f"  SIMULATED (NO GZ):   {sim_final_class}")
        print(f"  Rule A Forced Galaxy:{' *** YES (OVERRODE CLIP) ***' if rule_a_forced_galaxy else ' NO'}")

        audit_records.append({
            "category": category,
            "filename": fname,
            "compatible": is_compatible,
            "raw_top_class": raw_top_class,
            "raw_top_score": raw_top_score,
            "raw_ranking": sorted_raw_clip,
            "gz_pred": gz_pred,
            "gz_conf": gz_conf,
            "prod_final": prod_final_class,
            "sim_final": sim_final_class,
            "forced": rule_a_forced_galaxy
        })

    print("\n================================================================================")
    print(" AUDIT SUMMARY TABLE")
    print("================================================================================")
    print(f"{'CATEGORY':<20} | {'FILENAME':<30} | {'RAW CLIP TOP':<15} | {'GZ PRED':<15} | {'PROD FINAL':<25} | {'FORCED GALAXY?'}")
    print("-" * 115)
    for r in audit_records:
        print(f"{r['category']:<20} | {r['filename']:<30} | {r['raw_top_class']:<15} | {r['gz_pred']:<15} | {r['prod_final']:<25} | {'YES ***' if r['forced'] else 'NO'}")

if __name__ == "__main__":
    run_audit()
