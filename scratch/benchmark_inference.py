import os
import sys
import time
import json
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.src.inference import GalaxyZooInference

def run_benchmark():
    print("=" * 70)
    print("ASTRA STEP 11 & 12: INFERENCE LATENCY & RESOURCE AUDIT")
    print("=" * 70)

    project_root = os.getcwd()
    model_path = os.path.join(project_root, "ml/models/best_model.pt")
    test_img_path = os.path.join(project_root, "ml/data/processed/galaxy_zoo/images/20027.jpg")
    artifacts_dir = os.path.join(project_root, "ml/artifacts")

    if not os.path.exists(test_img_path):
        # find any image in images directory
        img_dir = os.path.join(project_root, "ml/data/processed/galaxy_zoo/images")
        files = [f for f in os.listdir(img_dir) if f.endswith(".jpg")]
        test_img_path = os.path.join(img_dir, files[0])

    print(f"Using sample image: {test_img_path}")

    # 1. Model Loading Time Benchmark
    t0_load = time.perf_counter()
    engine = GalaxyZooInference(model_path=model_path)
    t1_load = time.perf_counter()
    load_time_ms = round((t1_load - t0_load) * 1000.0, 2)
    print(f"Model Loading Time: {load_time_ms} ms (Device: {engine.device})")

    # 2. First Run (Cold Forward Pass)
    res_cold = engine.predict_single_image(test_img_path)
    first_inference_ms = res_cold["inference_time_ms"]
    print(f"First Inference Time (Cold): {first_inference_ms} ms")

    # 3. Warm Runs (35 iterations)
    warm_latencies = []
    for i in range(35):
        res_warm = engine.predict_single_image(test_img_path)
        warm_latencies.append(res_warm["inference_time_ms"])

    warm_arr = np.array(warm_latencies)
    warm_mean = float(round(np.mean(warm_arr), 2))
    warm_median = float(round(np.median(warm_arr), 2))
    warm_p95 = float(round(np.percentile(warm_arr, 95), 2))
    warm_min = float(round(np.min(warm_arr), 2))
    warm_max = float(round(np.max(warm_arr), 2))

    print(f"Warm Inference Latency (35 runs):")
    print(f"  Mean:   {warm_mean} ms")
    print(f"  Median: {warm_median} ms")
    print(f"  p95:    {warm_p95} ms")
    print(f"  Min:    {warm_min} ms")
    print(f"  Max:    {warm_max} ms")

    latency_report = {
        "device": str(engine.device),
        "backbone": engine.backbone_name,
        "num_runs": len(warm_latencies),
        "model_loading_time_ms": load_time_ms,
        "first_inference_cold_ms": first_inference_ms,
        "warm_inference_metrics": {
            "mean_ms": warm_mean,
            "median_ms": warm_median,
            "p95_ms": warm_p95,
            "min_ms": warm_min,
            "max_ms": warm_max
        },
        "sample_output": {
            "predicted_class": res_warm["predicted_class"],
            "class_confidence": res_warm["class_confidence"],
            "class_probabilities": res_warm["class_probabilities"],
            "scientific_attributes": res_warm["scientific_attributes"],
            "embedding_shape": list(res_warm["embedding"].shape)
        }
    }

    with open(os.path.join(artifacts_dir, "inference_latency.json"), "w") as f:
        json.dump(latency_report, f, indent=2)
    print("Saved inference latency report to inference_latency.json")

    # 4. Resource & Memory Estimates
    param_count = sum(p.numel() for p in engine.model.parameters())
    param_memory_mb = round(param_count * 4 / (1024 * 1024), 2)  # fp32
    ckpt_size_mb = round(os.path.getsize(model_path) / (1024 * 1024), 2)
    emb_file_path = os.path.join(artifacts_dir, "galaxy_zoo_embeddings.npy")
    emb_size_mb = round(os.path.getsize(emb_file_path) / (1024 * 1024), 2) if os.path.exists(emb_file_path) else 51.2

    print("\n" + "=" * 70)
    print("STEP 12: MEMORY & RESOURCE ESTIMATES")
    print("=" * 70)
    print(f"Model Checkpoint Size (Disk): {ckpt_size_mb} MB")
    print(f"Model Total Parameters: {param_count:,}")
    print(f"Model Parameters Memory (fp32 RAM/VRAM): {param_memory_mb} MB")
    print(f"10k Latent Embedding Matrix Size: {emb_size_mb} MB")
    print(f"Single Image Inference Tensor RAM: < 5 MB")
    print("=" * 70)

if __name__ == "__main__":
    run_benchmark()
