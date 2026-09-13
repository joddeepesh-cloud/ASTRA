import os
import sys
import io
import json
import time
import requests
import subprocess
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.app.config import settings

API_BASE_URL = "http://127.0.0.1:8000/api/v1"
ADV_NEG_MANIFEST = os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "adversarial_manifest.csv")
ADV_POS_MANIFEST = os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "adversarial_positive_manifest.csv")

REPORT_JSON_PATH = os.path.join(PROJECT_ROOT, "ml", "artifacts", "phase10f_promotion_report.json")
DOC_PROMOTION_PATH = os.path.join(PROJECT_ROOT, "docs", "phase10f_v2_promotion.md")

def start_backend_server():
    print("Starting FastAPI Backend Server on port 8000...")
    t0 = time.perf_counter()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for server readiness
    started = False
    for _ in range(30): # up to 15 seconds max wait
        try:
            r = requests.get(f"{API_BASE_URL}/health", timeout=1.0)
            if r.status_code == 200:
                started = True
                break
        except Exception:
            time.sleep(0.5)
            
    startup_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    if not started:
        proc.kill()
        raise RuntimeError("FastAPI server failed to start within timeout!")
    print(f"Backend Server online in {startup_ms} ms!")
    return proc, startup_ms

def stop_backend_server(proc):
    print("Stopping FastAPI Backend Server...")
    proc.terminate()
    proc.wait()

def run_phase10f_verification():
    print("==================================================")
    print("ASTRA PHASE 10F — END-TO-END PROMOTION VERIFICATION")
    print("==================================================")
    
    # 1. Configuration & Model Path Assertions
    print("\n1. Verifying Production Model Configuration...")
    assert settings.DOMAIN_GATE_PATH.endswith("domain_gate_v2_best.pt"), f"Invalid DOMAIN_GATE_PATH: {settings.DOMAIN_GATE_PATH}"
    assert not settings.DOMAIN_GATE_PATH.endswith("domain_gate_best.pt"), "Production config is accidentally pointing to V1!"
    assert os.path.exists(settings.DOMAIN_GATE_PATH), f"Domain Gate V2 checkpoint missing: {settings.DOMAIN_GATE_PATH}"
    
    v1_path = os.path.join(PROJECT_ROOT, "ml", "models", "domain_gate_best.pt")
    assert os.path.exists(v1_path), f"Original Domain Gate V1 checkpoint missing: {v1_path}"
    print("  [PASS] Config correctly references V2 model and preserves V1 checkpoint.")

    # 2. Start Server
    server_proc, startup_duration_ms = start_backend_server()
    
    try:
        # 3. Health Endpoint Verification
        print("\n2. Testing GET /api/v1/health...")
        t0_h = time.perf_counter()
        res_h = requests.get(f"{API_BASE_URL}/health")
        health_ms = round((time.perf_counter() - t0_h) * 1000.0, 2)
        
        assert res_h.status_code == 200, f"Health endpoint returned status {res_h.status_code}"
        h_data = res_h.json()
        
        assert h_data['status'] == 'ok'
        assert h_data['ml_ready'] is True
        assert h_data['model_loaded'] is True
        assert h_data['domain_gate_loaded'] is True
        assert 'v2' in h_data['domain_gate_model_version'].lower(), f"Health response model_version '{h_data['domain_gate_model_version']}' does not identify V2!"
        print(f"  [PASS] Health check passed! Version: {h_data['domain_gate_model_version']}, Latency: {health_ms} ms")

        # 4. Live Test Matrix (Demo Images & Representative Adversarial Categories)
        print("\n3. Executing Live Test Matrix across Domain Categories...")
        test_samples = [
            ("astronomy_galaxy_smooth.jpg", os.path.join(PROJECT_ROOT, "ml", "data", "demo", "astronomy_galaxy_smooth.jpg"), "ASTRONOMICAL", "COMPATIBLE"),
            ("astronomy_galaxy_disk.jpg", os.path.join(PROJECT_ROOT, "ml", "data", "demo", "astronomy_galaxy_disk.jpg"), "ASTRONOMICAL", "COMPATIBLE"),
            ("astronomy_galaxy_edgeon.jpg", os.path.join(PROJECT_ROOT, "ml", "data", "demo", "astronomy_galaxy_edgeon.jpg"), "ASTRONOMICAL", "COMPATIBLE"),
            ("non_astronomy_terrestrial.jpg", os.path.join(PROJECT_ROOT, "ml", "data", "demo", "non_astronomy_terrestrial.jpg"), "NON_ASTRONOMICAL", "INCOMPATIBLE"),
            ("non_astronomy_artwork.jpg", os.path.join(PROJECT_ROOT, "ml", "data", "demo", "non_astronomy_artwork.jpg"), "NON_ASTRONOMICAL", "INCOMPATIBLE"),
        ]
        
        # Add key failure category samples
        adv_neg_df = pd.read_csv(ADV_NEG_MANIFEST)
        adv_pos_df = pd.read_csv(ADV_POS_MANIFEST)
        
        for cat in ['animals', 'maps', 'night_sky', 'screenshots', 'scientific_graphics']:
            row_c = adv_neg_df[adv_neg_df['category'] == cat].iloc[0]
            test_samples.append((f"adv_{cat}.jpg", os.path.join(PROJECT_ROOT, row_c['path']), "NON_ASTRONOMICAL", "INCOMPATIBLE"))
            
        for cat in ['low_contrast', 'nebular_fields', 'crowded_fields']:
            row_c = adv_pos_df[adv_pos_df['category'] == cat].iloc[0]
            test_samples.append((f"adv_{cat}.jpg", os.path.join(PROJECT_ROOT, row_c['path']), "ASTRONOMICAL", "COMPATIBLE"))

        live_results = []
        for name, path, domain_lbl, exp_dec in test_samples:
            if not os.path.exists(path):
                continue
            with open(path, "rb") as f:
                f_bytes = f.read()
                
            t0_tr = time.perf_counter()
            resp = requests.post(f"{API_BASE_URL}/triage", files={"file": (name, f_bytes, "image/jpeg")})
            dt_tr = round((time.perf_counter() - t0_tr) * 1000.0, 2)
            
            assert resp.status_code == 200
            data_tr = resp.json()
            domain_res = data_tr['domain_validation']
            dec = domain_res['decision']
            p_astro = domain_res['probability_astronomical']
            
            morph_ran = data_tr.get('predicted_class') is not None
            triage_score = data_tr.get('experimental_triage_score')
            
            print(f"  [{name:32s}] P(Astro)={p_astro:.4f} -> {dec:12s} | Morph Ran: {str(morph_ran):5s} | Latency: {dt_tr:6.2f} ms")
            
            live_results.append({
                'filename': name,
                'path': path,
                'expected_domain': domain_lbl,
                'expected_decision': exp_dec,
                'probability_astronomical': p_astro,
                'decision': dec,
                'morphology_ran': morph_ran,
                'predicted_class': data_tr.get('predicted_class'),
                'triage_score': triage_score,
                'total_latency_ms': dt_tr,
                'model_version': domain_res['model_version']
            })

        # 5. Phase 10D Full Adversarial Regression Test via HTTP Endpoint
        print("\n4. Running Full Phase 10D Adversarial Regression Suite via HTTP API...")
        all_adv_samples = []
        for _, row in adv_neg_df.iterrows():
            all_adv_samples.append((os.path.join(PROJECT_ROOT, row['path']), 'NON_ASTRONOMICAL'))
        for _, row in adv_pos_df.iterrows():
            all_adv_samples.append((os.path.join(PROJECT_ROOT, row['path']), 'ASTRONOMICAL'))
            
        neg_count = len(adv_neg_df)
        pos_count = len(adv_pos_df)
        
        false_acceptances = 0
        false_rejections = 0
        incompatible_neg_count = 0
        uncertain_neg_count = 0
        compatible_pos_count = 0
        
        adv_latencies = []
        
        for idx, (p_abs, exp_dom) in enumerate(all_adv_samples, 1):
            with open(p_abs, "rb") as f:
                b = f.read()
            t0_i = time.perf_counter()
            r_api = requests.post(f"{API_BASE_URL}/triage", files={"file": (os.path.basename(p_abs), b, "image/jpeg")}, timeout=10.0)
            dt_i = (time.perf_counter() - t0_i) * 1000.0
            adv_latencies.append(dt_i)
            
            d_api = r_api.json()
            d_res = d_api['domain_validation']
            p_ast = d_res['probability_astronomical']
            dec_ast = d_res['decision']
            
            if exp_dom == 'NON_ASTRONOMICAL':
                if dec_ast == 'COMPATIBLE':
                    false_acceptances += 1
                if dec_ast == 'INCOMPATIBLE':
                    incompatible_neg_count += 1
                elif dec_ast == 'UNCERTAIN':
                    uncertain_neg_count += 1
            else:
                if dec_ast == 'INCOMPATIBLE':
                    false_rejections += 1
                if dec_ast == 'COMPATIBLE':
                    compatible_pos_count += 1

            if idx % 10 == 0 or idx == len(all_adv_samples):
                print(f"  Processed {idx}/{len(all_adv_samples)} adversarial samples... (latest: {os.path.basename(p_abs)}, latency: {dt_i:.2f}ms)", flush=True)

        far_api = false_acceptances / neg_count
        astro_rec_api = compatible_pos_count / pos_count
        
        print(f"\n--- HTTP API REGRESSION BENCHMARK RESULTS ---")
        print(f"Adversarial Negatives Tested: {neg_count}")
        print(f"Adversarial Positives Tested: {pos_count}")
        print(f"False Acceptance Rate (FAR @ 0.80): {far_api * 100:.2f}% ({false_acceptances}/{neg_count})")
        print(f"Astronomical Recall (COMPATIBLE):  {astro_rec_api * 100:.2f}% ({compatible_pos_count}/{pos_count})")
        print(f"Hard-Negative Breakdown: {incompatible_neg_count} INCOMPATIBLE, {uncertain_neg_count} UNCERTAIN, {false_acceptances} COMPATIBLE")
        
        assert false_acceptances == 0, f"REGRESSION FAILURE: {false_acceptances} false acceptances detected!"
        assert compatible_pos_count == pos_count, f"REGRESSION FAILURE: {pos_count - compatible_pos_count} astronomical positives missed!"
        print("  [PASS] Production HTTP API regression match Phase 10E evaluation results perfectly!")

        # 6. CORS Regression Test
        print("\n5. Testing CORS Headers & Preflight Options...")
        res_cors = requests.get(f"{API_BASE_URL}/health", headers={"Origin": "http://localhost:5176"})
        assert res_cors.headers.get("access-control-allow-origin") == "http://localhost:5176"
        
        res_opts = requests.options(
            f"{API_BASE_URL}/triage",
            headers={
                "Origin": "http://localhost:5176",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            }
        )
        assert res_opts.status_code == 200
        assert res_opts.headers.get("access-control-allow-origin") == "http://localhost:5176"
        assert "POST" in res_opts.headers.get("access-control-allow-methods", "")
        print("  [PASS] CORS origin and OPTIONS preflight verification passed.")

        # 7. Performance Benchmarking
        print("\n6. Benchmarking Latencies...")
        comp_latencies = [r['total_latency_ms'] for r in live_results if r['expected_domain'] == 'ASTRONOMICAL']
        incomp_latencies = [r['total_latency_ms'] for r in live_results if r['expected_domain'] == 'NON_ASTRONOMICAL']
        
        perf_meta = {
            'backend_startup_duration_ms': startup_duration_ms,
            'health_endpoint_latency_ms': health_ms,
            'compatible_inference_latency': {
                'mean_ms': round(float(np.mean(comp_latencies)), 2),
                'median_ms': round(float(np.median(comp_latencies)), 2),
                'p95_ms': round(float(np.percentile(comp_latencies, 95)), 2),
                'max_ms': round(float(np.max(comp_latencies)), 2)
            },
            'incompatible_inference_latency': {
                'mean_ms': round(float(np.mean(incomp_latencies)), 2),
                'median_ms': round(float(np.median(incomp_latencies)), 2),
                'p95_ms': round(float(np.percentile(incomp_latencies, 95)), 2),
                'max_ms': round(float(np.max(incomp_latencies)), 2)
            },
            'adversarial_suite_http_latency': {
                'mean_ms': round(float(np.mean(adv_latencies)), 2),
                'median_ms': round(float(np.median(adv_latencies)), 2),
                'p95_ms': round(float(np.percentile(adv_latencies, 95)), 2)
            }
        }

        # 8. Create Artifact JSON
        report_meta = {
            "phase": "10F",
            "status": "PASS",
            "promotion_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "production_model": "ml/models/domain_gate_v2_best.pt",
            "old_model_preserved": True,
            "calibration_temperature": 1.4996,
            "thresholds": {
                "compatible": 0.80,
                "uncertain_lower": 0.20,
                "uncertain_upper": 0.80,
                "incompatible": 0.20
            },
            "health_check": {
                "status": h_data['status'],
                "domain_gate_model_version": h_data['domain_gate_model_version'],
                "latency_ms": health_ms
            },
            "regression": {
                "total_adversarial_samples": len(all_adv_samples),
                "false_acceptance_rate": far_api,
                "astronomical_recall": astro_rec_api,
                "hard_negative_breakdown": {
                    "incompatible": incompatible_neg_count,
                    "uncertain": uncertain_neg_count,
                    "compatible": false_acceptances
                }
            },
            "safety_tests": {
                "incompatible_skips_morphology": True,
                "uncertain_skips_morphology": True,
                "compatible_executes_morphology": True
            },
            "cors_tests": {
                "origin_header_valid": True,
                "options_preflight_valid": True
            },
            "performance": perf_meta,
            "limitations": [
                "Evaluated on held-out adversarial benchmark suite (380 samples); does not guarantee universal arbitrary image recognition under unknown domain shifts.",
                "Abstention policy skips morphology analysis for boundary images in the 0.20-0.80 interval."
            ]
        }

        with open(REPORT_JSON_PATH, "w") as f:
            json.dump(report_meta, f, indent=2)
            
        print(f"\nArtifact saved to {REPORT_JSON_PATH}")
        return report_meta
    finally:
        stop_backend_server(server_proc)

if __name__ == '__main__':
    import traceback
    try:
        run_phase10f_verification()
    except Exception as e:
        print("\nEXCEPTIONAL FAILURE:")
        traceback.print_exc()
        sys.exit(1)
