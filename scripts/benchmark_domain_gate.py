import os
import json
import time
import numpy as np
import pandas as pd
from PIL import Image
import torch

from ml.src.domain_gate import DomainGate

MANIFEST_PATH = "ml/data/domain_gate_manifest.csv"
BEST_MODEL_PATH = "ml/models/domain_gate_best.pt"
LATENCY_PATH = "ml/artifacts/domain_gate_latency.json"
METRICS_PATH = "ml/artifacts/domain_gate_metrics.json"

def benchmark_model_size():
    checkpoint_bytes = os.path.getsize(BEST_MODEL_PATH)
    checkpoint_mb = checkpoint_bytes / (1024 * 1024)
    
    # Instantiate model to measure parameters
    gate = DomainGate(model_path=BEST_MODEL_PATH, device='cpu')
    param_count = sum(p.numel() for p in gate.model.parameters())
    trainable_param_count = sum(p.numel() for p in gate.model.parameters() if p.requires_grad)
    
    return {
        'checkpoint_size_mb': round(checkpoint_mb, 2),
        'total_parameters': param_count,
        'trainable_parameters': trainable_param_count
    }

def benchmark_latency(device_name='mps'):
    if device_name == 'mps' and not torch.backends.mps.is_available():
        device_name = 'cpu'
        
    print(f"\n--- BENCHMARKING LATENCY ON '{device_name}' ---")
    
    # 1. Model load time
    t0 = time.time()
    gate = DomainGate(model_path=BEST_MODEL_PATH, device=device_name)
    load_ms = (time.time() - t0) * 1000
    
    # Sample test image
    df_manifest = pd.read_csv(MANIFEST_PATH)
    sample_img_path = df_manifest.iloc[0]['path']
    
    # 2. First inference (cold)
    t0 = time.time()
    first_res = gate.predict(sample_img_path)
    first_ms = (time.time() - t0) * 1000
    
    # 3. 30 Warm iterations
    warm_latencies = []
    for _ in range(30):
        t0 = time.time()
        _ = gate.predict(sample_img_path)
        warm_latencies.append((time.time() - t0) * 1000)
        
    mean_ms = float(np.mean(warm_latencies))
    median_ms = float(np.median(warm_latencies))
    p95_ms = float(np.percentile(warm_latencies, 95))
    
    print(f"Device:               {device_name}")
    print(f"Model Load Time:      {load_ms:.2f} ms")
    print(f"First Inference:      {first_ms:.2f} ms")
    print(f"Warm Mean Latency:    {mean_ms:.2f} ms")
    print(f"Warm Median Latency:  {median_ms:.2f} ms")
    print(f"Warm p95 Latency:     {p95_ms:.2f} ms")
    
    return {
        'device': device_name,
        'load_ms': round(load_ms, 2),
        'first_inference_ms': round(first_ms, 2),
        'warm_mean_ms': round(mean_ms, 2),
        'warm_median_ms': round(median_ms, 2),
        'warm_p95_ms': round(p95_ms, 2)
    }

def run_sanity_tests():
    print("\n--- QUALITATIVE DOMAIN SANITY TEST ---")
    gate = DomainGate(model_path=BEST_MODEL_PATH)
    df_manifest = pd.read_csv(MANIFEST_PATH)
    
    samples = [
        ('Galaxy Zoo Astronomy', df_manifest[df_manifest['source'] == 'Galaxy Zoo 2 (SDSS)'].iloc[0]['path']),
        ('Stellar Field Survey', df_manifest[df_manifest['subcategory'] == 'stellar_field'].iloc[0]['path']),
        ('Nebula Survey', df_manifest[df_manifest['subcategory'] == 'nebula'].iloc[0]['path']),
        ('Natural Sky/Cloud', df_manifest[df_manifest['subcategory'] == 'natural_scenes'].iloc[0]['path']),
        ('Object/Building', df_manifest[df_manifest['subcategory'] == 'objects_vehicles'].iloc[0]['path']),
        ('Biological Portrait', df_manifest[df_manifest['subcategory'] == 'biological'].iloc[0]['path']),
        ('Graphics Plot', df_manifest[df_manifest['subcategory'] == 'graphics_ui'].iloc[0]['path']),
        ('Hard Negative Night Sky', df_manifest[df_manifest['subcategory'] == 'hard_negatives'].iloc[0]['path']),
        ('Ambiguous Space Poster', df_manifest[df_manifest['domain_label'] == 'AMBIGUOUS'].iloc[0]['path']),
    ]
    
    results = []
    for label, img_path in samples:
        res = gate.predict(img_path)
        print(f"  {label:<25} -> P(Astro): {res['probability_astronomical']:.4f} | Decision: {res['decision']}")
        results.append({
            'sample': label,
            'probability_astronomical': res['probability_astronomical'],
            'decision': res['decision']
        })
    return results

def main():
    size_meta = benchmark_model_size()
    
    mps_latency = benchmark_latency(device_name='mps')
    cpu_latency = benchmark_latency(device_name='cpu')
    
    sanity_res = run_sanity_tests()
    
    # Save latency artifact
    latency_data = {
        'mps': mps_latency,
        'cpu': cpu_latency
    }
    with open(LATENCY_PATH, 'w') as f:
        json.dump(latency_data, f, indent=2)
    print(f"\nSaved latency benchmarks to {LATENCY_PATH}")
    
    # Load evaluation summary created by evaluate_domain_gate.py
    eval_summary_path = "ml/artifacts/domain_gate_eval_summary.json"
    eval_summary = {}
    if os.path.exists(eval_summary_path):
        with open(eval_summary_path) as f:
            eval_summary = json.load(f)
            
    df_manifest = pd.read_csv(MANIFEST_PATH)
    
    metrics_data = {
        'dataset': {
            'train_count': len(df_manifest[df_manifest['split'] == 'TRAIN']),
            'val_count': len(df_manifest[df_manifest['split'] == 'VAL']),
            'test_count': len(df_manifest[df_manifest['split'] == 'TEST']),
            'review_count': len(df_manifest[df_manifest['split'] == 'REVIEW']),
            'total_count': len(df_manifest)
        },
        'model': {
            'architecture': 'MobileNetV3-Small',
            'parameters': size_meta['total_parameters'],
            'trainable_parameters': size_meta['trainable_parameters'],
            'checkpoint_size_mb': size_meta['checkpoint_size_mb'],
            'model_version': 'mobilenet_v3_small_domain_gate_v1'
        },
        'test_metrics': eval_summary.get('test_metrics', {}),
        'thresholds': eval_summary.get('thresholds', {'compatible_threshold': 0.80, 'incompatible_threshold': 0.20}),
        'latency_mps': mps_latency,
        'latency_cpu': cpu_latency,
        'sanity_tests': sanity_res
    }
    
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    print(f"Saved machine-readable metrics to {METRICS_PATH}")

if __name__ == '__main__':
    main()
