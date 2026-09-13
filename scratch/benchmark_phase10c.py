import os
import sys
import time
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.app.main import app
ASTRO_IMG_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "20027.jpg")
NON_ASTRO_IMG_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "non_astronomical", "non_astro_0001.jpg")
AMBIGUOUS_IMG_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "ambiguous", "ambiguous_001.jpg")

NUM_WARMUP = 5
NUM_RUNS = 25

def run_benchmark():
    print("=" * 60)
    print("ASTRA PHASE 10C — END-TO-END LATENCY BENCHMARK")
    print("=" * 60)

    with TestClient(app) as client:
        # Measure Startup & Health
        t0_health = time.perf_counter()
        health_res = client.get("/api/v1/health").json()
        health_ms = (time.perf_counter() - t0_health) * 1000.0

        print("\nHEALTH ENDPOINT SUMMARY:")
        print(f"Status: {health_res['status']}")
        print(f"ML Ready: {health_res['ml_ready']}")
        print(f"Domain Gate Loaded: {health_res['domain_gate_loaded']}")
        print(f"Model Version: {health_res['model_version']}")
        print(f"Domain Gate Model Version: {health_res['domain_gate_model_version']}")
        print(f"Device: {health_res['device']}")
        print(f"Backend Startup Duration: {health_res['startup_duration_ms']:.2f} ms")
        print(f"Health Response Latency: {health_ms:.2f} ms")

        categories = [
            ("COMPATIBLE ASTRONOMY IMAGE", ASTRO_IMG_PATH, "20027.jpg"),
            ("INCOMPATIBLE NON-ASTRONOMY IMAGE", NON_ASTRO_IMG_PATH, "non_astro_0001.jpg"),
            ("AMBIGUOUS / REVIEW IMAGE", AMBIGUOUS_IMG_PATH, "ambiguous_001.jpg")
        ]

        benchmark_summary = {}

        for cat_name, img_path, filename in categories:
            if not os.path.exists(img_path):
                print(f"\nSkipping {cat_name}: File not found ({img_path})")
                continue

            with open(img_path, "rb") as f:
                file_bytes = f.read()

            print(f"\n------------------------------------------------------------")
            print(f"BENCHMARKING: {cat_name} ({filename})")
            print(f"------------------------------------------------------------")

            # Warmup passes
            for _ in range(NUM_WARMUP):
                client.post("/api/v1/triage", files={"file": (filename, file_bytes, "image/jpeg")})

            http_latencies = []
            domain_latencies = []
            morphology_latencies = []
            total_triage_latencies = []
            sample_response = None

            for i in range(NUM_RUNS):
                t0 = time.perf_counter()
                res = client.post("/api/v1/triage", files={"file": (filename, file_bytes, "image/jpeg")})
                t1 = time.perf_counter()

                http_ms = (t1 - t0) * 1000.0
                data = res.json()
                sample_response = data

                domain_info = data.get("domain_validation", {})
                dom_ms = domain_info.get("inference_time_ms", 0.0)
                tot_ms = data.get("total_triage_ms", 0.0)
                morph_ms = data.get("inference_time_ms", 0.0) if domain_info.get("decision") == "COMPATIBLE" else 0.0

                http_latencies.append(http_ms)
                domain_latencies.append(dom_ms)
                morphology_latencies.append(morph_ms)
                total_triage_latencies.append(tot_ms)

            decision = sample_response.get("domain_validation", {}).get("decision")
            p_astro = sample_response.get("domain_validation", {}).get("probability_astronomical")

            stats = {
                "decision": decision,
                "p_astro": p_astro,
                "http_mean": float(np.mean(http_latencies)),
                "http_median": float(np.median(http_latencies)),
                "http_p95": float(np.percentile(http_latencies, 95)),
                "domain_mean": float(np.mean(domain_latencies)),
                "domain_median": float(np.median(domain_latencies)),
                "domain_p95": float(np.percentile(domain_latencies, 95)),
                "total_triage_mean": float(np.mean(total_triage_latencies)),
                "total_triage_median": float(np.median(total_triage_latencies)),
                "total_triage_p95": float(np.percentile(total_triage_latencies, 95)),
                "sample_response": sample_response
            }
            benchmark_summary[cat_name] = stats

            print(f"Domain Probability (Astronomical): {p_astro:.4f}")
            print(f"Domain Decision: {decision}")
            print(f"HTTP Latency (ms)       -> Mean: {stats['http_mean']:.2f} | Median: {stats['http_median']:.2f} | P95: {stats['http_p95']:.2f}")
            print(f"Domain Gate Latency (ms)-> Mean: {stats['domain_mean']:.2f} | Median: {stats['domain_median']:.2f} | P95: {stats['domain_p95']:.2f}")
            print(f"Total Triage Latency(ms)-> Mean: {stats['total_triage_mean']:.2f} | Median: {stats['total_triage_median']:.2f} | P95: {stats['total_triage_p95']:.2f}")

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print("=" * 60)
    return benchmark_summary

if __name__ == "__main__":
    run_benchmark()
