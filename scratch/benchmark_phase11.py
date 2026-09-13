import os
import sys
import time
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.app.main import app

ASTRO_IMG_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "demo", "astronomy_galaxy_smooth.jpg")
NON_ASTRO_IMG_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "demo", "non_astronomy_terrestrial.jpg")
AMBIGUOUS_IMG_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "ambiguous", "ambiguous_001.jpg")

NUM_WARMUP = 5
NUM_RUNS = 30

def run_phase11_benchmark():
    print("=" * 70)
    print("ASTRA PHASE 11 — END-TO-END PERFORMANCE BENCHMARK")
    print("=" * 70)

    summary = {}

    with TestClient(app) as client:
        # 1. Benchmark Health Endpoint
        for _ in range(NUM_WARMUP):
            client.get("/api/v1/health")

        health_latencies = []
        for _ in range(NUM_RUNS):
            t0 = time.perf_counter()
            res = client.get("/api/v1/health")
            t1 = time.perf_counter()
            health_latencies.append((t1 - t0) * 1000.0)

        health_stats = {
            "mean": float(np.mean(health_latencies)),
            "median": float(np.median(health_latencies)),
            "p95": float(np.percentile(health_latencies, 95)),
            "min": float(np.min(health_latencies)),
            "max": float(np.max(health_latencies))
        }
        summary["health"] = health_stats

        print("\nHEALTH ENDPOINT LATENCY (30 runs):")
        print(f"Mean: {health_stats['mean']:.2f} ms | Median: {health_stats['median']:.2f} ms | P95: {health_stats['p95']:.2f} ms | Min: {health_stats['min']:.2f} ms")

        targets = [
            ("COMPATIBLE (Astronomy Galaxy)", ASTRO_IMG_PATH, "astronomy_galaxy_smooth.jpg"),
            ("INCOMPATIBLE (Non-Astronomy Photo)", NON_ASTRO_IMG_PATH, "non_astronomy_terrestrial.jpg"),
            ("UNCERTAIN / BOUNDARY (Ambiguous)", AMBIGUOUS_IMG_PATH, "ambiguous_001.jpg")
        ]

        for label, file_path, filename in targets:
            if not os.path.exists(file_path):
                print(f"[-] Missing target file: {file_path}")
                continue

            with open(file_path, "rb") as f:
                img_bytes = f.read()

            # Warmup runs
            for _ in range(NUM_WARMUP):
                client.post("/api/v1/triage", files={"file": (filename, img_bytes, "image/jpeg")})

            http_times = []
            domain_times = []
            gz_times = []
            triage_times = []
            decisions = []

            for _ in range(NUM_RUNS):
                t0 = time.perf_counter()
                res = client.post("/api/v1/triage", files={"file": (filename, img_bytes, "image/jpeg")})
                t1 = time.perf_counter()

                http_ms = (t1 - t0) * 1000.0
                data = res.json()

                dom_info = data.get("domain_validation", {})
                dom_ms = dom_info.get("inference_time_ms", 0.0)
                tot_triage_ms = data.get("total_triage_ms", 0.0)
                gz_ms = data.get("inference_time_ms", 0.0) if dom_info.get("decision") == "COMPATIBLE" else 0.0
                decisions.append(dom_info.get("decision"))

                http_times.append(http_ms)
                domain_times.append(dom_ms)
                gz_times.append(gz_ms)
                triage_times.append(tot_triage_ms)

            target_stats = {
                "decision": decisions[0],
                "http": {
                    "mean": float(np.mean(http_times)),
                    "median": float(np.median(http_times)),
                    "p95": float(np.percentile(http_times, 95))
                },
                "domain_gate": {
                    "mean": float(np.mean(domain_times)),
                    "median": float(np.median(domain_times)),
                    "p95": float(np.percentile(domain_times, 95))
                },
                "galaxy_zoo": {
                    "mean": float(np.mean(gz_times)),
                    "median": float(np.median(gz_times)),
                    "p95": float(np.percentile(gz_times, 95))
                },
                "total_triage": {
                    "mean": float(np.mean(triage_times)),
                    "median": float(np.median(triage_times)),
                    "p95": float(np.percentile(triage_times, 95))
                }
            }
            summary[label] = target_stats

            print(f"\n{label} ({filename}):")
            print(f"Decision: {decisions[0]}")
            print(f"HTTP Latency         -> Mean: {target_stats['http']['mean']:.2f} ms | Median: {target_stats['http']['median']:.2f} ms | P95: {target_stats['http']['p95']:.2f} ms")
            print(f"Domain Gate Latency  -> Mean: {target_stats['domain_gate']['mean']:.2f} ms | Median: {target_stats['domain_gate']['median']:.2f} ms | P95: {target_stats['domain_gate']['p95']:.2f} ms")
            print(f"Galaxy Zoo Latency   -> Mean: {target_stats['galaxy_zoo']['mean']:.2f} ms | Median: {target_stats['galaxy_zoo']['median']:.2f} ms | P95: {target_stats['galaxy_zoo']['p95']:.2f} ms")
            print(f"Total Triage Latency -> Mean: {target_stats['total_triage']['mean']:.2f} ms | Median: {target_stats['total_triage']['median']:.2f} ms | P95: {target_stats['total_triage']['p95']:.2f} ms")

    print("\n" + "=" * 70)
    print("PHASE 11 BENCHMARK COMPLETE")
    print("=" * 70)
    return summary

if __name__ == "__main__":
    run_phase11_benchmark()
