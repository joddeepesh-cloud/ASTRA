import os
import json
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, roc_curve, auc, confusion_matrix, ConfusionMatrixDisplay
)

import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T
from torchvision.models import mobilenet_v3_small

MANIFEST_PATH = "ml/data/domain_gate_manifest.csv"
BEST_MODEL_PATH = "ml/models/domain_gate_best.pt"

THRESHOLD_ANALYSIS_PATH = "ml/artifacts/domain_gate_threshold_analysis.csv"
CONFUSION_MATRIX_PATH = "ml/artifacts/domain_gate_confusion_matrix.png"
ROC_CURVE_PATH = "ml/artifacts/domain_gate_roc_curve.png"
PR_CURVE_PATH = "ml/artifacts/domain_gate_pr_curve.png"

class DomainGateEvalDataset(Dataset):
    def __init__(self, df, transform=None):
        self.df = df.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = row['path']
        label = 1.0 if row['domain_label'] == 'ASTRONOMICAL' else (0.0 if row['domain_label'] == 'NON_ASTRONOMICAL' else -1.0)
        
        with Image.open(img_path) as img:
            img = img.convert('RGB')
            if self.transform:
                img = self.transform(img)
                
        return img, torch.tensor(label, dtype=torch.float32), idx

def get_eval_transform():
    return T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

def load_trained_model(device):
    checkpoint = torch.load(BEST_MODEL_PATH, map_location=device)
    model = mobilenet_v3_small()
    in_features = model.classifier[3].in_features
    model.classifier[3] = torch.nn.Linear(in_features, 1)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()
    return model, checkpoint

def run_predictions(model, loader, device):
    all_probs = []
    all_targets = []
    all_indices = []
    
    with torch.no_grad():
        for images, labels, idxs in loader:
            images = images.to(device)
            logits = model(images)
            probs = torch.sigmoid(logits).cpu().numpy().flatten()
            
            all_probs.extend(probs)
            all_targets.extend(labels.numpy().flatten())
            all_indices.extend(idxs.numpy().flatten())
            
    return np.array(all_probs), np.array(all_targets), np.array(all_indices)

def evaluate_threshold_sweep(val_probs, val_targets):
    print("--- EVALUATING VALIDATION THRESHOLD SWEEP (VAL ONLY) ---")
    thresholds = np.linspace(0.05, 0.95, 19)
    rows = []
    
    for th in thresholds:
        preds = (val_probs >= th).astype(int)
        acc = accuracy_score(val_targets, preds)
        prec = precision_score(val_targets, preds, zero_division=0)
        rec = recall_score(val_targets, preds, zero_division=0) # Astro recall
        f1 = f1_score(val_targets, preds, zero_division=0)
        
        non_astro_mask = (val_targets == 0)
        non_astro_spec = recall_score(1 - val_targets[non_astro_mask], 1 - preds[non_astro_mask], zero_division=0)
        
        fp = ((preds == 1) & (val_targets == 0)).sum()
        fn = ((preds == 0) & (val_targets == 1)).sum()
        tn = ((preds == 0) & (val_targets == 0)).sum()
        tp = ((preds == 1) & (val_targets == 1)).sum()
        
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        rows.append({
            'threshold': round(th, 2),
            'astronomy_recall': round(rec, 4),
            'astronomy_precision': round(prec, 4),
            'non_astronomy_specificity': round(non_astro_spec, 4),
            'false_positive_rate': round(fpr, 4),
            'false_negative_rate': round(fnr, 4),
            'accuracy': round(acc, 4),
            'f1': round(f1, 4)
        })
        
    df_sweep = pd.DataFrame(rows)
    df_sweep.to_csv(THRESHOLD_ANALYSIS_PATH, index=False)
    print(f"Saved validation threshold sweep to {THRESHOLD_ANALYSIS_PATH}")
    print(df_sweep.to_string(index=False))
    return df_sweep

def main():
    device = torch.device('mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu'))
    print(f"Loading trained domain gate model onto device '{device}'...")
    
    model, checkpoint = load_trained_model(device)
    df_manifest = pd.read_csv(MANIFEST_PATH)
    eval_tf = get_eval_transform()
    
    # 1. Validation Set Predictions & Threshold Sweep
    df_val = df_manifest[df_manifest['split'] == 'VAL']
    val_dataset = DomainGateEvalDataset(df_val, transform=eval_tf)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    val_probs, val_targets, _ = run_predictions(model, val_loader, device)
    
    df_sweep = evaluate_threshold_sweep(val_probs, val_targets)
    
    # Select Thresholds based on Validation ONLY
    # High Threshold = 0.80 (Compatible), Low Threshold = 0.20 (Incompatible)
    compatible_th = 0.80
    incompatible_th = 0.20
    
    print(f"\nSelected Threshold Policy (from VAL): COMPATIBLE >= {compatible_th}, INCOMPATIBLE <= {incompatible_th}, otherwise UNCERTAIN.")
    
    # 2. Touch Held-Out TEST Set EXACTLY ONCE
    print("\n" + "=" * 60)
    print("  EVALUATING HELDOUT TEST SET (UNTOUCHED UNTIL NOW)")
    print("=" * 60)
    
    df_test = df_manifest[df_manifest['split'] == 'TEST']
    test_dataset = DomainGateEvalDataset(df_test, transform=eval_tf)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    test_probs, test_targets, _ = run_predictions(model, test_loader, device)
    
    test_preds_binary = (test_probs >= 0.50).astype(int)
    
    test_acc = accuracy_score(test_targets, test_preds_binary)
    test_prec = precision_score(test_targets, test_preds_binary, zero_division=0)
    test_rec = recall_score(test_targets, test_preds_binary, zero_division=0)
    test_f1 = f1_score(test_targets, test_preds_binary, zero_division=0)
    test_roc = roc_auc_score(test_targets, test_probs)
    
    test_p_prec, test_p_rec, _ = precision_recall_curve(test_targets, test_probs)
    test_pr_auc = auc(test_p_rec, test_p_prec)
    
    test_astro_mask = (test_targets == 1)
    test_non_astro_mask = (test_targets == 0)
    
    test_astro_rec = recall_score(test_targets[test_astro_mask], test_preds_binary[test_astro_mask], zero_division=0)
    test_non_astro_spec = recall_score(1 - test_targets[test_non_astro_mask], 1 - test_preds_binary[test_non_astro_mask], zero_division=0)
    
    print(f"Test Accuracy:                {test_acc*100:.2f}%")
    print(f"Test Precision:               {test_prec*100:.2f}%")
    print(f"Test Recall:                  {test_rec*100:.2f}%")
    print(f"Test F1 Score:                {test_f1:.4f}")
    print(f"Test ROC-AUC:                 {test_roc:.4f}")
    print(f"Test PR-AUC:                  {test_pr_auc:.4f}")
    print(f"Test Astronomy Recall:        {test_astro_rec*100:.2f}%")
    print(f"Test Non-Astronomy Specificity: {test_non_astro_spec*100:.2f}%")
    
    # 3. Evaluate Hard Negatives Subset
    print("\n--- HARD-NEGATIVE SUBSET EVALUATION ---")
    df_hard_neg = df_manifest[(df_manifest['split'] == 'TEST') & (df_manifest['subcategory'] == 'hard_negatives')]
    if len(df_hard_neg) > 0:
        hn_dataset = DomainGateEvalDataset(df_hard_neg, transform=eval_tf)
        hn_loader = DataLoader(hn_dataset, batch_size=32, shuffle=False)
        hn_probs, hn_targets, _ = run_predictions(model, hn_loader, device)
        
        hn_rejected = (hn_probs <= incompatible_th).sum()
        hn_uncertain = ((hn_probs > incompatible_th) & (hn_probs < compatible_th)).sum()
        hn_accepted = (hn_probs >= compatible_th).sum()
        
        print(f"Hard Negatives Test Count: {len(df_hard_neg)}")
        print(f"  Correctly Rejected (<= {incompatible_th}): {hn_rejected} ({hn_rejected/len(df_hard_neg)*100:.1f}%)")
        print(f"  Uncertain Routed ({incompatible_th} - {compatible_th}): {hn_uncertain} ({hn_uncertain/len(df_hard_neg)*100:.1f}%)")
        print(f"  False Acceptance (>= {compatible_th}): {hn_accepted} ({hn_accepted/len(df_hard_neg)*100:.1f}%)")
    else:
        print("No hard negatives in test split.")
        
    # 4. Evaluate Ambiguous REVIEW Set
    print("\n--- AMBIGUOUS / REVIEW SET EVALUATION ---")
    df_review = df_manifest[df_manifest['split'] == 'REVIEW']
    rev_dataset = DomainGateEvalDataset(df_review, transform=eval_tf)
    rev_loader = DataLoader(rev_dataset, batch_size=32, shuffle=False)
    rev_probs, _, _ = run_predictions(model, rev_loader, device)
    
    rev_compatible = (rev_probs >= compatible_th).sum()
    rev_incompatible = (rev_probs <= incompatible_th).sum()
    rev_uncertain = ((rev_probs > incompatible_th) & (rev_probs < compatible_th)).sum()
    
    print(f"Ambiguous Review Count: {len(df_review)}")
    print(f"  Evaluated as COMPATIBLE (>= {compatible_th}):   {rev_compatible} ({rev_compatible/len(df_review)*100:.1f}%)")
    print(f"  Evaluated as INCOMPATIBLE (<= {incompatible_th}): {rev_incompatible} ({rev_incompatible/len(df_review)*100:.1f}%)")
    print(f"  Evaluated as UNCERTAIN ({incompatible_th} - {compatible_th}):  {rev_uncertain} ({rev_uncertain/len(df_review)*100:.1f}%)")
    
    # 5. Plot Confusion Matrix, ROC, PR Curves
    print("\nGenerating evaluation plots...")
    
    # Confusion Matrix
    cm = confusion_matrix(test_targets, test_preds_binary)
    fig, ax = plt.subplots(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['NON_ASTRONOMICAL', 'ASTRONOMICAL'])
    disp.plot(cmap='Blues', ax=ax)
    plt.title("Domain Gate — Held-Out Test Set Confusion Matrix")
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH, dpi=150)
    plt.close(fig)
    print(f"Saved confusion matrix to {CONFUSION_MATRIX_PATH}")
    
    # ROC Curve
    fpr, tpr, _ = roc_curve(test_targets, test_probs)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color='#0284c7', lw=2, label=f'ROC curve (AUC = {test_roc:.4f})')
    ax.plot([0, 1], [0, 1], color='#475569', lw=1.5, linestyle='--')
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('Domain Gate — ROC Curve')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(ROC_CURVE_PATH, dpi=150)
    plt.close(fig)
    print(f"Saved ROC curve to {ROC_CURVE_PATH}")
    
    # PR Curve
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(test_p_rec, test_p_prec, color='#059669', lw=2, label=f'PR curve (AUC = {test_pr_auc:.4f})')
    ax.set_xlabel('Recall')
    ax.set_ylabel('Precision')
    ax.set_title('Domain Gate — Precision-Recall Curve')
    ax.legend(loc='lower left')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(PR_CURVE_PATH, dpi=150)
    plt.close(fig)
    print(f"Saved PR curve to {PR_CURVE_PATH}")
    
    # Save Machine-Readable Evaluation Metrics
    eval_results = {
        'test_metrics': {
            'accuracy': float(test_acc),
            'precision': float(test_prec),
            'recall': float(test_rec),
            'f1': float(test_f1),
            'roc_auc': float(test_roc),
            'pr_auc': float(test_pr_auc),
            'astronomy_recall': float(test_astro_rec),
            'non_astronomy_specificity': float(test_non_astro_spec)
        },
        'thresholds': {
            'compatible_threshold': compatible_th,
            'incompatible_threshold': incompatible_th
        },
        'ambiguous_review_distribution': {
            'total': len(df_review),
            'compatible_count': int(rev_compatible),
            'incompatible_count': int(rev_incompatible),
            'uncertain_count': int(rev_uncertain)
        }
    }
    
    with open("ml/artifacts/domain_gate_eval_summary.json", "w") as f:
        json.dump(eval_results, f, indent=2)

if __name__ == '__main__':
    main()
