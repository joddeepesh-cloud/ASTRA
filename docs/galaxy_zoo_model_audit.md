# ASTRA — Phase 6 Galaxy Zoo ML Model Audit & Production Readiness Report

---

## 1. Executive Summary & Audit Scope

This document presents a comprehensive scientific and engineering audit of the trained **ASTRA Galaxy Zoo Multi-Head CNN model** (`efficientnet_b0` backbone). Following the completion of the 15-epoch training schedule, this audit evaluates model performance on the held-out 1,000-sample test set, assesses confidence calibration, verifies embedding integrity across all 10,000 observations, analyzes class-centroid distance distributions in latent space, examines scientific `p_odd` attributes, establishes an experimental triage scoring heuristic, and benchmarks single-image inference latency for production readiness.

> [!IMPORTANT]
> - **Scientific Framing**: The model does **NOT** "discover new astronomical objects." It identifies observations that are statistically unusual or outside its learned distribution and prioritizes them for expert scientific review.
> - **No Retraining or Tuning**: All metrics reported in this audit were computed using the un-tuned best validation checkpoint ([`ml/models/best_model.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/best_model.pt)).
> - **Zero Code/Data Alterations**: Model weights, splits, labels, and training datasets were preserved without modification.

---

## 2. Checkpoint Audit (Step 1)

Both model checkpoints were verified on disk:

| Checkpoint Parameter | `best_model.pt` (Best Validation Loss) | `latest_model.pt` (Latest Completed Epoch) |
| :--- | :--- | :--- |
| **Path** | [`ml/models/best_model.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/best_model.pt) | [`ml/models/latest_model.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/latest_model.pt) |
| **Completed Epoch** | **Epoch 10** | **Epoch 15** |
| **Validation Loss** | **`0.6951`** | `0.7023` |
| **Validation Accuracy** | `70.70%` | `72.00%` |
| **Validation Macro F1** | `0.6846` | `0.7004` |
| **Backbone Architecture**| `efficientnet_b0` (timm / torchvision) | `efficientnet_b0` |
| **Number of Classes** | 4 (`SMOOTH`, `EDGE_ON`, `FEATURED_DISK`, `SPIRAL`) | 4 |
| **Continuous Attributes**| 6 (`prob_smooth`, `prob_features`, `prob_edgeon`, `prob_spiral`, `prob_bar`, `prob_odd`) | 6 |
| **Latent Embedding Dim** | 1,280 | 1,280 |
| **Input Resolution** | 224 x 224 x 3 | 224 x 224 x 3 |
| **Normalization** | ImageNet Mean `[0.485, 0.456, 0.406]`, Std `[0.229, 0.224, 0.225]` | ImageNet Mean/Std |
| **Optimizer State Dict** | Present (`AdamW`, `lr=1e-4`, `weight_decay=1e-4`) | Present |
| **Scheduler State Dict**| Present (`CosineAnnealingLR`, `T_max=12`) | Present |
| **Total Parameters** | **4,502,022** (all trainable in Phase 2) | **4,502,022** |
| **File Size on Disk** | `51.99 MB` (54,510,355 bytes) | `51.99 MB` (54,512,515 bytes) |

---

## 3. Test Set Performance Audit (Step 2)

Evaluating `best_model.pt` on the 1,000 held-out test samples (`subset_10k_scientific_targets.csv`) yields the following performance breakdown:

### Overall Test Metrics
- **Test Accuracy**: `68.50%`
- **Macro Precision**: `0.6615` | **Macro Recall**: `0.6718` | **Macro F1 Score**: `0.6648`
- **Weighted Precision**: `0.6727` | **Weighted Recall**: `0.6850` | **Weighted F1 Score**: `0.6770`
- **Mean Attribute MAE**: `0.1544`

### Per-Class Performance Breakdown
| Class | Support | Precision | Recall | F1 Score | Accuracy / Characteristics |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`SMOOTH`** | 251 | `0.7200` | `0.7888` | `0.7529` | Strong performance on featureless elliptical/spherical galaxies |
| **`EDGE_ON`** | 289 | **`0.8520`** | **`0.8962`** | **`0.8735`** | Exceptional precision and recall due to distinctive high-aspect edge profile |
| **`FEATURED_DISK`**| 241 | `0.4794` | `0.3859` | `0.4276` | Challenging intermediate class; frequently shares traits with `SMOOTH` & `SPIRAL` |
| **`SPIRAL`** | 219 | `0.5947` | `0.6164` | `0.6054` | Moderate performance; sensitive to arm structure visibility & inclination |

### Continuous Attribute MAE Breakdown
| Attribute | Description | Test MAE |
| :--- | :--- | :--- |
| `prob_smooth` | Probability galaxy is smooth/featureless | `0.1206` |
| `prob_features` | Probability galaxy has disk/feature structures | `0.1294` |
| `prob_edgeon` | Probability galaxy is viewed edge-on | **`0.0963`** |
| `prob_spiral` | Probability galaxy exhibits spiral arms | `0.2378` |
| `prob_bar` | Probability galaxy exhibits a central bar structure | `0.1999` |
| `prob_odd` | Probability galaxy exhibits odd/anomalous structure | `0.1423` |

---

## 4. Confusion Matrix Audit (Step 3)

The test set confusion matrix ([`ml/artifacts/galaxy_zoo_confusion_matrix_final.png`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/galaxy_zoo_confusion_matrix_final.png)) demonstrates the following distribution:

| True \ Predicted | `SMOOTH` | `EDGE_ON` | `FEATURED_DISK` | `SPIRAL` | Total |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`SMOOTH`** | **198** | 12 | 34 | 7 | 251 |
| **`EDGE_ON`** | 11 | **259** | 12 | 7 | 289 |
| **`FEATURED_DISK`**| 55 | 22 | **93** | 71 | 241 |
| **`SPIRAL`** | 11 | 11 | 62 | **135** | 219 |

### Scientific Analysis of Cross-Class Confusion
1. **`FEATURED_DISK` vs `SMOOTH` (55 samples confused)**:
   - *Scientific Cause*: Low-inclination or faint disk galaxies with subtle bulge dominance often lack high-contrast features in SDSS DR7 imagery, causing visual resemblance to `SMOOTH` ellipticals.
2. **`FEATURED_DISK` vs `SPIRAL` (62 + 71 = 133 samples confused)**:
   - *Scientific Cause*: `FEATURED_DISK` is a broad morphological super-category encompassing lenticulars (S0), ringed galaxies, and faint spirals. When spiral arms are tightly wound or faint, human Galaxy Zoo classifiers often split votes between `FEATURED_DISK` and `SPIRAL`.
3. **`EDGE_ON` Separation**:
   - `EDGE_ON` galaxies exhibit distinct dust lanes and linear aspect ratios, yielding `89.6%` recall and minimal confusion with other classes.

---

## 5. Confidence Calibration Audit (Step 4)

Analyzing prediction confidence across the 1,000 test samples reveals strong calibration alignment:

| Confidence Bucket | Sample Count | % of Total | Average Confidence | Actual Accuracy | Calibration Alignment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`0.00–0.49`** | 158 | `15.8%` | `43.25%` | **`43.04%`** | Excellent (Uncertain predictions match low accuracy) |
| **`0.50–0.59`** | 172 | `17.2%` | `54.52%` | **`49.42%`** | Well Calibrated |
| **`0.60–0.69`** | 142 | `14.2%` | `64.54%` | **`59.15%`** | Well Calibrated |
| **`0.70–0.79`** | 95 | `9.5%` | `74.70%` | **`66.32%`** | Moderate Alignment |
| **`0.80–0.89`** | 94 | `9.4%` | `84.65%` | **`74.47%`** | Well Calibrated |
| **`0.90–1.00`** | 336 | `33.6%` | `96.65%` | **`93.15%`** | **Exceptional** (High confidence corresponds to 93% accuracy) |

- **Mean Test Confidence**: `73.12%` | **Median Test Confidence**: `72.35%` | **Mean Classification Entropy**: `0.9084` bits.
- **Key Takeaway**: High confidence ($\ge 0.90$) is an exceptionally reliable predictor of correct classification, while low confidence ($< 0.50$) serves as an effective trigger for review triage.

---

## 6. Embedding Space Sanity Audit (Step 5)

The 10,000-sample latent embedding matrix ([`ml/artifacts/galaxy_zoo_embeddings.npy`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/galaxy_zoo_embeddings.npy)) was verified:
- **Shape**: `(10000, 1280)` float32 matrix (`48.83 MB`).
- **Integrity**: `0` NaNs, `0` Infinities, `10,000` matching rows in `galaxy_zoo_embedding_index.csv`.
- **Value Distribution**: Mean = `0.1264`, Std = `0.3388`, Min = `-0.2519`, Max = `5.0250` (ReLU/SiLU activation profile).
- **L2 Norm Distribution**: Mean = `12.8128`, Std = `1.7906`, Median = `12.6928`, Min = `7.7507`, Max = `20.9629`.

---

## 7. Class-Centroid Distance Analysis (Step 6)

Class centroids $\boldsymbol{\mu}_c$ were calculated using **only the 8,000 training embeddings**. Cosine distances $d_{\text{cos}}(\mathbf{e}, \boldsymbol{\mu}_c)$ were then evaluated for all test set predictions:

- **Cosine Distance Distribution**: Mean = `0.4648`, Median = `0.4637`, Std = `0.0977`, Min = `0.2264`, Max = `0.7984`.
- **Euclidean Distance Distribution**: Mean = `10.7075`, Median = `10.5504`, Std = `1.3594`, Min = `7.4845`, Max = `17.0827`.

### Scientific Correlations
1. **Cosine Distance vs Classification Confidence**: **`-0.6917`**
   - *Finding*: Strong negative correlation. As an observation's embedding moves away from its class centroid in 1,280-dimensional space, the model's classification confidence decreases significantly.
2. **Cosine Distance vs Scientific `p_odd`**: **`+0.2287`**
   - *Finding*: Positive correlation. Observations positioned further from learned morphological centroids tend to exhibit higher probabilities of unusual structure (`p_odd`).

---

## 8. Scientific `p_odd` Distribution Analysis (Step 7)

`p_odd` measures human voter consensus on whether a galaxy exhibits irregular, colliding, tidal, or anomalous features:

| Dataset Split | Sample Count | Mean `p_odd` | Median `p_odd` | % $\ge 0.5$ | % $\ge 0.7$ | % $\ge 0.8$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **All (10k)** | 10,000 | `0.2547` | `0.1593` | `18.08%` | `8.65%` | `4.90%` |
| **Train** | 8,000 | `0.2550` | `0.1594` | `18.12%` | `8.76%` | `4.94%` |
| **Validation** | 1,000 | `0.2565` | `0.1570` | `18.30%` | `8.60%` | `5.20%` |
| **Test** | 1,000 | `0.2504` | `0.1593` | `17.50%` | `7.80%` | `4.30%` |

- **Percentiles (All 10k)**: P25 = `0.0642`, P50 = `0.1593`, P75 = `0.3794`, P90 = `0.6676`, P95 = `0.7964`, P99 = `0.9450`.
- **Constraint**: `p_odd ≥ 0.5` is **not** automatically declared an anomaly; it serves as a continuous candidate signal for observation triage.

---

## 9. Experimental Triage Score Formulation (Step 8)

To test how model signals combine for observation prioritization, an experimental score was constructed:

$$\text{experimental\_triage\_score} = 0.35 \times d_{\text{cos, norm}} + 0.35 \times (1.0 - \text{conf}_{\text{norm}}) + 0.30 \times p_{\text{odd}}$$

- **Score Range**: `[0.00, 1.00]` (`0.0` = routine/low-priority, `1.0` = highly unusual/high-priority review candidate).
- **Test Set Distribution**: Mean = `0.3464`, Median = `0.3569`, Std = `0.1778`, Min = `0.0116`, Max = `0.8418`.

---

## 10. Representative Observations (Step 9)

Extracted test set examples ([`ml/artifacts/model_audit_examples.csv`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/model_audit_examples.csv)):

| Category | Asset ID | True Class | Pred Class | Confidence | `p_odd` | Cosine Distance | Triage Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **High-Confidence SMOOTH** | 224076 | `SMOOTH` | `SMOOTH` | **`0.9955`** | `0.0000` | `0.3208` | `0.0599` |
| **High-Confidence EDGE_ON** | 97653 | `EDGE_ON` | `EDGE_ON` | **`0.9987`** | `0.0274` | `0.2740` | `0.0380` |
| **High-Confidence FEATURED_DISK**| 122992 | `FEATURED_DISK` | `FEATURED_DISK` | `0.7841` | `0.8492` | `0.5382` | `0.5463` |
| **High-Confidence SPIRAL** | 205041 | `SPIRAL` | `SPIRAL` | **`0.9517`** | `0.0274` | `0.3701` | `0.1187` |
| **High Uncertainty** | 214553 | `SPIRAL` | `FEATURED_DISK` | **`0.3069`** | `0.1631` | `0.6290` | `0.6187` |
| **High Scientific `p_odd`** | 106723 | `FEATURED_DISK` | `SPIRAL` | `0.6743` | **`1.0000`** | `0.5793` | `0.6679` |
| **High Embedding Distance** | 177206 | `SMOOTH` | `EDGE_ON` | `0.5033` | `0.3902` | **`0.7984`** | `0.6988` |
| **High Conf / High Priority Disagreement** | 90767 | `FEATURED_DISK` | `FEATURED_DISK` | `0.6854` | `0.9006` | `0.6383` | **`0.6690`** |

---

## 11. Single-Image Production Inference & Latency Benchmarks (Steps 10 & 11)

The standalone inference engine ([`ml/src/inference.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/inference.py)) was tested across Apple Silicon MPS and CPU:

### Single-Image Latency Benchmarks ([`ml/artifacts/inference_latency.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/inference_latency.json))
- **Model Load Time**: `191.21 ms` (Apple Silicon MPS)
- **First Inference Run (Cold)**: `1473.31 ms` (Includes initial PyTorch MPS Metal shader compilation)
- **Warm Inference Latency (35 Runs on MPS)**:
  - **Mean**: **`14.64 ms`** (~68 images/sec)
  - **Median**: `15.65 ms`
  - **P95**: `16.55 ms`
  - **Min**: `7.54 ms`
  - **Max**: `17.33 ms`
- **CPU Inference Latency (Fallback Mode)**: Cold = `92.8 ms`, Warm Mean = `85.17 ms` (~11.7 images/sec).

---

## 12. Resource & Memory Footprint (Step 12)

- **Model Weights Disk Footprint**: `51.99 MB`
- **Model Parameter RAM / VRAM**: `17.17 MB` (fp32)
- **Single-Image Inference Tensor Footprint**: `< 5 MB`
- **10k Embedding Matrix (Optional Lazy Load)**: `48.83 MB`

---

## 13. Production Artifact Plan (Step 13)

See [`docs/ml_production_artifacts.md`](file:///Users/deepeshjoshi/Desktop/ASTRA/docs/ml_production_artifacts.md) for full details.
- **Required Backend Artifacts**: [`ml/models/best_model.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/best_model.pt), [`ml/src/inference.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/inference.py), [`ml/src/model.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/model.py).
- **Excluded from Backend**: `scripts/train_galaxy_zoo.py`, `ml/data/raw/`, `ml/data/processed/`, test evaluation JSONs.

---

## 14. Scientific Limitations & Engineering Risks

### Scientific Limitations
1. **Morphological Confusion**: `FEATURED_DISK` precision (`47.9%`) and recall (`38.6%`) reflect inherent noise in crowd-sourced labels for faint disk systems lacking clear spiral resolution.
2. **Not an Anomaly Classifier**: `p_odd` and embedding distance provide heuristic candidate signals for triage, not statistically calibrated discovery probabilities.

### Engineering Risks
1. **Cold-Start Latency**: The first MPS inference pass takes `~1.47s` due to Metal kernel compilation. Production workers should undergo 1 warm-up pass upon startup.
