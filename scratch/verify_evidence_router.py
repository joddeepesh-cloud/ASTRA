#!/usr/bin/env python3
"""
ASTRA Evidence-First Object Router V2 — Verification & Latency Benchmark Script
Tests real repository images across galaxy, star/point-source, nebula, survey cutouts, and non-astronomical categories.
Measures warm pipeline latency and outputs structured results table.
"""

import os
import io
import glob
import time
import numpy as np
from PIL import Image

from backend.app.services.ml_service import ml_service

def run_verification():
    print("================================================================================")
    print(" INITIALIZING ML SERVICE & EXECUTING WARMUP")
    print("================================================================================")
    ml_service.initialize()

    # Define image test buckets from repository
    test_buckets = {
        "GALAXY": sorted(glob.glob("ml/data/processed/galaxy_zoo/images/*.jpg"))[:5],
        "POINT_SOURCE / STAR": sorted(glob.glob("ml/data/domain_gate/adversarial_positive/stellar_fields/*.jpg"))[:5],
        "NEBULA": sorted(glob.glob("ml/data/domain_gate/adversarial_positive/nebular_fields/*.jpg"))[:5],
        "SURVEY CUTOUT / QUASAR CANDIDATE": sorted(glob.glob("ml/data/domain_gate/adversarial_positive/survey_cutouts/*.jpg"))[:5],
        "NON-ASTRONOMICAL": sorted(glob.glob("ml/data/domain_gate/non_astronomical/*.jpg"))[:3]
    }

    # Generate synthetic compact point source to verify AMBIGUOUS_POINT_SOURCE guardrail
    pt_img = Image.new("L", (64, 64), color=10)
    pt_arr = np.array(pt_img, dtype=np.float32)
    y, x = np.indices((64, 64))
    r2 = (x - 32)**2 + (y - 32)**2
    pt_arr += 230.0 * np.exp(-r2 / (2 * 1.5**2))  # Compact Gaussian FWHM ~ 3.5px
    pt_pil = Image.fromarray(np.clip(pt_arr, 0, 255).astype(np.uint8)).convert("RGB")
    pt_bytes = io.BytesIO()
    pt_pil.save(pt_bytes, format="JPEG")

    print("\n--- SYNTHETIC TEST: COMPACT POINT SOURCE CUTOUT ---")
    pt_res = ml_service.object_id_service.classify_pil_image(pt_pil, filename="compact_star_or_quasar.jpg")
    print(f"Predicted Object Type: {pt_res['predicted_object_type']}")
    print(f"Object Type Status:    {pt_res['object_type_status']}")
    print(f"Evidence Quality:      {pt_res['evidence_quality']}")
    print(f"Evidence Notes:        {pt_res['evidence']}")
    assert pt_res['predicted_object_type'] == "AMBIGUOUS_POINT_SOURCE"
    assert pt_res['object_type_status'] == "INSUFFICIENT_VISUAL_EVIDENCE"
    print("[PASS] Compact point source correctly resolved to AMBIGUOUS_POINT_SOURCE (INSUFFICIENT_VISUAL_EVIDENCE).")

    all_latencies = []
    results = []

    print("\n================================================================================")
    print(" RUNNING REAL IMAGE EVIDENCE ROUTER VERIFICATION")
    print("================================================================================")

    for category, file_paths in test_buckets.items():
        print(f"\n--- CATEGORY: {category} ({len(file_paths)} files) ---")
        for path in file_paths:
            fname = os.path.basename(path)
            with open(path, "rb") as f:
                img_bytes = f.read()

            t0 = time.perf_counter()
            out = ml_service.analyze_image(img_bytes, filename=fname)
            t1 = time.perf_counter()
            latency_ms = (t1 - t0) * 1000.0
            all_latencies.append(latency_ms)

            dom_dec = out.get("domain_validation", {}).get("decision")
            pred_obj = out.get("predicted_object_type")
            status = out.get("object_type_status")
            obj_info = out.get("object_type_info") or {}
            quality = obj_info.get("evidence_quality", "N/A")
            sim_score = out.get("visual_similarity_score")
            margin = out.get("object_margin")
            gz_class = out.get("predicted_class")
            gz_conf = out.get("class_confidence")
            evidence = obj_info.get("evidence", [])

            pt_metrics = obj_info.get("point_source_metrics") or {}

            print(f"File:                   {fname}")
            print(f"Domain Decision:        {dom_dec}")
            print(f"Predicted Object:       {pred_obj}")
            print(f"Status / Quality:       {status} ({quality})")
            print(f"Visual Similarity:      {sim_score if sim_score is not None else 'N/A'}")
            print(f"Decision Margin:        +{margin:.4f}" if margin is not None else "Decision Margin:        N/A")
            print(f"Galaxy Zoo Specialist:  {gz_class} ({f'{gz_conf*100:.1f}%' if gz_conf else 'N/A'})")
            if pt_metrics:
                print(f"Structural Metrics:     Compactness={pt_metrics.get('compactness')}, Conc={pt_metrics.get('concentration_ratio')}, FWHM={pt_metrics.get('fwhm_proxy_px')}px, Ext={pt_metrics.get('extent_px')}px, ExtScore={pt_metrics.get('extended_score')}, DiffScore={pt_metrics.get('diffuse_emission_score')}")
            print(f"Evidence Notes:         {'; '.join(evidence[:2]) if evidence else 'N/A'}")
            print(f"Latency:                {latency_ms:.2f} ms")
            print("-" * 60)

            results.append({
                "category": category,
                "filename": fname,
                "domain_decision": dom_dec,
                "predicted_object": pred_obj,
                "status": status,
                "quality": quality,
                "sim_score": sim_score,
                "margin": margin,
                "gz_class": gz_class,
                "latency_ms": latency_ms
            })

    # Benchmark Warm Inference (100 passes on sample galaxy image)
    print("\n================================================================================")
    print(" BENCHMARKING WARM INFERENCE PERFORMANCE (100 PASSES)")
    print("================================================================================")
    sample_path = test_buckets["GALAXY"][0]
    with open(sample_path, "rb") as f:
        sample_bytes = f.read()

    warm_latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        _ = ml_service.analyze_image(sample_bytes, filename="benchmark.jpg")
        t1 = time.perf_counter()
        warm_latencies.append((t1 - t0) * 1000.0)

    mean_lat = np.mean(warm_latencies)
    median_lat = np.median(warm_latencies)
    p95_lat = np.percentile(warm_latencies, 95)
    max_lat = np.max(warm_latencies)

    print(f"Warm Inference Latency Statistics (N=100):")
    print(f"  Mean:   {mean_lat:.2f} ms")
    print(f"  Median: {median_lat:.2f} ms")
    print(f"  P95:    {p95_lat:.2f} ms")
    print(f"  Max:    {max_lat:.2f} ms")
    print("================================================================================")

    assert p95_lat < 250.0, f"Target latency < 250 ms violated! P95 is {p95_lat:.2f} ms"
    print("VERIFICATION COMPLETE & LATENCY TARGET MET (< 250 ms P95).")

if __name__ == "__main__":
    run_verification()
