#!/usr/bin/env python3
"""
ASTRA Phase 12B Real-Data Evidence Fusion Validation Script
Passes the 9 real Phase 12A target evidence bundles through EvidenceFusionEngine.
Saves results to docs/phase12b_real_fusion_results.json.
"""

import os
import io
import json
from PIL import Image

from backend.app.services.ml_service import ml_service
from backend.app.services.evidence.evidence_models import EvidenceBundle
from backend.app.services.evidence.evidence_fusion import evidence_fusion_engine

PHASE12A_RESULTS = "docs/phase12_real_evidence_results.json"
OUTPUT_RESULTS = "docs/phase12b_real_fusion_results.json"

def run_fusion_validation():
    print("====================================================================================================")
    print(" ASTRA PHASE 12B — REAL-DATA EVIDENCE FUSION VALIDATION SWEEP")
    print("====================================================================================================")

    if not os.path.exists(PHASE12A_RESULTS):
        raise FileNotFoundError(f"Phase 12A results file {PHASE12A_RESULTS} not found!")

    with open(PHASE12A_RESULTS, "r") as f:
        p12a_data = json.load(f)

    ml_service.initialize()
    svc = ml_service.object_id_service

    fusion_results = []

    for item in p12a_data.get("results", []):
        tid = item["target_id"]
        ra = item["ra"]
        dec = item["dec"]
        cat = item["category"]
        bundle_dict = item["evidence_bundle"]
        bundle = EvidenceBundle(**bundle_dict)

        # Parse asset_id from target_id (e.g., GALAXY-ZOO-20027 -> 20027)
        img_path = None
        parts = tid.split('-')
        if parts[-1].isdigit():
            possible_path = f"ml/data/processed/galaxy_zoo/images/{parts[-1]}.jpg"
            if os.path.exists(possible_path):
                img_path = possible_path

        if img_path:
            img = Image.open(img_path).convert("RGB")
        else:
            # Point source stub image for stellar candidates
            img = Image.new("RGB", (64, 64), color=(10, 10, 10))

        local_res = svc.classify_pil_image(img, filename=tid)
        fusion_res = evidence_fusion_engine.fuse_evidence(local_res, bundle)

        fusion_dict = fusion_res.model_dump()
        print(f"\nTarget: {tid:<35} | RA: {ra:.6f}, DEC: {dec:.6f}")
        print(f"  Local Image Pred:   {local_res['predicted_object_type']:<28} (CLIP: {local_res.get('top_class')})")
        print(f"  Fused Decision:     {fusion_res.target_decision:<28} [Level: {fusion_res.evidence_level}, Quality: {fusion_res.match_quality}]")
        print(f"  Conflict Status:    {fusion_res.is_conflicting}")
        print(f"  Primary Rationale:  {fusion_res.primary_rationale}")

        fusion_results.append({
            "target_id": tid,
            "ra": ra,
            "dec": dec,
            "category": cat,
            "local_image_result": local_res,
            "fused_evidence_result": fusion_dict
        })

    out_payload = {
        "validation_timestamp": p12a_data.get("sweep_timestamp"),
        "total_targets_evaluated": len(fusion_results),
        "results": fusion_results
    }

    with open(OUTPUT_RESULTS, "w") as f:
        json.dump(out_payload, f, indent=2)

    print(f"\nSaved real-data fusion validation results to {OUTPUT_RESULTS}")

if __name__ == "__main__":
    run_fusion_validation()
