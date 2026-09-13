import os
import sys
import json
import datetime
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml.src.galaxy_zoo_dataset import CLASS_TO_IDX, IDX_TO_CLASS

def build_reference():
    print("=" * 70)
    print("ASTRA STEP 1: BUILDING TRAINING-ONLY REFERENCE DISTRIBUTION")
    print("=" * 70)

    project_root = os.getcwd()
    emb_file = os.path.join(project_root, "ml/artifacts/galaxy_zoo_embeddings.npy")
    idx_file = os.path.join(project_root, "ml/artifacts/galaxy_zoo_embedding_index.csv")
    out_ref_file = os.path.join(project_root, "ml/artifacts/triage_reference.json")

    embeddings = np.load(emb_file)
    df_idx = pd.read_csv(idx_file)

    # STRICT CHECK: Filter to ONLY training split samples (8,000)
    train_mask = df_idx['split'] == 'train'
    train_embs = embeddings[train_mask]
    train_labels = df_idx.loc[train_mask, 'target_4class'].map(CLASS_TO_IDX).values
    train_asset_ids = df_idx.loc[train_mask, 'asset_id'].values

    num_train = len(train_embs)
    print(f"Verified training sample count: {num_train} (Must be exactly 8,000)")
    assert num_train == 8000, f"Expected 8000 training samples, found {num_train}"

    # 1. Compute Centroids for each morphology class using training embeddings only
    centroids_raw = {}
    centroids_normalized = {}
    class_counts = {}

    for c_idx in range(4):
        c_name = IDX_TO_CLASS[c_idx]
        mask_c = (train_labels == c_idx)
        c_embs = train_embs[mask_c]
        c_cnt = int(np.sum(mask_c))
        class_counts[c_name] = c_cnt

        mean_vec = np.mean(c_embs, axis=0)
        norm_val = np.linalg.norm(mean_vec)
        norm_vec = mean_vec / (norm_val + 1e-12)

        centroids_raw[c_name] = [float(round(v, 6)) for v in mean_vec]
        centroids_normalized[c_name] = [float(round(v, 6)) for v in norm_vec]

    # 2. Compute Cosine Distances across training set to assigned class centroid
    # L2 normalize training embeddings
    norm_train_embs = train_embs / (np.linalg.norm(train_embs, axis=1, keepdims=True) + 1e-12)

    train_cosine_dists = []
    train_per_class_dists = {c_name: [] for c_name in CLASS_TO_IDX.keys()}

    for i in range(num_train):
        c_idx = train_labels[i]
        c_name = IDX_TO_CLASS[c_idx]
        c_norm = np.array(centroids_normalized[c_name])
        e_norm = norm_train_embs[i]

        cos_d = float(1.0 - np.dot(e_norm, c_norm))
        train_cosine_dists.append(cos_d)
        train_per_class_dists[c_name].append(cos_d)

    train_cosine_dists = np.array(train_cosine_dists)

    def calc_dist_stats(d_arr):
        return {
            "count": len(d_arr),
            "min": float(round(np.min(d_arr), 6)),
            "max": float(round(np.max(d_arr), 6)),
            "mean": float(round(np.mean(d_arr), 6)),
            "std": float(round(np.std(d_arr), 6)),
            "p5": float(round(np.percentile(d_arr, 5), 6)),
            "p10": float(round(np.percentile(d_arr, 10), 6)),
            "p25": float(round(np.percentile(d_arr, 25), 6)),
            "p50": float(round(np.percentile(d_arr, 50), 6)),
            "p75": float(round(np.percentile(d_arr, 75), 6)),
            "p80": float(round(np.percentile(d_arr, 80), 6)),
            "p90": float(round(np.percentile(d_arr, 90), 6)),
            "p95": float(round(np.percentile(d_arr, 95), 6)),
            "p99": float(round(np.percentile(d_arr, 99), 6))
        }

    overall_stats = calc_dist_stats(train_cosine_dists)
    per_class_stats = {c_name: calc_dist_stats(np.array(train_per_class_dists[c_name])) for c_name in CLASS_TO_IDX.keys()}

    reference_artifact = {
        "metadata": {
            "title": "ASTRA Scientific Triage Reference Distribution",
            "model_version": "best_model.pt (Epoch 10)",
            "backbone": "efficientnet_b0",
            "embedding_dim": 1280,
            "training_samples_used": 8000,
            "validation_samples_used": 0,
            "test_samples_used": 0,
            "creation_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        },
        "class_names": list(CLASS_TO_IDX.keys()),
        "class_sample_counts": class_counts,
        "centroids_normalized": centroids_normalized,
        "overall_training_distance_stats": overall_stats,
        "per_class_training_distance_stats": per_class_stats,
        "normalization_bounds": {
            "cosine_dist_min": overall_stats["min"],
            "cosine_dist_max": overall_stats["max"],
            "cosine_dist_p5": overall_stats["p5"],
            "cosine_dist_p50": overall_stats["p50"],
            "cosine_dist_p95": overall_stats["p95"]
        },
        "priority_thresholds": {
            "LOW": {"max_score": 0.30, "description": "Routine observation consistent with reference distribution"},
            "MEDIUM": {"min_score": 0.30, "max_score": 0.50, "description": "Worth monitoring; subtle novelty or minor classification ambiguity"},
            "HIGH": {"min_score": 0.50, "max_score": 0.70, "description": "Prioritize for scientific review; elevated novelty, uncertainty, or oddity"},
            "CRITICAL": {"min_score": 0.70, "description": "Strongly prioritize for scientific review; multiple elevated triage signals"}
        }
    }

    with open(out_ref_file, "w") as f:
        json.dump(reference_artifact, f, indent=2)

    print(f"Successfully saved triage reference artifact to: {out_ref_file}")
    print(f"File Size: {round(os.path.getsize(out_ref_file)/1024, 2)} KB")
    print(f"Overall Training Cosine Dist Min: {overall_stats['min']}, Max: {overall_stats['max']}, Mean: {overall_stats['mean']}")

if __name__ == "__main__":
    build_reference()
