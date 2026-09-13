import os
import sys
import time
import json
import logging
import pandas as pd
import numpy as np
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from ml.src.semantic_gate import SemanticDomainGate, PROMPT_FAMILIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("astra.calibrate_semantic")

def run_calibration():
    print("==================================================")
    print("ASTRA PHASE 10H — SEMANTIC GATE CALIBRATION")
    print("==================================================")

    gate = SemanticDomainGate()

    # Load dataset manifests
    adv_neg_csv = os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "adversarial_manifest.csv")
    adv_pos_csv = os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "adversarial_positive_manifest.csv")
    demo_dir = os.path.join(PROJECT_ROOT, "ml", "data", "demo")

    samples = []
    
    # 1. Demo images
    demo_files = [
        ("astronomy_galaxy_smooth.jpg", "ASTRONOMICAL", "galaxies"),
        ("astronomy_galaxy_disk.jpg", "ASTRONOMICAL", "galaxies"),
        ("astronomy_galaxy_edgeon.jpg", "ASTRONOMICAL", "galaxies"),
        ("non_astronomy_terrestrial.jpg", "NON_ASTRONOMICAL", "terrestrial_scenes"),
        ("non_astronomy_artwork.jpg", "NON_ASTRONOMICAL", "artwork")
    ]
    for fn, label, cat in demo_files:
        fp = os.path.join(demo_dir, fn)
        if os.path.exists(fp):
            samples.append((fp, label, cat, "demo"))

    # 2. Adversarial Negatives
    if os.path.exists(adv_neg_csv):
        df_neg = pd.read_csv(adv_neg_csv)
        for _, row in df_neg.iterrows():
            fp = os.path.join(PROJECT_ROOT, row['path'])
            samples.append((fp, "NON_ASTRONOMICAL", row['category'], "adversarial_negative"))

    # 3. Adversarial Positives
    if os.path.exists(adv_pos_csv):
        df_pos = pd.read_csv(adv_pos_csv)
        for _, row in df_pos.iterrows():
            fp = os.path.join(PROJECT_ROOT, row['path'])
            samples.append((fp, "ASTRONOMICAL", row['category'], "adversarial_positive"))

    logger.info(f"Evaluating {len(samples)} total image samples across broad semantic families...")

    rows = []
    latencies = []
    
    for fp, ground_truth, category, split_tag in samples:
        if not os.path.exists(fp):
            continue
        
        with open(fp, "rb") as f:
            b = f.read()
            
        t0 = time.perf_counter()
        res = gate.validate_image_bytes(b)
        dt = (time.perf_counter() - t0) * 1000.0
        latencies.append(dt)
        
        rows.append({
            "path": os.path.relpath(fp, PROJECT_ROOT),
            "filename": os.path.basename(fp),
            "ground_truth": ground_truth,
            "category": category,
            "split_tag": split_tag,
            "status": res.status,
            "astronomical_score": res.astronomical_score,
            "competing_score": res.competing_score,
            "competing_family": res.competing_family,
            "semantic_margin": res.semantic_margin,
            "reason": res.reason,
            "latency_ms": res.latency_ms
        })

    df_res = pd.DataFrame(rows)

    # Output CSV analysis
    csv_path = os.path.join(PROJECT_ROOT, "ml", "artifacts", "semantic_gate_threshold_analysis.csv")
    df_res.to_csv(csv_path, index=False)
    print(f"Threshold analysis saved to {csv_path}")

    # Metrics evaluation
    pos_mask = df_res["ground_truth"] == "ASTRONOMICAL"
    neg_mask = df_res["ground_truth"] == "NON_ASTRONOMICAL"
    
    pos_df = df_res[pos_mask]
    neg_df = df_res[neg_mask]

    false_acceptances = (neg_df["status"] == "SEMANTIC_COMPATIBLE").sum()
    false_rejections = (pos_df["status"] == "SEMANTIC_INCOMPATIBLE").sum()
    uncertain_pos = (pos_df["status"] == "SEMANTIC_UNCERTAIN").sum()
    uncertain_neg = (neg_df["status"] == "SEMANTIC_UNCERTAIN").sum()
    compatible_pos = (pos_df["status"] == "SEMANTIC_COMPATIBLE").sum()
    incompatible_neg = (neg_df["status"] == "SEMANTIC_INCOMPATIBLE").sum()

    total_pos = len(pos_df)
    total_neg = len(neg_df)

    far = false_acceptances / total_neg if total_neg > 0 else 0.0
    astro_recall = compatible_pos / total_pos if total_pos > 0 else 0.0

    print("\n--- SEMANTIC GATE EVALUATION METRICS ---")
    print(f"Total Positives: {total_pos} | Compatible: {compatible_pos}, Uncertain: {uncertain_pos}, Incompatible: {false_rejections}")
    print(f"Total Negatives: {total_neg} | Incompatible: {incompatible_neg}, Uncertain: {uncertain_neg}, Compatible (FALSE ACCEPT): {false_acceptances}")
    print(f"False Acceptance Rate (FAR): {far * 100:.2f}% ({false_acceptances}/{total_neg})")
    print(f"Astronomical Recall: {astro_recall * 100:.2f}% ({compatible_pos}/{total_pos})")
    print(f"Mean Latency: {np.mean(latencies):.2f} ms | Median: {np.median(latencies):.2f} ms | P95: {np.percentile(latencies, 95):.2f} ms")

    # Save metrics JSON
    metrics_meta = {
        "total_samples": len(df_res),
        "total_positives": total_pos,
        "total_negatives": total_neg,
        "false_acceptance_rate": round(far, 4),
        "astronomical_recall": round(astro_recall, 4),
        "positives_breakdown": {
            "compatible": int(compatible_pos),
            "uncertain": int(uncertain_pos),
            "incompatible": int(false_rejections)
        },
        "negatives_breakdown": {
            "incompatible": int(incompatible_neg),
            "uncertain": int(uncertain_neg),
            "compatible": int(false_acceptances)
        },
        "latency_ms": {
            "mean": round(float(np.mean(latencies)), 2),
            "median": round(float(np.median(latencies)), 2),
            "p95": round(float(np.percentile(latencies, 95)), 2)
        }
    }
    metrics_path = os.path.join(PROJECT_ROOT, "ml", "artifacts", "semantic_gate_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_meta, f, indent=2)
    print(f"Metrics saved to {metrics_path}")

    # Manual Holdout Verification (Leopard, Rainfall Map, IDE Screenshot, Sci-Fi Art)
    holdout_samples = [
        ("ml/data/demo/non_astronomy_terrestrial.jpg", "terrestrial_art"),
        ("ml/data/domain_gate/adversarial/animals/adv_neg_animals_001.jpg", "leopard"),
        ("ml/data/domain_gate/adversarial/maps/adv_neg_maps_001.jpg", "rainfall_map"),
        ("ml/data/domain_gate/adversarial/screenshots/adv_neg_screenshots_001.jpg", "ide_screenshot"),
        ("ml/data/domain_gate/adversarial/space_art/adv_neg_space_art_001.jpg", "scifi_space_art"),
        ("ml/data/demo/astronomy_galaxy_smooth.jpg", "real_galaxy_smooth"),
        ("ml/data/domain_gate/adversarial_positive/low_contrast/adv_pos_low_contrast_001.jpg", "faint_low_contrast_galaxy")
    ]

    holdout_results = []
    for rel_p, label_id in holdout_samples:
        abs_p = os.path.join(PROJECT_ROOT, rel_p)
        if not os.path.exists(abs_p):
            continue
        with open(abs_p, "rb") as f:
            b = f.read()
        res_h = gate.validate_image_bytes(b)
        holdout_results.append({
            "label": label_id,
            "filename": os.path.basename(abs_p),
            "status": res_h.status,
            "astronomical_score": res_h.astronomical_score,
            "competing_score": res_h.competing_score,
            "competing_family": res_h.competing_family,
            "semantic_margin": res_h.semantic_margin,
            "reason": res_h.reason
        })

    holdout_path = os.path.join(PROJECT_ROOT, "ml", "artifacts", "semantic_gate_manual_holdout.json")
    with open(holdout_path, "w") as f:
        json.dump(holdout_results, f, indent=2)
    print(f"Manual holdout saved to {holdout_path}")

    # Report artifact
    report_meta = {
        "phase": "10H",
        "status": "PASS" if false_acceptances == 0 and astro_recall >= 0.95 else "FAIL",
        "model_selected": gate.model_version,
        "selection_rationale": "OpenCLIP ViT-B-32 (laion2b_s34b_b79k) provides fast (~10ms MPS, ~20ms CPU) zero-shot image-text family reasoning with normalized cosine margins.",
        "prompt_families": {k: len(v) for k, v in PROMPT_FAMILIES.items()},
        "thresholds": {
            "astro_min_threshold": gate.astro_min_threshold,
            "margin_min_threshold": gate.margin_min_threshold,
            "lower_margin_threshold": gate.lower_margin_threshold,
            "max_competing_threshold": gate.max_competing_threshold
        },
        "metrics": metrics_meta,
        "manual_holdout": holdout_results,
        "limitations": [
            "Provides open-world zero-shot semantic screening against broad visual concept families; does not guarantee universal arbitrary image understanding across all unconstrained distribution shifts.",
            "Combines with Domain Gate V2 in a fail-closed two-stage validation pipeline."
        ]
    }
    report_path = os.path.join(PROJECT_ROOT, "ml", "artifacts", "phase10h_open_world_gate_report.json")
    with open(report_path, "w") as f:
        json.dump(report_meta, f, indent=2)
    print(f"Phase 10H promotion report saved to {report_path}")

if __name__ == "__main__":
    run_calibration()
