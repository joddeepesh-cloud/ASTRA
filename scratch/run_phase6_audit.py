import sys
import os
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, confusion_matrix
)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.src.galaxy_zoo_dataset import GalaxyZooDataset, CLASS_TO_IDX, IDX_TO_CLASS, ATTRIBUTE_COLS
from ml.src.model import GalaxyZooMultiHeadCNN

def run_audit():
    print("=" * 70)
    print("ASTRA PHASE 6 AUDIT — EXECUTING STEPS 1 TO 9")
    print("=" * 70)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")

    project_root = os.getcwd()
    best_model_path = os.path.join(project_root, "ml/models/best_model.pt")
    latest_model_path = os.path.join(project_root, "ml/models/latest_model.pt")
    csv_path = os.path.join(project_root, "ml/data/splits/subset_10k_scientific_targets.csv")
    img_dir = os.path.join(project_root, "ml/data/processed/galaxy_zoo/images")
    artifacts_dir = os.path.join(project_root, "ml/artifacts")
    docs_dir = os.path.join(project_root, "docs")
    os.makedirs(artifacts_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # STEP 1: Checkpoint Audit
    # -------------------------------------------------------------------------
    print("\n--- STEP 1: Checkpoint Audit ---")
    best_ckpt = torch.load(best_model_path, map_location='cpu')
    latest_ckpt = torch.load(latest_model_path, map_location='cpu')

    model_dummy = GalaxyZooMultiHeadCNN(
        backbone_name=best_ckpt.get('backbone', 'efficientnet_b0'),
        num_classes=4,
        num_attributes=6,
        pretrained=False
    )
    total_params = sum(p.numel() for p in model_dummy.parameters())

    step1_report = {
        "best_model": {
            "path": best_model_path,
            "file_size_mb": round(os.path.getsize(best_model_path) / (1024 * 1024), 2),
            "completed_epoch": best_ckpt.get("epoch"),
            "val_loss": best_ckpt.get("val_loss"),
            "val_acc": best_ckpt.get("val_acc"),
            "val_macro_f1": best_ckpt.get("val_macro_f1"),
            "backbone": best_ckpt.get("backbone"),
            "num_classes": best_ckpt.get("num_classes"),
            "classes": best_ckpt.get("idx_to_class"),
            "attribute_cols": best_ckpt.get("attribute_cols"),
            "embedding_dim": best_ckpt.get("embedding_dim"),
            "input_size": best_ckpt.get("input_size"),
            "normalization": best_ckpt.get("normalization"),
            "has_optimizer_state": "optimizer_state_dict" in best_ckpt,
            "has_scheduler_state": ("scheduler_state_dict" in best_ckpt and best_ckpt["scheduler_state_dict"] is not None),
            "total_params": total_params
        },
        "latest_model": {
            "path": latest_model_path,
            "file_size_mb": round(os.path.getsize(latest_model_path) / (1024 * 1024), 2),
            "completed_epoch": latest_ckpt.get("epoch"),
            "val_loss": latest_ckpt.get("val_loss"),
            "val_acc": latest_ckpt.get("val_acc"),
            "val_macro_f1": latest_ckpt.get("val_macro_f1"),
            "train_loss": latest_ckpt.get("train_loss"),
            "train_acc": latest_ckpt.get("train_acc"),
            "has_optimizer_state": "optimizer_state_dict" in latest_ckpt,
            "has_scheduler_state": ("scheduler_state_dict" in latest_ckpt and latest_ckpt["scheduler_state_dict"] is not None)
        }
    }
    print("Best Checkpoint Epoch:", step1_report["best_model"]["completed_epoch"])
    print("Latest Checkpoint Epoch:", step1_report["latest_model"]["completed_epoch"])

    # Load Model Weights from best_model.pt
    model = GalaxyZooMultiHeadCNN(
        backbone_name=best_ckpt.get('backbone', 'efficientnet_b0'),
        num_classes=4,
        num_attributes=6,
        pretrained=False
    )
    model.load_state_dict(best_ckpt['model_state_dict'])
    model.to(device)
    model.eval()

    # -------------------------------------------------------------------------
    # STEP 2 & STEP 3 & STEP 4: Test Evaluation, Confusion Matrix & Calibration Audit
    # -------------------------------------------------------------------------
    print("\n--- STEP 2, 3, 4: Running Test Set Evaluation & Calibration Audit ---")
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    test_ds = GalaxyZooDataset(csv_path=csv_path, img_dir=img_dir, split='test', transform=val_transform)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=0)

    all_asset_ids = []
    all_targets = []
    all_preds = []
    all_probs = []
    all_attr_targets = []
    all_attr_preds = []

    with torch.no_grad():
        for batch in test_loader:
            imgs = batch['image'].to(device)
            cls_targets = batch['class_target']
            attr_targets = batch['attribute_targets']
            asset_ids = batch['asset_id']

            cls_logits, attr_probs, _ = model(imgs)
            probs = torch.softmax(cls_logits, dim=1)
            preds = torch.argmax(probs, dim=1)

            all_asset_ids.extend(asset_ids.numpy())
            all_targets.extend(cls_targets.numpy())
            all_preds.extend(preds.cpu().numpy())
            all_probs.append(probs.cpu().numpy())
            all_attr_targets.append(attr_targets.numpy())
            all_attr_preds.append(attr_probs.cpu().numpy())

    all_probs = np.vstack(all_probs)
    all_attr_targets = np.vstack(all_attr_targets)
    all_attr_preds = np.vstack(all_attr_preds)

    targets_arr = np.array(all_targets)
    preds_arr = np.array(all_preds)

    # Metrics
    acc = accuracy_score(targets_arr, preds_arr)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(targets_arr, preds_arr, average='macro', zero_division=0)
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(targets_arr, preds_arr, average='weighted', zero_division=0)
    per_class_p, per_class_r, per_class_f1, per_class_supp = precision_recall_fscore_support(targets_arr, preds_arr, average=None, zero_division=0)

    class_names = [IDX_TO_CLASS[i] for i in range(4)]
    per_class_metrics = {}
    for i, c_name in enumerate(class_names):
        per_class_metrics[c_name] = {
            "precision": float(round(per_class_p[i], 4)),
            "recall": float(round(per_class_r[i], 4)),
            "f1_score": float(round(per_class_f1[i], 4)),
            "support": int(per_class_supp[i])
        }

    # Attribute MAE
    attr_mae = np.mean(np.abs(all_attr_targets - all_attr_preds), axis=0)
    attr_mae_dict = {col: float(round(attr_mae[i], 4)) for i, col in enumerate(ATTRIBUTE_COLS)}
    mean_attr_mae = float(round(np.mean(attr_mae), 4))

    test_report = {
        "evaluation_split": "test",
        "num_samples": len(targets_arr),
        "overall_accuracy": float(round(acc, 4)),
        "macro_precision": float(round(macro_p, 4)),
        "macro_recall": float(round(macro_r, 4)),
        "macro_f1": float(round(macro_f1, 4)),
        "weighted_precision": float(round(weighted_p, 4)),
        "weighted_recall": float(round(weighted_r, 4)),
        "weighted_f1": float(round(weighted_f1, 4)),
        "per_class_metrics": per_class_metrics,
        "mean_attribute_mae": mean_attr_mae,
        "per_attribute_mae": attr_mae_dict
    }

    with open(os.path.join(artifacts_dir, "galaxy_zoo_test_report.json"), "w") as f:
        json.dump(test_report, f, indent=2)
    print("Saved test report to galaxy_zoo_test_report.json")

    # Step 3: Confusion Matrix Plot
    cm = confusion_matrix(targets_arr, preds_arr)
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm, cmap='Blues')
    plt.colorbar(im, ax=ax)
    ax.set_xticks(np.arange(len(class_names)))
    ax.set_yticks(np.arange(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha="right")
    ax.set_yticklabels(class_names)
    ax.set_title("Galaxy Zoo Multi-Head CNN — Test Set Confusion Matrix")
    ax.set_ylabel("True Class")
    ax.set_xlabel("Predicted Class")

    # Loop over data dimensions and create text annotations.
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            text = ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")

    plt.tight_layout()
    cm_path_final = os.path.join(artifacts_dir, "galaxy_zoo_confusion_matrix_final.png")
    plt.savefig(cm_path_final, dpi=300)
    plt.close()
    print("Saved final confusion matrix plot to galaxy_zoo_confusion_matrix_final.png")

    # Step 4: Calibration / Confidence Audit
    max_confs = np.max(all_probs, axis=1)
    eps = 1e-12
    entropies = -np.sum(all_probs * np.log2(all_probs + eps), axis=1)

    buckets = [
        ("0.00–0.49", 0.0, 0.4999),
        ("0.50–0.59", 0.5, 0.5999),
        ("0.60–0.69", 0.6, 0.6999),
        ("0.70–0.79", 0.7, 0.7999),
        ("0.80–0.89", 0.8, 0.8999),
        ("0.90–1.00", 0.9, 1.0)
    ]

    confidence_audit_results = []
    for label, b_min, b_max in buckets:
        mask = (max_confs >= b_min) & (max_confs <= b_max)
        cnt = int(np.sum(mask))
        if cnt > 0:
            b_acc = float(round(accuracy_score(targets_arr[mask], preds_arr[mask]), 4))
            b_avg_conf = float(round(np.mean(max_confs[mask]), 4))
        else:
            b_acc = 0.0
            b_avg_conf = 0.0
        confidence_audit_results.append({
            "bucket": label,
            "sample_count": cnt,
            "fraction_of_total": float(round(cnt / len(targets_arr), 4)),
            "avg_confidence": b_avg_conf,
            "accuracy": b_acc
        })

    confidence_report = {
        "total_test_samples": len(targets_arr),
        "mean_confidence": float(round(np.mean(max_confs), 4)),
        "median_confidence": float(round(np.median(max_confs), 4)),
        "mean_entropy": float(round(np.mean(entropies), 4)),
        "confidence_buckets": confidence_audit_results
    }

    with open(os.path.join(artifacts_dir, "galaxy_zoo_confidence_audit.json"), "w") as f:
        json.dump(confidence_report, f, indent=2)
    print("Saved confidence audit to galaxy_zoo_confidence_audit.json")

    # -------------------------------------------------------------------------
    # STEP 5: Embedding Sanity Check
    # -------------------------------------------------------------------------
    print("\n--- STEP 5: Embedding Sanity Check ---")
    emb_file = os.path.join(artifacts_dir, "galaxy_zoo_embeddings.npy")
    idx_file = os.path.join(artifacts_dir, "galaxy_zoo_embedding_index.csv")

    embeddings = np.load(emb_file)
    df_idx = pd.read_csv(idx_file)
    df_scientific = pd.read_csv(csv_path)
    if 'prob_odd' not in df_idx.columns:
        df_idx = df_idx.merge(df_scientific[['asset_id', 'prob_odd']], on='asset_id', how='left')

    has_nan = bool(np.isnan(embeddings).any())
    has_inf = bool(np.isinf(embeddings).any())
    l2_norms = np.linalg.norm(embeddings, axis=1)

    embedding_audit = {
        "embedding_shape": list(embeddings.shape),
        "index_row_count": len(df_idx),
        "has_nans": has_nan,
        "has_infs": has_inf,
        "stats": {
            "mean": float(round(np.mean(embeddings), 6)),
            "std": float(round(np.std(embeddings), 6)),
            "min": float(round(np.min(embeddings), 6)),
            "max": float(round(np.max(embeddings), 6))
        },
        "l2_norm_distribution": {
            "mean": float(round(np.mean(l2_norms), 4)),
            "std": float(round(np.std(l2_norms), 4)),
            "min": float(round(np.min(l2_norms), 4)),
            "p25": float(round(np.percentile(l2_norms, 25), 4)),
            "median": float(round(np.median(l2_norms), 4)),
            "p75": float(round(np.percentile(l2_norms, 75), 4)),
            "max": float(round(np.max(l2_norms), 4))
        },
        "split_counts": df_idx['split'].value_counts().to_dict()
    }

    with open(os.path.join(artifacts_dir, "embedding_audit.json"), "w") as f:
        json.dump(embedding_audit, f, indent=2)
    print("Saved embedding audit to embedding_audit.json")

    # -------------------------------------------------------------------------
    # STEP 6: Class-Centroid Distance Analysis
    # -------------------------------------------------------------------------
    print("\n--- STEP 6: Class-Centroid Distance Analysis ---")
    train_mask = df_idx['split'] == 'train'
    val_mask = df_idx['split'] == 'val'
    test_mask = df_idx['split'] == 'test'

    train_embs = embeddings[train_mask]
    train_classes = df_idx.loc[train_mask, 'target_4class'].map(CLASS_TO_IDX).values

    # Calculate class centroids using ONLY training embeddings
    centroids = {}
    normalized_centroids = {}
    for c_idx in range(4):
        c_mask = (train_classes == c_idx)
        c_emb = train_embs[c_mask]
        c_mean = np.mean(c_emb, axis=0)
        centroids[c_idx] = c_mean
        normalized_centroids[c_idx] = c_mean / (np.linalg.norm(c_mean) + 1e-12)

    # Compute distances for test samples
    test_embs = embeddings[test_mask]
    norm_test_embs = test_embs / (np.linalg.norm(test_embs, axis=1, keepdims=True) + 1e-12)

    pred_cosine_dists = []
    pred_euclidean_dists = []

    for i in range(len(test_embs)):
        p_c = preds_arr[i]
        emb = test_embs[i]
        n_emb = norm_test_embs[i]

        c_norm = normalized_centroids[p_c]
        c_orig = centroids[p_c]

        cos_d = 1.0 - np.dot(n_emb, c_norm)
        euc_d = np.linalg.norm(emb - c_orig)

        pred_cosine_dists.append(cos_d)
        pred_euclidean_dists.append(euc_d)

    pred_cosine_dists = np.array(pred_cosine_dists)
    pred_euclidean_dists = np.array(pred_euclidean_dists)

    p_odd_test = df_idx.loc[test_mask, 'prob_odd'].values
    corr_cos_conf = float(round(np.corrcoef(pred_cosine_dists, max_confs)[0, 1], 4))
    corr_cos_podd = float(round(np.corrcoef(pred_cosine_dists, p_odd_test)[0, 1], 4))

    centroid_analysis = {
        "distance_metric": "cosine_distance",
        "pred_cosine_distance": {
            "mean": float(round(np.mean(pred_cosine_dists), 4)),
            "median": float(round(np.median(pred_cosine_dists), 4)),
            "std": float(round(np.std(pred_cosine_dists), 4)),
            "min": float(round(np.min(pred_cosine_dists), 4)),
            "max": float(round(np.max(pred_cosine_dists), 4))
        },
        "pred_euclidean_distance": {
            "mean": float(round(np.mean(pred_euclidean_dists), 4)),
            "median": float(round(np.median(pred_euclidean_dists), 4)),
            "std": float(round(np.std(pred_euclidean_dists), 4)),
            "min": float(round(np.min(pred_euclidean_dists), 4)),
            "max": float(round(np.max(pred_euclidean_dists), 4))
        },
        "correlations": {
            "cosine_dist_vs_confidence": corr_cos_conf,
            "cosine_dist_vs_p_odd": corr_cos_podd
        }
    }

    # -------------------------------------------------------------------------
    # STEP 7: p_odd / Unusualness Analysis
    # -------------------------------------------------------------------------
    print("\n--- STEP 7: p_odd / Unusualness Analysis ---")
    p_odd_all = df_idx['prob_odd'].values

    def calc_p_odd_stats(arr):
        return {
            "count": len(arr),
            "mean": float(round(np.mean(arr), 4)),
            "median": float(round(np.median(arr), 4)),
            "std": float(round(np.std(arr), 4)),
            "p25": float(round(np.percentile(arr, 25), 4)),
            "p50": float(round(np.percentile(arr, 50), 4)),
            "p75": float(round(np.percentile(arr, 75), 4)),
            "p90": float(round(np.percentile(arr, 90), 4)),
            "p95": float(round(np.percentile(arr, 95), 4)),
            "p99": float(round(np.percentile(arr, 99), 4)),
            "frac_ge_0_5": float(round(np.mean(arr >= 0.5), 4)),
            "frac_ge_0_7": float(round(np.mean(arr >= 0.7), 4)),
            "frac_ge_0_8": float(round(np.mean(arr >= 0.8), 4))
        }

    p_odd_report = {
        "all_10k": calc_p_odd_stats(p_odd_all),
        "train": calc_p_odd_stats(df_idx.loc[train_mask, 'prob_odd'].values),
        "val": calc_p_odd_stats(df_idx.loc[val_mask, 'prob_odd'].values),
        "test": calc_p_odd_stats(p_odd_test)
    }

    # -------------------------------------------------------------------------
    # STEP 8: Preliminary Triage Score Formulation
    # -------------------------------------------------------------------------
    print("\n--- STEP 8: Preliminary Triage Score Formulation ---")
    cos_min = np.min(pred_cosine_dists)
    cos_max = np.max(pred_cosine_dists)
    norm_cos_dists = np.clip((pred_cosine_dists - cos_min) / (cos_max - cos_min + 1e-12), 0.0, 1.0)
    norm_uncertainty = np.clip((1.0 - max_confs) / 0.75, 0.0, 1.0)

    triage_scores = 0.35 * norm_cos_dists + 0.35 * norm_uncertainty + 0.30 * p_odd_test
    triage_scores = np.clip(triage_scores, 0.0, 1.0)

    triage_analysis = {
        "formula": "experimental_triage_score = 0.35 * norm_cosine_dist + 0.35 * norm_uncertainty + 0.30 * p_odd",
        "description": "Heuristic prioritization score combining embedding space distance, classification entropy/uncertainty, and scientific p_odd attribute.",
        "test_distribution": {
            "mean": float(round(np.mean(triage_scores), 4)),
            "median": float(round(np.median(triage_scores), 4)),
            "std": float(round(np.std(triage_scores), 4)),
            "min": float(round(np.min(triage_scores), 4)),
            "p25": float(round(np.percentile(triage_scores, 25), 4)),
            "p75": float(round(np.percentile(triage_scores, 75), 4)),
            "p90": float(round(np.percentile(triage_scores, 90), 4)),
            "max": float(round(np.max(triage_scores), 4))
        },
        "p_odd_stats": p_odd_report,
        "centroid_distance_stats": centroid_analysis
    }

    with open(os.path.join(artifacts_dir, "triage_signal_analysis.json"), "w") as f:
        json.dump(triage_analysis, f, indent=2)
    print("Saved triage signal analysis to triage_signal_analysis.json")

    # -------------------------------------------------------------------------
    # STEP 9: Representative Observations Selection
    # -------------------------------------------------------------------------
    print("\n--- STEP 9: Representative Observations Selection ---")
    test_df_idx = df_idx[test_mask].reset_index(drop=True)

    smooth_mask = (preds_arr == 0) & (targets_arr == 0)
    idx_high_smooth = np.where(smooth_mask)[0][np.argmax(max_confs[smooth_mask])]

    edge_mask = (preds_arr == 1) & (targets_arr == 1)
    idx_high_edge = np.where(edge_mask)[0][np.argmax(max_confs[edge_mask])]

    feat_mask = (preds_arr == 2) & (targets_arr == 2)
    idx_high_feat = np.where(feat_mask)[0][np.argmax(max_confs[feat_mask])]

    spiral_mask = (preds_arr == 3) & (targets_arr == 3)
    idx_high_spiral = np.where(spiral_mask)[0][np.argmax(max_confs[spiral_mask])]

    idx_uncertain = np.argmin(max_confs)
    idx_high_podd = np.argmax(p_odd_test)
    idx_high_dist = np.argmax(pred_cosine_dists)

    disagree_metric = max_confs * triage_scores
    idx_disagree = np.argmax(disagree_metric)

    selected_indices = [
        ("High-Confidence SMOOTH", idx_high_smooth),
        ("High-Confidence EDGE_ON", idx_high_edge),
        ("High-Confidence FEATURED_DISK", idx_high_feat),
        ("High-Confidence SPIRAL", idx_high_spiral),
        ("High Uncertainty", idx_uncertain),
        ("High Scientific p_odd", idx_high_podd),
        ("High Embedding Distance (Novelty)", idx_high_dist),
        ("High Confidence / High Priority Disagreement", idx_disagree)
    ]

    example_rows = []
    for label_desc, idx_sel in selected_indices:
        asset_id = int(test_df_idx.loc[idx_sel, 'asset_id'])
        t_cls = IDX_TO_CLASS[targets_arr[idx_sel]]
        p_cls = IDX_TO_CLASS[preds_arr[idx_sel]]
        conf = float(round(max_confs[idx_sel], 4))
        p_o = float(round(p_odd_test[idx_sel], 4))
        d_cos = float(round(pred_cosine_dists[idx_sel], 4))
        t_score = float(round(triage_scores[idx_sel], 4))

        example_rows.append({
            "category": label_desc,
            "asset_id": asset_id,
            "split": "test",
            "true_class": t_cls,
            "predicted_class": p_cls,
            "class_confidence": conf,
            "p_odd": p_o,
            "embedding_distance": d_cos,
            "experimental_triage_score": t_score
        })

    df_examples = pd.DataFrame(example_rows)
    df_examples.to_csv(os.path.join(artifacts_dir, "model_audit_examples.csv"), index=False)
    print("Saved representative examples to model_audit_examples.csv")

    print("\n=" * 70)
    print("AUDIT STEPS 1 TO 9 COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_audit()
