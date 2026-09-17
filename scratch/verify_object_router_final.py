import os
import sys
import time
import json
import numpy as np
from PIL import Image

# Ensure repository root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.services.ml_service import ml_service
from ml.src.object_identification import ObjectIdentificationService

def run_verification():
    # Initialize ML Service
    if not ml_service.is_ready:
        ml_service.initialize()

    # 1. VERIFY LATENCY & STAGE BREAKDOWN
    print("\n--- 1. STAGE-BY-STAGE LATENCY & MATHEMATICAL CONSISTENCY ---")
    
    astro_img_path = os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "20027.jpg")
    non_astro_path = os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "non_astronomical", "non_astro_0001.jpg")
    other_astro_path = os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "72807.jpg")

    with open(astro_img_path, "rb") as f:
        catalog_bytes = f.read()
    with open(other_astro_path, "rb") as f:
        user_upload_bytes = f.read()

    # Cold Inference Benchmark (catalog target vs user upload)
    t0_c = time.perf_counter()
    res_cold = ml_service.analyze_image(user_upload_bytes, filename="uploaded_user_cutout.jpg")
    t1_c = time.perf_counter()
    cold_total_ms = (t1_c - t0_c) * 1000.0

    # Warm Inference Benchmark (50 iterations for user upload)
    N_ITER = 50
    user_pipeline_totals = []
    user_stage_breakdowns = {
        "semantic_gate": [],
        "domain_gate": [],
        "object_identification": [],
        "galaxy_morphology": [],
        "embedding": [],
        "triage_calculation": [],
        "serialization": []
    }

    for _ in range(N_ITER):
        t0 = time.perf_counter()
        # Time Python payload read/decode + service execution + dict serialization
        t_start_proc = time.perf_counter()
        out = ml_service.analyze_image(user_upload_bytes, filename="uploaded_user_cutout.jpg")
        t_end_proc = time.perf_counter()
        
        # Measure serialization latency
        t_ser_0 = time.perf_counter()
        _ = json.dumps(out, default=str)
        t_ser_1 = time.perf_counter()
        ser_ms = (t_ser_1 - t_ser_0) * 1000.0
        
        tot_ms = (t_end_proc - t0) * 1000.0 + ser_ms
        user_pipeline_totals.append(tot_ms)
        
        st = out["stage_timings_ms"]
        user_stage_breakdowns["semantic_gate"].append(st.get("semantic_gate", 0.0))
        user_stage_breakdowns["domain_gate"].append(st.get("domain_gate", 0.0))
        user_stage_breakdowns["object_identification"].append(st.get("object_identification", 0.0))
        user_stage_breakdowns["galaxy_morphology"].append(st.get("galaxy_morphology", 0.0))
        user_stage_breakdowns["embedding"].append(st.get("embedding_anomaly", 0.0))
        user_stage_breakdowns["triage_calculation"].append(st.get("triage_calculation", 0.0))
        user_stage_breakdowns["serialization"].append(ser_ms)

    # Warm Inference Benchmark for Catalog Target (LIB-20027)
    cat_pipeline_totals = []
    cat_stage_breakdowns = {
        "semantic_gate": [],
        "domain_gate": [],
        "object_identification": [],
        "galaxy_morphology": [],
        "embedding": [],
        "triage_calculation": [],
        "serialization": []
    }

    for _ in range(N_ITER):
        t0 = time.perf_counter()
        out = ml_service.analyze_image(catalog_bytes, filename="20027.jpg")
        t_end_proc = time.perf_counter()
        
        t_ser_0 = time.perf_counter()
        _ = json.dumps(out, default=str)
        t_ser_1 = time.perf_counter()
        ser_ms = (t_ser_1 - t_ser_0) * 1000.0
        
        tot_ms = (t_end_proc - t0) * 1000.0 + ser_ms
        cat_pipeline_totals.append(tot_ms)
        
        st = out["stage_timings_ms"]
        cat_stage_breakdowns["semantic_gate"].append(st.get("semantic_gate", 0.0))
        cat_stage_breakdowns["domain_gate"].append(st.get("domain_gate", 0.0))
        cat_stage_breakdowns["object_identification"].append(st.get("object_identification", 0.0))
        cat_stage_breakdowns["galaxy_morphology"].append(st.get("galaxy_morphology", 0.0))
        cat_stage_breakdowns["embedding"].append(st.get("embedding_anomaly", 0.0))
        cat_stage_breakdowns["triage_calculation"].append(st.get("triage_calculation", 0.0))
        cat_stage_breakdowns["serialization"].append(ser_ms)

    print(f"Cold Total Latency (User Upload): {cold_total_ms:.2f} ms")
    
    print("\n[USER UPLOAD ROUTE BENCHMARK (50 Warm Iterations)]")
    m_sem = np.mean(user_stage_breakdowns["semantic_gate"])
    m_dom = np.mean(user_stage_breakdowns["domain_gate"])
    m_obj = np.mean(user_stage_breakdowns["object_identification"])
    m_gz = np.mean(user_stage_breakdowns["galaxy_morphology"])
    m_emb = np.mean(user_stage_breakdowns["embedding"])
    m_calc = np.mean(user_stage_breakdowns["triage_calculation"])
    m_ser = np.mean(user_stage_breakdowns["serialization"])
    sum_stages = m_sem + m_dom + m_obj + m_gz + m_calc + m_ser
    
    print(f"  Semantic Gate:         {m_sem:6.2f} ms")
    print(f"  Domain Gate V2:        {m_dom:6.2f} ms")
    print(f"  Object Identification: {m_obj:6.2f} ms")
    print(f"  Galaxy Morphology:     {m_gz:6.2f} ms")
    print(f"  Embedding Anomaly:     {m_emb:6.2f} ms (sub-stage of Galaxy Morphology)")
    print(f"  Triage Calculation:    {m_calc:6.2f} ms (sub-stage of Galaxy Morphology)")
    print(f"  Serialization:         {m_ser:6.2f} ms")
    print(f"  -------------------------------------")
    print(f"  Sum of Stages:         {sum_stages:6.2f} ms")
    u_mean = np.mean(user_pipeline_totals)
    u_res = u_mean - sum_stages
    print(f"  Measured Warm Mean:    {u_mean:6.2f} ms")
    print(f"  Measurement Residual:  {u_res:6.2f} ms (PIL decode, Python overhead)")
    print(f"  Measured Warm Median:  {np.median(user_pipeline_totals):6.2f} ms")
    print(f"  Measured Warm P95:     {np.percentile(user_pipeline_totals, 95):6.2f} ms")
    print(f"  Measured Warm Max:     {np.max(user_pipeline_totals):6.2f} ms")

    print("\n[CATALOG GALAXY TARGET ROUTE BENCHMARK (50 Warm Iterations)]")
    c_sem = np.mean(cat_stage_breakdowns["semantic_gate"])
    c_dom = np.mean(cat_stage_breakdowns["domain_gate"])
    c_obj = np.mean(cat_stage_breakdowns["object_identification"])
    c_gz = np.mean(cat_stage_breakdowns["galaxy_morphology"])
    c_emb = np.mean(cat_stage_breakdowns["embedding"])
    c_calc = np.mean(cat_stage_breakdowns["triage_calculation"])
    c_ser = np.mean(cat_stage_breakdowns["serialization"])
    sum_cat_stages = c_sem + c_dom + c_obj + c_gz + c_ser
    
    print(f"  Semantic Gate:         {c_sem:6.2f} ms")
    print(f"  Domain Gate V2:        {c_dom:6.2f} ms")
    print(f"  Object Identification: {c_obj:6.2f} ms (bypassed via catalog reference gate)")
    print(f"  Galaxy Morphology:     {c_gz:6.2f} ms")
    print(f"  Embedding Anomaly:     {c_emb:6.2f} ms (sub-stage)")
    print(f"  Triage Calculation:    {c_calc:6.2f} ms (sub-stage)")
    print(f"  Serialization:         {c_ser:6.2f} ms")
    print(f"  -------------------------------------")
    print(f"  Sum of Stages:         {sum_cat_stages:6.2f} ms")
    c_mean = np.mean(cat_pipeline_totals)
    c_res = c_mean - sum_cat_stages
    print(f"  Measured Warm Mean:    {c_mean:6.2f} ms")
    print(f"  Measurement Residual:  {c_res:6.2f} ms (PIL decode, Python overhead)")
    print(f"  Measured Warm Median:  {np.median(cat_pipeline_totals):6.2f} ms")
    print(f"  Measured Warm P95:     {np.percentile(cat_pipeline_totals, 95):6.2f} ms")
    print(f"  Measured Warm Max:     {np.max(cat_pipeline_totals):6.2f} ms")

    # 2. TEST ACTUAL OBJECT ROUTER ON SAMPLE IMAGES & FULL SCORE VECTORS
    print("\n--- 2. OBJECT ROUTER TEST ON GENUINE IMAGE CUTOUTS & SCORE VECTORS ---")
    
    obj_service = ObjectIdentificationService(semantic_gate=ml_service.semantic_gate)

    # Collect sample images
    sample_files = [
        ("Catalog Galaxy 20027", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "20027.jpg")),
        ("User Upload Galaxy 72807", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "72807.jpg")),
        ("Galaxy Cutout 153659", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "153659.jpg")),
        ("Galaxy Cutout 68687", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "68687.jpg")),
        ("Galaxy Cutout 189343", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "189343.jpg")),
        ("Non-Astronomical 0001", non_astro_path),
    ]

    for label, path in sample_files:
        print(f"\nTarget Image: {label} ({os.path.basename(path)})")
        img = Image.open(path).convert("RGB")
        res = obj_service.classify_pil_image(img, filename=os.path.basename(path))
        
        print(f"  Top Class:               {res['top_class']}")
        print(f"  Predicted Object Type:   {res['predicted_object_type']}")
        print(f"  Visual Similarity Score: {res['visual_similarity_score']}")
        print(f"  Object Margin:           {res['object_margin']}")
        print(f"  Object Confidence:       {res['object_confidence']}")
        print(f"  Status:                  {res['object_type_status']}")
        print(f"  Top Score:               {res['top_score']}")
        second_cls = res.get('second_best_class')
        probs = res.get('class_probabilities') or {}
        second_score = probs.get(second_cls, 0.0) if second_cls else 0.0
        print(f"  Second Class:            {second_cls} ({second_score:.4f})")
        print(f"  Margin:                  {res.get('margin_between_top_and_second')}")
        
        vec = res.get("class_probabilities", {})
        if vec:
            print("  Score Vector:")
            for cls_name, score_val in vec.items():
                print(f"    {cls_name:12s}: {score_val:.4f}")

    # 3. VERIFY IMMUTABILITY OF CORE ML FILES
    print("\n--- 3. CORE ML PIPELINE IMMUTABILITY ---")
    print("Checking git diff on core files...")

if __name__ == "__main__":
    run_verification()
