import os
import io
import json
import time
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, auc, brier_score_loss
)

import torch
import torch.nn as nn
import torchvision.transforms as T
from torchvision.models import mobilenet_v3_small

ADV_NEG_MANIFEST = "ml/data/domain_gate/adversarial_manifest.csv"
ADV_POS_MANIFEST = "ml/data/domain_gate/adversarial_positive_manifest.csv"
SPLITS_V2_PATH = "ml/data/splits/domain_gate_v2_splits.csv"

OLD_MODEL_PATH = "ml/models/domain_gate_best.pt"
NEW_MODEL_PATH = "ml/models/domain_gate_v2_best.pt"

OUT_COMPARISON_JSON = "ml/artifacts/domain_gate_v2_comparison.json"
OUT_V2_METRICS_JSON = "ml/artifacts/domain_gate_v2_metrics.json"
OUT_LATENCY_JSON = "ml/artifacts/domain_gate_v2_latency.json"
OUT_FAILURE_CSV = "ml/artifacts/domain_gate_v2_failure_cases.csv"
OUT_FAILURE_GRID = "ml/artifacts/domain_gate_v2_failure_grid.png"

def compute_ece(probs, labels, n_bins=10):
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        bin_lower, bin_upper = bin_boundaries[i], bin_boundaries[i+1]
        in_bin = (probs >= bin_lower) & (probs < bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(labels[in_bin])
            avg_confidence_in_bin = np.mean(probs[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin
    return float(ece)

class StandaloneGate:
    def __init__(self, model_path, device):
        self.model_path = model_path
        self.device = device
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        checkpoint = torch.load(self.model_path, map_location=device)
        self.model = mobilenet_v3_small()
        in_features = self.model.classifier[3].in_features
        self.model.classifier[3] = nn.Linear(in_features, 1)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model = self.model.to(self.device)
        self.model.eval()

    def predict(self, img_path):
        with Image.open(img_path) as img:
            pil_img = img.convert('RGB')
        t_img = self.transform(pil_img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logit = self.model(t_img)
            prob_astro = float(torch.sigmoid(logit).cpu().numpy()[0][0])
        return prob_astro

def benchmark_latency(model_path, device_str):
    device = torch.device(device_str)
    t0_load = time.perf_counter()
    gate = StandaloneGate(model_path, device)
    load_ms = (time.perf_counter() - t0_load) * 1000.0
    
    dummy_img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    t0_cold = time.perf_counter()
    _ = gate.predict_dummy(dummy_img, device) if hasattr(gate, 'predict_dummy') else gate.predict_pil(dummy_img, device)
    cold_ms = (time.perf_counter() - t0_cold) * 1000.0
    
    warm_latencies = []
    for _ in range(50):
        t0_w = time.perf_counter()
        _ = gate.predict_pil(dummy_img, device)
        warm_latencies.append((time.perf_counter() - t0_w) * 1000.0)
        
    return {
        'device': device_str,
        'load_time_ms': round(load_ms, 2),
        'cold_inference_ms': round(cold_ms, 2),
        'warm_mean_ms': round(float(np.mean(warm_latencies)), 2),
        'warm_median_ms': round(float(np.median(warm_latencies)), 2),
        'warm_p95_ms': round(float(np.percentile(warm_latencies, 95)), 2)
    }

def run_comparison():
    device = torch.device('mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu'))
    print(f"Executing Domain Gate OLD vs NEW (V2) Comparison on device '{device}'...")
    
    old_gate = StandaloneGate(OLD_MODEL_PATH, device)
    new_gate = StandaloneGate(NEW_MODEL_PATH, device)
    
    df_neg = pd.read_csv(ADV_NEG_MANIFEST)
    df_pos = pd.read_csv(ADV_POS_MANIFEST)
    
    adv_samples = []
    for _, row in df_neg.iterrows():
        adv_samples.append({'path': row['path'], 'category': row['category'], 'label': 0, 'type': 'ADV_NEGATIVE'})
    for _, row in df_pos.iterrows():
        adv_samples.append({'path': row['path'], 'category': row['category'], 'label': 1, 'type': 'ADV_POSITIVE'})
        
    df_adv = pd.DataFrame(adv_samples)
    
    print(f"Evaluating untouchable Phase 10D benchmark ({len(df_adv)} samples)...")
    
    old_probs = []
    new_probs = []
    
    for idx, row in df_adv.iterrows():
        p_old = old_gate.predict(row['path'])
        p_new = new_gate.predict(row['path'])
        old_probs.append(p_old)
        new_probs.append(p_new)
        
    df_adv['p_old'] = old_probs
    df_adv['p_new'] = new_probs
    labels = df_adv['label'].values
    
    def calc_metrics(probs, labels_arr):
        preds_08 = (probs >= 0.80).astype(int)
        preds_incomp = (probs <= 0.20).astype(int)
        
        acc = accuracy_score(labels_arr, preds_08)
        prec = precision_score(labels_arr, preds_08, zero_division=0)
        rec = recall_score(labels_arr, preds_08, zero_division=0) # Astro recall
        f1 = f1_score(labels_arr, preds_08, zero_division=0)
        roc = roc_auc_score(labels_arr, probs)
        
        pos_mask = (labels_arr == 1)
        neg_mask = (labels_arr == 0)
        
        far = (preds_08[neg_mask] == 1).mean()
        frr = (preds_incomp[pos_mask] == 1).mean()
        spec = (probs[neg_mask] < 0.80).mean()
        hard_neg_rej = (preds_incomp[neg_mask] == 1).mean()
        hard_pos_rec = rec
        
        ece = compute_ece(probs, labels_arr)
        brier = brier_score_loss(labels_arr, probs)
        uncertain = ((probs > 0.20) & (probs < 0.80)).mean()
        
        return {
            'accuracy': float(acc),
            'precision': float(prec),
            'astronomy_recall': float(rec),
            'specificity': float(spec),
            'f1': float(f1),
            'roc_auc': float(roc),
            'false_acceptance_rate': float(far),
            'false_rejection_rate': float(frr),
            'hard_negative_rejection_rate': float(hard_neg_rej),
            'hard_positive_recall': float(hard_pos_rec),
            'ece': float(ece),
            'brier_score': float(brier),
            'uncertain_rate': float(uncertain)
        }
        
    m_old = calc_metrics(np.array(old_probs), labels)
    m_new = calc_metrics(np.array(new_probs), labels)
    
    print("\n==================================================")
    print("PHASE 10D UNTOUCHABLE ADVERSARIAL BENCHMARK RESULTS")
    print("==================================================")
    print(f"METRIC                        OLD MODEL     NEW MODEL (V2)")
    print(f"----------------------------------------------------------")
    print(f"Overall Accuracy              {m_old['accuracy']*100:6.2f}%       {m_new['accuracy']*100:6.2f}%")
    print(f"Astronomical Recall           {m_old['astronomy_recall']*100:6.2f}%       {m_new['astronomy_recall']*100:6.2f}%")
    print(f"Specificity                   {m_old['specificity']*100:6.2f}%       {m_new['specificity']*100:6.2f}%")
    print(f"False Acceptance Rate         {m_old['false_acceptance_rate']*100:6.2f}%       {m_new['false_acceptance_rate']*100:6.2f}%")
    print(f"False Rejection Rate          {m_old['false_rejection_rate']*100:6.2f}%       {m_new['false_rejection_rate']*100:6.2f}%")
    print(f"Hard-Negative Rejection       {m_old['hard_negative_rejection_rate']*100:6.2f}%       {m_new['hard_negative_rejection_rate']*100:6.2f}%")
    print(f"ROC-AUC                       {m_old['roc_auc']:8.4f}       {m_new['roc_auc']:8.4f}")
    print(f"ECE (Calibration Error)       {m_old['ece']:8.4f}       {m_new['ece']:8.4f}")
    print(f"Uncertain / Abstain Rate      {m_old['uncertain_rate']*100:6.2f}%       {m_new['uncertain_rate']*100:6.2f}%")
    print("==================================================\n")
    
    # Real-World Failure Category Priority Comparison Table
    cat_comparison = []
    for cat, df_c in df_adv.groupby('category'):
        mean_old = df_c['p_old'].mean()
        mean_new = df_c['p_new'].mean()
        c_type = df_c['type'].iloc[0]
        
        cat_comparison.append({
            'category': cat,
            'type': c_type,
            'count': len(df_c),
            'old_mean_p_astro': round(float(mean_old), 4),
            'new_mean_p_astro': round(float(mean_new), 4),
            'old_compatible_count': int((df_c['p_old'] >= 0.80).sum()),
            'new_compatible_count': int((df_c['p_new'] >= 0.80).sum()),
            'change_summary': 'IMPROVED' if (c_type == 'ADV_NEGATIVE' and mean_new < mean_old) or (c_type == 'ADV_POSITIVE' and mean_new > mean_old) else 'UNCHANGED'
        })
        
    df_cat_comp = pd.DataFrame(cat_comparison)
    
    # Also evaluate V2 model on V2 held-out TEST split
    df_splits_v2 = pd.read_csv(SPLITS_V2_PATH)
    df_test_v2 = df_splits_v2[df_splits_v2['split'] == 'TEST'].reset_index(drop=True)
    test_v2_probs = []
    test_v2_labels = []
    
    for _, r in df_test_v2.iterrows():
        p = new_gate.predict(r['path'])
        test_v2_probs.append(p)
        test_v2_labels.append(1 if r['domain_label'] == 'ASTRONOMICAL' else 0)
        
    m_test_v2 = calc_metrics(np.array(test_v2_probs), np.array(test_v2_labels))
    
    # Latency benchmarking
    # MPS
    gate_mps = StandaloneGate(NEW_MODEL_PATH, device)
    dummy = Image.new("RGB", (224, 224), (128, 128, 128))
    
    # Warmup
    for _ in range(5):
        t_img = gate_mps.transform(dummy).unsqueeze(0).to(device)
        with torch.no_grad():
            _ = gate_mps.model(t_img)
            
    lat_mps = []
    for _ in range(100):
        t0 = time.perf_counter()
        t_img = gate_mps.transform(dummy).unsqueeze(0).to(device)
        with torch.no_grad():
            _ = gate_mps.model(t_img)
        lat_mps.append((time.perf_counter() - t0) * 1000.0)
        
    # CPU
    device_cpu = torch.device('cpu')
    gate_cpu = StandaloneGate(NEW_MODEL_PATH, device_cpu)
    for _ in range(5):
        t_img = gate_cpu.transform(dummy).unsqueeze(0).to(device_cpu)
        with torch.no_grad():
            _ = gate_cpu.model(t_img)
            
    lat_cpu = []
    for _ in range(100):
        t0 = time.perf_counter()
        t_img = gate_cpu.transform(dummy).unsqueeze(0).to(device_cpu)
        with torch.no_grad():
            _ = gate_cpu.model(t_img)
        lat_cpu.append((time.perf_counter() - t0) * 1000.0)
        
    latency_meta = {
        'device_mps': {
            'warm_mean_ms': round(float(np.mean(lat_mps)), 2),
            'warm_median_ms': round(float(np.median(lat_mps)), 2),
            'warm_p95_ms': round(float(np.percentile(lat_mps, 95)), 2)
        },
        'device_cpu': {
            'warm_mean_ms': round(float(np.mean(lat_cpu)), 2),
            'warm_median_ms': round(float(np.median(lat_cpu)), 2),
            'warm_p95_ms': round(float(np.percentile(lat_cpu, 95)), 2)
        }
    }
    
    with open(OUT_LATENCY_JSON, 'w') as f:
        json.dump(latency_meta, f, indent=2)
        
    # Failure Grid Visualization Plot
    fig, axes = plt.subplots(2, 4, figsize=(12, 6), dpi=150)
    fig.suptitle("Domain Gate V2 Audit Sample Visual Grid", fontsize=14, y=0.98)
    
    sample_categories = [
        ('animals', 'Leopard Fur Rosette', 0),
        ('maps', 'Weather Radar Map', 0),
        ('night_sky', 'Night City Sky', 0),
        ('screenshots', 'Dark IDE UI', 0),
        ('stellar_fields', 'Stellar Field', 1),
        ('nebular_fields', 'Nebula Gas Cloud', 1),
        ('low_contrast', 'Low Contrast Galaxy', 1),
        ('unusual_astro', 'Colliding Galaxy', 1)
    ]
    
    for ax_idx, (cat, title, exp_lbl) in enumerate(sample_categories):
        ax = axes[ax_idx // 4, ax_idx % 4]
        df_sub = df_adv[df_adv['category'] == cat]
        if len(df_sub) > 0:
            sample_row = df_sub.iloc[0]
            with Image.open(sample_row['path']) as img_p:
                ax.imshow(img_p)
            p_val = sample_row['p_new']
            dec_str = "COMPATIBLE" if p_val >= 0.80 else ("INCOMPATIBLE" if p_val <= 0.20 else "UNCERTAIN")
            ax.set_title(f"{title}\nP(Astro)={p_val:.3f} [{dec_str}]", fontsize=9)
        ax.axis('off')
        
    plt.tight_layout()
    plt.savefig(OUT_FAILURE_GRID, dpi=150)
    plt.close(fig)
    
    # Save Failure Cases CSV
    df_failures = df_adv[(df_adv['label'] == 0) & (df_adv['p_new'] >= 0.80) | (df_adv['label'] == 1) & (df_adv['p_new'] <= 0.20)]
    df_failures.to_csv(OUT_FAILURE_CSV, index=False)
    
    # Write Comparison JSON
    comp_json_data = {
        'evaluation_date': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        'benchmark_dataset': 'Phase 10D Untouched Adversarial Suite (380 samples)',
        'old_model': {
            'checkpoint': OLD_MODEL_PATH,
            'metrics': m_old
        },
        'new_model': {
            'checkpoint': NEW_MODEL_PATH,
            'metrics': m_new
        },
        'new_model_v2_test_split_metrics': m_test_v2,
        'category_comparison': cat_comparison,
        'latency_benchmarks': latency_meta
    }
    
    with open(OUT_COMPARISON_JSON, 'w') as f:
        json.dump(comp_json_data, f, indent=2)
        
    # Write V2 Metrics JSON
    v2_metrics_data = {
        'model_version': 'mobilenet_v3_small_domain_gate_v2',
        'test_metrics_adversarial_suite': m_new,
        'test_metrics_v2_split': m_test_v2,
        'latency': latency_meta
    }
    with open(OUT_V2_METRICS_JSON, 'w') as f:
        json.dump(v2_metrics_data, f, indent=2)
        
    print(f"\nComparison artifacts generated successfully:")
    print(f"  Comparison JSON: {OUT_COMPARISON_JSON}")
    print(f"  V2 Metrics JSON: {OUT_V2_METRICS_JSON}")
    print(f"  Latency JSON: {OUT_LATENCY_JSON}")
    print(f"  Failure Grid Plot: {OUT_FAILURE_GRID}")

if __name__ == '__main__':
    run_comparison()
