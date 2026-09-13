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
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.src.domain_gate import DomainGate

ADV_MANIFEST_PATH = "ml/data/domain_gate/adversarial_manifest.csv"
ADV_POS_MANIFEST_PATH = "ml/data/domain_gate/adversarial_positive_manifest.csv"

OUT_JSON_PATH = "ml/artifacts/domain_gate_adversarial_results.json"
OUT_CSV_PATH = "ml/artifacts/domain_gate_adversarial_by_category.csv"
OUT_CM_PATH = "ml/artifacts/domain_gate_adversarial_confusion_matrix.png"

def run_adversarial_evaluation():
    print("Initializing Domain Gate for Adversarial Failure Audit...")
    gate = DomainGate()
    
    df_neg = pd.read_csv(ADV_MANIFEST_PATH)
    df_pos = pd.read_csv(ADV_POS_MANIFEST_PATH)
    
    print(f"Loaded {len(df_neg)} adversarial negatives and {len(df_pos)} adversarial positives.")
    
    results = []
    
    # Evaluate Negatives
    print("\nEvaluating Adversarial Negatives...")
    for idx, row in df_neg.iterrows():
        path = row['path']
        cat = row['category']
        expected_dec = "INCOMPATIBLE"
        
        t0 = time.perf_counter()
        pred = gate.predict(path)
        dt = (time.perf_counter() - t0) * 1000.0
        
        p_astro = pred['probability_astronomical']
        decision = pred['decision']
        
        # Correct if predicted INCOMPATIBLE (or UNCERTAIN depending on strictness)
        # False Acceptance occurs if decision == "COMPATIBLE" (P_astro >= 0.80)
        is_correct = (decision == expected_dec)
        is_false_acceptance = (p_astro >= 0.80)
        
        results.append({
            'filename': os.path.basename(path),
            'path': path,
            'category': cat,
            'type': 'NEGATIVE',
            'expected_domain': 'NON_ASTRONOMICAL',
            'expected_decision': expected_dec,
            'probability_astronomical': p_astro,
            'probability_non_astronomical': pred['probability_non_astronomical'],
            'predicted_decision': decision,
            'is_correct': is_correct,
            'is_false_acceptance': is_false_acceptance,
            'is_false_rejection': False,
            'inference_latency_ms': round(dt, 2),
            'notes': row.get('notes', ''),
            'source': row.get('source', '')
        })
        
    # Evaluate Positives
    print("Evaluating Adversarial Positives...")
    for idx, row in df_pos.iterrows():
        path = row['path']
        cat = row['category']
        expected_dec = "COMPATIBLE"
        
        t0 = time.perf_counter()
        pred = gate.predict(path)
        dt = (time.perf_counter() - t0) * 1000.0
        
        p_astro = pred['probability_astronomical']
        decision = pred['decision']
        
        is_correct = (decision == expected_dec)
        is_false_rejection = (p_astro <= 0.20)
        
        results.append({
            'filename': os.path.basename(path),
            'path': path,
            'category': cat,
            'type': 'POSITIVE',
            'expected_domain': 'ASTRONOMICAL',
            'expected_decision': expected_dec,
            'probability_astronomical': p_astro,
            'probability_non_astronomical': pred['probability_non_astronomical'],
            'predicted_decision': decision,
            'is_correct': is_correct,
            'is_false_acceptance': False,
            'is_false_rejection': is_false_rejection,
            'inference_latency_ms': round(dt, 2),
            'notes': row.get('notes', ''),
            'source': row.get('source', '')
        })
        
    df_res = pd.DataFrame(results)
    
    # 1. Overall Summary Metrics
    total_samples = len(df_res)
    total_negatives = len(df_res[df_res['type'] == 'NEGATIVE'])
    total_positives = len(df_res[df_res['type'] == 'POSITIVE'])
    
    false_acceptances = df_res[(df_res['type'] == 'NEGATIVE') & (df_res['probability_astronomical'] >= 0.80)]
    false_rejections = df_res[(df_res['type'] == 'POSITIVE') & (df_res['probability_astronomical'] <= 0.20)]
    
    overall_far = len(false_acceptances) / total_negatives if total_negatives > 0 else 0.0
    overall_frr = len(false_rejections) / total_positives if total_positives > 0 else 0.0
    
    correct_count = len(df_res[df_res['is_correct']])
    overall_accuracy = correct_count / total_samples
    
    positive_rec = len(df_res[(df_res['type'] == 'POSITIVE') & (df_res['predicted_decision'] == 'COMPATIBLE')]) / total_positives
    
    print(f"\n--- OVERALL ADVERSARIAL METRICS ---")
    print(f"Total Samples: {total_samples} (Negatives: {total_negatives}, Positives: {total_positives})")
    print(f"Overall Accuracy: {overall_accuracy * 100:.2f}%")
    print(f"False Acceptance Rate (FAR @ 0.80): {overall_far * 100:.2f}% ({len(false_acceptances)}/{total_negatives})")
    print(f"False Rejection Rate (FRR @ 0.20): {overall_frr * 100:.2f}% ({len(false_rejections)}/{total_positives})")
    print(f"Astronomical Recall (COMPATIBLE): {positive_rec * 100:.2f}%")
    
    # 2. Per-Category Breakdown
    category_summary = []
    for cat, df_cat in df_res.groupby('category'):
        cat_type = df_cat['type'].iloc[0]
        n_cat = len(df_cat)
        mean_prob = float(df_cat['probability_astronomical'].mean())
        std_prob = float(df_cat['probability_astronomical'].std()) if n_cat > 1 else 0.0
        
        n_compatible = len(df_cat[df_cat['predicted_decision'] == 'COMPATIBLE'])
        n_uncertain = len(df_cat[df_cat['predicted_decision'] == 'UNCERTAIN'])
        n_incompatible = len(df_cat[df_cat['predicted_decision'] == 'INCOMPATIBLE'])
        
        if cat_type == 'NEGATIVE':
            far_cat = n_compatible / n_cat
            frr_cat = 0.0
        else:
            far_cat = 0.0
            frr_cat = n_incompatible / n_cat
            
        category_summary.append({
            'category': cat,
            'type': cat_type,
            'sample_count': n_cat,
            'mean_p_astronomical': round(mean_prob, 4),
            'std_p_astronomical': round(std_prob, 4),
            'n_compatible': n_compatible,
            'n_uncertain': n_uncertain,
            'n_incompatible': n_incompatible,
            'false_acceptance_rate': round(far_cat, 4),
            'false_rejection_rate': round(frr_cat, 4)
        })
        
    df_cat_sum = pd.DataFrame(category_summary)
    df_cat_sum.to_csv(OUT_CSV_PATH, index=False)
    
    # Identify Hardest Negative Category (highest FAR or highest mean P_astro)
    df_neg_cats = df_cat_sum[df_cat_sum['type'] == 'NEGATIVE'].sort_values(by=['false_acceptance_rate', 'mean_p_astronomical'], ascending=False)
    hardest_negative_cat = df_neg_cats.iloc[0]['category'] if len(df_neg_cats) > 0 else 'N/A'
    
    # 3. Threshold Tradeoff Analysis across candidate thresholds
    candidate_thresholds = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    threshold_tradeoffs = []
    
    for t in candidate_thresholds:
        # At threshold t, P(Astro) >= t is COMPATIBLE
        # P(Astro) <= 0.20 is INCOMPATIBLE
        # 0.20 < P(Astro) < t is UNCERTAIN
        n_pos_comp = len(df_res[(df_res['type'] == 'POSITIVE') & (df_res['probability_astronomical'] >= t)])
        n_neg_comp = len(df_res[(df_res['type'] == 'NEGATIVE') & (df_res['probability_astronomical'] >= t)])
        n_neg_incomp = len(df_res[(df_res['type'] == 'NEGATIVE') & (df_res['probability_astronomical'] <= 0.20)])
        n_neg_uncert = len(df_res[(df_res['type'] == 'NEGATIVE') & (df_res['probability_astronomical'] > 0.20) & (df_res['probability_astronomical'] < t)])
        
        astro_recall = n_pos_comp / total_positives if total_positives > 0 else 0.0
        non_astro_spec = (total_negatives - n_neg_comp) / total_negatives if total_negatives > 0 else 0.0
        far_t = n_neg_comp / total_negatives if total_negatives > 0 else 0.0
        hard_neg_rejection = n_neg_incomp / total_negatives if total_negatives > 0 else 0.0
        uncertain_rate = n_neg_uncert / total_negatives if total_negatives > 0 else 0.0
        
        threshold_tradeoffs.append({
            'threshold': t,
            'astronomy_recall': round(astro_recall, 4),
            'non_astronomy_specificity': round(non_astro_spec, 4),
            'false_acceptance_rate': round(far_t, 4),
            'hard_negative_rejection_rate': round(hard_neg_rejection, 4),
            'uncertain_rate': round(uncertain_rate, 4)
        })
        
    # 4. Worst Failure Examples
    worst_fps = df_res[df_res['type'] == 'NEGATIVE'].sort_values(by='probability_astronomical', ascending=False).head(10).to_dict(orient='records')
    worst_fns = df_res[df_res['type'] == 'POSITIVE'].sort_values(by='probability_astronomical', ascending=True).head(10).to_dict(orient='records')
    
    # 5. Confusion Matrix Artifact Plot
    # Map decisions: COMPATIBLE -> 1, INCOMPATIBLE -> 0, UNCERTAIN -> 2
    y_true_cm = [1 if r['type'] == 'POSITIVE' else 0 for r in results]
    y_pred_cm = []
    for r in results:
        dec = r['predicted_decision']
        if dec == 'COMPATIBLE':
            y_pred_cm.append(1)
        elif dec == 'INCOMPATIBLE':
            y_pred_cm.append(0)
        else:
            y_pred_cm.append(2)
            
    fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
    cm = confusion_matrix(y_true_cm, y_pred_cm, labels=[1, 0, 2])
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Astronomical', 'Non-Astro', 'Uncertain'])
    disp.plot(cmap='Blues', ax=ax, values_format='d')
    ax.set_title('Domain Gate Adversarial Confusion Matrix', fontsize=11, pad=12)
    plt.tight_layout()
    plt.savefig(OUT_CM_PATH, dpi=150)
    plt.close(fig)
    
    # Write Final Output JSON
    output_meta = {
        'evaluation_timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        'total_samples': total_samples,
        'negative_samples': total_negatives,
        'positive_samples': total_positives,
        'overall_accuracy': round(overall_accuracy, 4),
        'false_acceptance_rate': round(overall_far, 4),
        'false_rejection_rate': round(overall_frr, 4),
        'astronomical_recall': round(positive_rec, 4),
        'hardest_negative_category': hardest_negative_cat,
        'current_thresholds': {
            'compatible': 0.80,
            'incompatible': 0.20
        },
        'per_category_summary': category_summary,
        'threshold_tradeoffs': threshold_tradeoffs,
        'worst_false_positives': worst_fps,
        'worst_false_negatives': worst_fns
    }
    
    with open(OUT_JSON_PATH, 'w') as f:
        json.dump(output_meta, f, indent=2)
        
    print(f"\nAdversarial Audit Completed Successfully!")
    print(f"  Results JSON: {OUT_JSON_PATH}")
    print(f"  Category CSV: {OUT_CSV_PATH}")
    print(f"  Confusion Matrix Plot: {OUT_CM_PATH}")

if __name__ == '__main__':
    run_adversarial_evaluation()
