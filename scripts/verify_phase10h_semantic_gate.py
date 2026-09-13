import os
import sys
import time
import json
import subprocess
import requests
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.app.config import settings

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

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
    for _ in range(40): # up to 20 seconds max wait
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

def run_phase10h_verification():
    print("==================================================")
    print("ASTRA PHASE 10H — TWO-STAGE SEMANTIC GATE VERIFICATION")
    print("==================================================")

    # 1. Verification of Backend Configuration
    print("\n1. Verifying Configuration & Artifact Paths...")
    assert os.path.exists(settings.DOMAIN_GATE_PATH), f"Domain Gate V2 missing: {settings.DOMAIN_GATE_PATH}"
    print("  [PASS] Domain Gate V2 checkpoint verified.")

    # 2. Start Backend Server
    server_proc, startup_ms = start_backend_server()

    try:
        # 3. Test Health Endpoint
        print("\n2. Testing GET /api/v1/health...")
        t0_h = time.perf_counter()
        r_health = requests.get(f"{API_BASE_URL}/health")
        dt_h = (time.perf_counter() - t0_h) * 1000.0
        assert r_health.status_code == 200, f"Health check failed: {r_health.status_code}"
        d_health = r_health.json()
        assert d_health["ml_ready"] is True
        assert d_health["domain_gate_loaded"] is True
        assert d_health["semantic_gate_loaded"] is True
        print(f"  [PASS] Health check passed! Semantic Gate: {d_health.get('semantic_gate_model_version')}, Latency: {dt_h:.2f} ms")

        # 4. Safety Assertion Tests & Manual Holdout HTTP API Evaluation
        print("\n3. Testing Two-Stage Fail-Closed API Safety Assertions...")

        test_cases = [
            ("LEOPARD (ANIMAL)", "ml/data/domain_gate/adversarial/animals/adv_neg_animals_001.jpg", "INCOMPATIBLE", False),
            ("RAINFALL MAP", "ml/data/domain_gate/adversarial/maps/adv_neg_maps_001.jpg", "INCOMPATIBLE", False),
            ("IDE SCREENSHOT", "ml/data/domain_gate/adversarial/screenshots/adv_neg_screenshots_001.jpg", "INCOMPATIBLE", False),
            ("SPACE ARTWORK", "ml/data/domain_gate/adversarial/space_art/adv_neg_space_art_001.jpg", "UNCERTAIN", False),
            ("TERRESTRIAL SCENE", "ml/data/demo/non_astronomy_terrestrial.jpg", "INCOMPATIBLE", False),
            ("REAL GALAXY (SMOOTH)", "ml/data/demo/astronomy_galaxy_smooth.jpg", "COMPATIBLE", True),
            ("REAL GALAXY (DISK)", "ml/data/demo/astronomy_galaxy_disk.jpg", "COMPATIBLE", True),
            ("FAINT LOW-CONTRAST GALAXY", "ml/data/domain_gate/adversarial_positive/low_contrast/adv_pos_low_contrast_001.jpg", "COMPATIBLE", True)
        ]

        safety_results = []

        for name, rel_path, expected_dec, expect_morph in test_cases:
            abs_path = os.path.join(PROJECT_ROOT, rel_path)
            if not os.path.exists(abs_path):
                print(f"  [SKIP] File missing: {rel_path}")
                continue

            with open(abs_path, "rb") as f:
                b = f.read()

            t0_req = time.perf_counter()
            res = requests.post(f"{API_BASE_URL}/triage", files={"file": (os.path.basename(abs_path), b, "image/jpeg")})
            dt_req = (time.perf_counter() - t0_req) * 1000.0

            assert res.status_code == 200, f"HTTP request failed for {name}: {res.status_code}"
            data = res.json()

            dom_val = data["domain_validation"]
            decision = dom_val["decision"]
            sem_status = dom_val.get("semantic_gate_status")
            sem_margin = dom_val.get("semantic_margin")
            
            morph_ran = data.get("predicted_class") is not None
            triage_ran = data.get("experimental_triage_score") is not None

            print(f"  [{name:25s}] Decision: {decision:12s} | SemStatus: {str(sem_status):20s} | Margin: {str(sem_margin):7s} | Morph: {str(morph_ran):5s} | Latency: {dt_req:.2f} ms")

            # SAFETY CONTROL ASSERTIONS
            if decision == "INCOMPATIBLE" or decision == "UNCERTAIN":
                assert morph_ran is False, f"SAFETY VIOLATION: Morphology executed for {name} ({decision})!"
                assert triage_ran is False, f"SAFETY VIOLATION: Triage score computed for {name} ({decision})!"
            elif decision == "COMPATIBLE":
                assert morph_ran is True, f"EXECUTION FAILURE: Morphology missing for compatible {name}!"
                assert triage_ran is True, f"EXECUTION FAILURE: Triage score missing for compatible {name}!"

            safety_results.append({
                "test_name": name,
                "path": rel_path,
                "expected_decision": expected_dec,
                "actual_decision": decision,
                "semantic_gate_status": sem_status,
                "semantic_margin": sem_margin,
                "morphology_executed": morph_ran,
                "triage_executed": triage_ran,
                "latency_ms": round(dt_req, 2)
            })

        print("  [PASS] All fail-closed safety assertions passed!")

        # 5. CORS Integration Verification
        print("\n4. Testing CORS Headers & Preflight Options...")
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
        print("  [PASS] CORS origin and OPTIONS preflight verification passed.")

        # 6. Full 380-Sample Two-Stage HTTP API Regression Evaluation
        print("\n5. Running 380-Sample Two-Stage Regression Benchmark via HTTP API...")
        adv_neg_df = pd.read_csv(os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "adversarial_manifest.csv"))
        adv_pos_df = pd.read_csv(os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "adversarial_positive_manifest.csv"))

        all_samples = []
        for _, row in adv_neg_df.iterrows():
            all_samples.append((os.path.join(PROJECT_ROOT, row['path']), 'NON_ASTRONOMICAL'))
        for _, row in adv_pos_df.iterrows():
            all_samples.append((os.path.join(PROJECT_ROOT, row['path']), 'ASTRONOMICAL'))

        neg_count = len(adv_neg_df)
        pos_count = len(adv_pos_df)

        false_acceptances = 0
        false_rejections = 0
        incompatible_neg = 0
        uncertain_neg = 0
        compatible_pos = 0
        uncertain_pos = 0

        latencies = []

        for idx, (p_abs, exp_dom) in enumerate(all_samples, 1):
            with open(p_abs, "rb") as f:
                b = f.read()
            t0_i = time.perf_counter()
            r_api = requests.post(f"{API_BASE_URL}/triage", files={"file": (os.path.basename(p_abs), b, "image/jpeg")}, timeout=10.0)
            dt_i = (time.perf_counter() - t0_i) * 1000.0
            latencies.append(dt_i)

            d_api = r_api.json()
            dec_ast = d_api['domain_validation']['decision']

            if exp_dom == 'NON_ASTRONOMICAL':
                if dec_ast == 'COMPATIBLE':
                    false_acceptances += 1
                elif dec_ast == 'INCOMPATIBLE':
                    incompatible_neg += 1
                elif dec_ast == 'UNCERTAIN':
                    uncertain_neg += 1
            else:
                if dec_ast == 'INCOMPATIBLE':
                    false_rejections += 1
                elif dec_ast == 'UNCERTAIN':
                    uncertain_pos += 1
                elif dec_ast == 'COMPATIBLE':
                    compatible_pos += 1

            if idx % 50 == 0 or idx == len(all_samples):
                print(f"  Processed {idx}/{len(all_samples)} samples... (latest: {os.path.basename(p_abs)}, latency: {dt_i:.2f}ms)", flush=True)

        far_api = false_acceptances / neg_count
        astro_rec_api = compatible_pos / pos_count

        print("\n--- TWO-STAGE HTTP API REGRESSION RESULTS ---")
        print(f"Total Non-Astronomical Negatives Tested: {neg_count}")
        print(f"Total Astronomical Positives Tested:     {pos_count}")
        print(f"False Acceptance Rate (FAR):            {far_api * 100:.2f}% ({false_acceptances}/{neg_count})")
        print(f"Astronomical Recall (COMPATIBLE):       {astro_rec_api * 100:.2f}% ({compatible_pos}/{pos_count})")
        print(f"Negatives Breakdown: {incompatible_neg} INCOMPATIBLE, {uncertain_neg} UNCERTAIN, {false_acceptances} COMPATIBLE")
        print(f"Positives Breakdown: {compatible_pos} COMPATIBLE, {uncertain_pos} UNCERTAIN, {false_rejections} INCOMPATIBLE")
        print(f"HTTP Latency (Mean): {np.mean(latencies):.2f} ms | Median: {np.median(latencies):.2f} ms | P95: {np.percentile(latencies, 95):.2f} ms")

        assert false_acceptances == 0, f"FAIL: {false_acceptances} false acceptances detected!"
        assert false_rejections == 0, f"FAIL: {false_rejections} false rejections detected!"
        print("  [PASS] Two-stage pipeline achieved 0.00% False Acceptance Rate with zero false rejections!")

        # 7. Generate Verification Report
        perf_meta = {
            "startup_duration_ms": startup_ms,
            "health_latency_ms": round(dt_h, 2),
            "http_regression_latency_ms": {
                "mean": round(float(np.mean(latencies)), 2),
                "median": round(float(np.median(latencies)), 2),
                "p95": round(float(np.percentile(latencies, 95)), 2)
            }
        }

        report_meta = {
            "phase": "10H",
            "status": "PASS",
            "semantic_gate_model": d_health.get("semantic_gate_model_version"),
            "domain_gate_v2_model": d_health.get("domain_gate_model_version"),
            "two_stage_pipeline": "Universal Semantic Gate -> Domain Gate V2 -> Galaxy Zoo Morphology",
            "safety_assertions": safety_results,
            "regression_metrics": {
                "total_negatives": neg_count,
                "total_positives": pos_count,
                "false_acceptance_rate": round(far_api, 4),
                "astronomical_recall": round(astro_rec_api, 4),
                "incompatible_negatives": incompatible_neg,
                "uncertain_negatives": uncertain_neg,
                "compatible_positives": compatible_pos,
                "uncertain_positives": uncertain_pos
            },
            "cors_tests": {"origin_header_valid": True, "options_preflight_valid": True},
            "performance": perf_meta
        }

        report_path = os.path.join(PROJECT_ROOT, "ml", "artifacts", "phase10h_open_world_gate_report.json")
        with open(report_path, "w") as f:
            json.dump(report_meta, f, indent=2)
        print(f"\nFinal promotion report saved to {report_path}")

    finally:
        stop_backend_server(server_proc)

if __name__ == "__main__":
    import traceback
    try:
        run_phase10h_verification()
    except Exception as e:
        print("\nEXCEPTIONAL FAILURE:")
        traceback.print_exc()
        sys.exit(1)
