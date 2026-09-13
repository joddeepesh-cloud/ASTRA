# ASTRA — ML Production Artifact Specification

This document defines the strict demarcation between **Required Production Artifacts**, **Development & Training Artifacts**, and **Evaluation-Only Artifacts** for the ASTRA machine learning subsystem.

---

## 1. Architectural Principles

1. **Decoupled Backend Execution**: The production backend API service depends **only** on portable inference modules ([`ml/src/inference.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/inference.py)), triage engines ([`ml/src/triage.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/triage.py)), serialized weights ([`ml/models/best_model.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/best_model.pt)), and training reference centroids ([`ml/artifacts/triage_reference.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/triage_reference.json)).
2. **Zero Training Script Dependencies**: The production server must **not** import or execute `scripts/train_galaxy_zoo.py` or require training data loaders.
3. **Startup Loading Flow**:
```text
Frontend
   ↓
FastAPI (backend/app/main.py)
   ↓
MLService (backend/app/services/ml_service.py)
   ↓
GalaxyZooInference (ml/src/inference.py)
   ↓
ASTRATriageEngine (ml/src/triage.py)
   ↓
best_model.pt (51.99 MB) + triage_reference.json (142.96 KB)
```
4. **No Raw Image Footprint**: The production backend service must **never** load the 243,500 raw images or the 10,000 training images into server memory or local disk. Single incoming astronomical observations are preprocessed dynamically in memory.

---

## 2. Artifact Classification Matrix

| Artifact Path | Category | Purpose | Loaded at Production Startup? | File Size |
| :--- | :--- | :--- | :--- | :--- |
| [`ml/models/best_model.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/best_model.pt) | **A. Required Production** | Best validation-loss weights (Epoch 10) for morphology classification & attribute prediction. | **YES** | `51.99 MB` |
| [`ml/models/domain_gate_v2_best.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/domain_gate_v2_best.pt) | **A. Required Production** | Calibrated V2 MobileNetV3-Small binary domain gate weights (Epoch 15, $T = 1.4996$). | **YES** | `6.10 MB` |
| [`ml/models/domain_gate_best.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/domain_gate_best.pt) | **B. Audit / Preserved V1** | Original Domain Gate V1 checkpoint preserved on disk for auditability. | **NO** | `6.10 MB` |
| [`ml/src/semantic_gate.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/semantic_gate.py) | **A. Required Production** | Standalone zero-shot open-world Universal Semantic Gate module (`SemanticDomainGate`). | **YES** | `< 10 KB` |
| [`ml/src/domain_gate.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/domain_gate.py) | **A. Required Production** | Standalone domain compatibility gate module (`DomainGate`). | **YES** | `< 5 KB` |
| [`ml/src/inference.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/inference.py) | **A. Required Production** | Standalone inference engine (`GalaxyZooInference`) supporting CPU/MPS/CUDA single-image inference. | **YES** | `< 10 KB` |
| [`ml/src/triage.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/triage.py) | **A. Required Production** | Scientific triage engine (`ASTRATriageEngine`) computing novelty, uncertainty, oddity & priority scores. | **YES** | `< 10 KB` |
| [`ml/artifacts/triage_reference.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/triage_reference.json) | **A. Required Production** | Training-only reference centroids, distance percentiles & normalization bounds. | **YES** | `142.96 KB` |
| [`ml/src/model.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/model.py) | **A. Required Production** | Core multi-head CNN architecture definition (`GalaxyZooMultiHeadCNN`). | **YES** | `< 5 KB` |
| [`ml/artifacts/galaxy_zoo_embeddings.npy`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/galaxy_zoo_embeddings.npy) | **B. Development / Evaluation** | 10,000 x 1,280 latent embedding matrix for offline vector search & audit. | **NO** | `48.83 MB` |
| [`ml/artifacts/galaxy_zoo_embedding_index.csv`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/galaxy_zoo_embedding_index.csv) | **B. Development / Evaluation** | Mapping index associating embedding rows with `asset_id`, split, and target label. | **NO** | `0.55 MB` |
| [`ml/models/latest_model.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/latest_model.pt) | **B. Development / Training** | Latest training checkpoint (Epoch 15) for training resumption. | **NO** | `51.99 MB` |
| [`scripts/train_galaxy_zoo.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/scripts/train_galaxy_zoo.py) | **B. Development / Training** | Training execution pipeline script. | **NO** | `25.8 KB` |
| `ml/data/raw/` & `ml/data/processed/` | **B. Development / Training** | 10,000 validated training/val/test images and raw metadata. | **NO** | `~350 MB` |
| [`ml/artifacts/galaxy_zoo_test_report.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/galaxy_zoo_test_report.json) | **C. Evaluation-Only** | Detailed 1,000-sample test set evaluation metrics. | **NO** | `< 5 KB` |
| [`ml/artifacts/triage_distribution.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/triage_distribution.json) | **C. Evaluation-Only** | Offline 10,000-sample triage score distribution & priority counts per split. | **NO** | `< 5 KB` |
| [`ml/artifacts/triage_latency.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/triage_latency.json) | **C. Evaluation-Only** | Full warm-pipeline latency benchmark (image load -> model -> triage). | **NO** | `< 5 KB` |
| [`ml/artifacts/galaxy_zoo_confusion_matrix_final.png`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/galaxy_zoo_confusion_matrix_final.png) | **C. Evaluation-Only** | Confusion matrix plot for documentation & audit. | **NO** | `123 KB` |
| [`ml/artifacts/galaxy_zoo_confidence_audit.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/galaxy_zoo_confidence_audit.json) | **C. Evaluation-Only** | Confidence calibration bucket analysis. | **NO** | `< 5 KB` |
| [`ml/artifacts/embedding_audit.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/embedding_audit.json) | **C. Evaluation-Only** | Sanity audit report for 10k embedding matrix. | **NO** | `< 5 KB` |
| [`ml/artifacts/triage_signal_analysis.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/triage_signal_analysis.json) | **C. Evaluation-Only** | Exploratory centroid distance and `p_odd` correlation report. | **NO** | `< 5 KB` |
| [`ml/artifacts/model_audit_examples.csv`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/model_audit_examples.csv) | **C. Evaluation-Only** | Representative test set audit examples. | **NO** | `< 5 KB` |
| [`ml/artifacts/inference_latency.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/inference_latency.json) | **C. Evaluation-Only** | Cold/warm single-image inference latency benchmarks. | **NO** | `< 5 KB` |

---

## 3. Server Startup Memory Footprint

- **Minimum Required RAM (Model Loading)**: `191 ms` cold startup time, `~17.2 MB` weight RAM.
- **Optional Latent Index RAM (Lazy Load)**: `~49.4 MB` total RAM for 10k embeddings and CSV metadata index.
- **Peak Inference Memory**: `< 25 MB` total RAM per active inference worker.

---

## 4. Production Load Path Verification

```python
from ml.src.inference import GalaxyZooInference

# Production service initialization
engine = GalaxyZooInference(model_path="ml/models/best_model.pt")

# Single image observation prediction
result = engine.predict_single_image("path/to/observation.jpg")
```
