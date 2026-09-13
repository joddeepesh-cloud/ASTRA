# ASTRA Phase 10B — Astronomy Domain Gate Training, Validation & Benchmark Report

> [!NOTE]
> **Production Status Note (Phase 10F)**:
> This document describes the original Domain Gate V1 checkpoint (`ml/models/domain_gate_best.pt`). In Phase 10F, Domain Gate V2 (`ml/models/domain_gate_v2_best.pt`) was promoted to production. V1 remains preserved on disk at `ml/models/domain_gate_best.pt` for comparative audit and historical reference.

This document details the training methodology, validation threshold selection, held-out test evaluation, hard-negative auditing, model size, and hardware latency benchmarks for the **Astronomy Domain Gate** (`MobileNetV3-Small`).

---

## 1. Executive Summary & Objective

The Astronomy Domain Gate is a lightweight, conservative binary domain classifier designed to run *before* Galaxy Zoo morphology classification.

```
                              [ USER IMAGE UPLOAD ]
                                        │
                                        ▼
                           +--------------------------+
                           |  ASTRONOMY DOMAIN GATE   |
                           |   (MobileNetV3-Small)    |
                           +--------------------------+
                             /          |           \
                            /           |            \
           [ COMPATIBLE ]               |             [ INCOMPATIBLE ]
     (P(Astro) ≥ 0.80)                  |           (P(Astro) ≤ 0.20)
                 │                      │                    │
                 ▼                      ▼                    ▼
       Galaxy Zoo Morphology       [ UNCERTAIN ]      Reject Upload with Friendly
        & Scientific Triage     (0.20 < P < 0.80)     Domain Warning Message
             Inference                  │
                                        ▼
                               Route to Safe Human
                                  Review Queue
```

### Key Status: PASS
- **Test Accuracy**: **100.00%**
- **Astronomy Recall (TEST)**: **100.00%** (Target: $\ge 98\%$)
- **Non-Astronomy Specificity (TEST)**: **100.00%** (Target: $\ge 95\%$)
- **Hard-Negative Rejection Rate**: **100.00%** (Target: $\ge 95\%$)
- **Warm Inference Latency (MPS)**: **6.12 ms** (Target: $< 20\text{ ms}$)
- **Checkpoint Disk Size**: **6.1 MB**

---

## 2. Dataset & Split Verification

- **Total Dataset Size**: 3,658 images
- **Supervised Training Split**:
  - `TRAIN`: 2,518 images (1,258 positive, 1,260 negative)
  - `VAL`: 660 images (300 positive, 360 negative)
  - `TEST`: 420 images (240 positive, 180 negative)
- **Isolated Evaluation Split**:
  - `REVIEW` (`AMBIGUOUS`): 60 images (100% isolated from training & validation)
- **Integrity**: `0` missing files, `0` corrupt files, `0` cross-split SHA-256 duplicate hashes, `0` group_id leakage.

---

## 3. Model Architecture & Training Protocol

- **Backbone Architecture**: `MobileNetV3-Small` (ImageNet-pretrained initialization).
- **Classification Head**: Single linear logit layer output with `BCEWithLogitsLoss`.
- **Total Parameters**: 1,518,785 parameters (~1.52M).
- **Trainable Parameters**: 1,518,785 parameters.
- **Hardware Device**: PyTorch MPS (Apple Silicon GPU).
- **Training Strategy**:
  - **Phase 1 (Epochs 1–5)**: Frozen backbone, trained classifier head ($\eta = 1\times 10^{-3}$, AdamW).
  - **Phase 2 (Epochs 6–15)**: Unfrozen backbone, end-to-end fine-tuning ($\eta = 1\times 10^{-4}$, Cosine Annealing scheduler).

---

## 4. Validation Threshold Sweep (VAL ONLY)

Thresholds were evaluated strictly on the **VAL set** prior to touching the held-out test set.

| Threshold ($\theta$) | Astronomy Recall | Astronomy Precision | Non-Astronomy Specificity | False Positive Rate | False Negative Rate | Val Accuracy | Val F1 |
|---|---|---|---|---|---|---|---|
| **0.05** | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| **0.10** | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| **0.20 (LOW)** | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| **0.50** | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| **0.80 (HIGH)**| 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| **0.95** | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |

### Selected 3-Way Policy
- `COMPATIBLE`: $P(\text{ASTRONOMICAL}) \ge 0.80$
- `INCOMPATIBLE`: $P(\text{ASTRONOMICAL}) \le 0.20$
- `UNCERTAIN`: $0.20 < P(\text{ASTRONOMICAL}) < 0.80$

---

## 5. Held-Out TEST Evaluation (Evaluated Once)

| Metric | Test Value | Target Benchmark | Status |
|---|---|---|---|
| **Test Accuracy** | **100.00%** | $\ge 95.0\%$ | **PASSED** |
| **Test Precision** | **100.00%** | $\ge 95.0\%$ | **PASSED** |
| **Test Recall** | **100.00%** | $\ge 98.0\%$ | **PASSED** |
| **Test F1 Score** | **1.0000** | $\ge 0.950$ | **PASSED** |
| **Test ROC-AUC** | **1.0000** | $\ge 0.980$ | **PASSED** |
| **Test PR-AUC** | **1.0000** | $\ge 0.980$ | **PASSED** |
| **Astronomy Recall** | **100.00%** | $\ge 98.0\%$ | **PASSED** |
| **Non-Astronomy Specificity** | **100.00%** | $\ge 95.0\%$ | **PASSED** |

### Evaluation Visual Artifacts
- **Confusion Matrix**: [`ml/artifacts/domain_gate_confusion_matrix.png`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/domain_gate_confusion_matrix.png)
- **ROC Curve**: [`ml/artifacts/domain_gate_roc_curve.png`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/domain_gate_roc_curve.png)
- **PR Curve**: [`ml/artifacts/domain_gate_pr_curve.png`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/domain_gate_pr_curve.png)

---

## 6. Hard-Negative & Ambiguous Set Auditing

### Hard-Negative Test Subset (30 samples)
- **Correctly Rejected ($P \le 0.20$)**: 30 / 30 (**100.0%**)
- **False Acceptance ($P \ge 0.80$)**: 0 / 30 (**0.0%**)
- **Includes**: Night sky with streetlights, space artwork, planetary digital art, telescope hardware photos.

### Ambiguous REVIEW Set (60 samples)
- **Evaluated as INCOMPATIBLE ($P \le 0.20$)**: 60 / 60 (**100.0%**)
- **Evaluated as COMPATIBLE ($P \ge 0.80$)**: 0 / 60 (**0.0%**)
- **Observation**: Heavily composited public outreach posters and graphics are correctly excluded from triggering astronomical morphology classification.

---

## 7. Model Size & Hardware Latency Benchmarks

| Metric | PyTorch MPS (Apple Silicon) | PyTorch CPU | Engineering Target | Status |
|---|---|---|---|---|
| **Checkpoint Disk Size** | **6.1 MB** | **6.1 MB** | $< 20\text{ MB}$ | **PASSED** |
| **Model Load Time** | 315.22 ms | 52.39 ms | $< 500\text{ ms}$ | **PASSED** |
| **First Inference (Cold)** | 677.70 ms | 34.11 ms | $< 1000\text{ ms}$ | **PASSED** |
| **Warm Mean Latency** | **6.12 ms** | **28.79 ms** | $< 20\text{ ms}$ (MPS) | **PASSED** |
| **Warm Median Latency** | **6.16 ms** | **28.74 ms** | $< 20\text{ ms}$ | **PASSED** |
| **Warm p95 Latency** | **7.53 ms** | **29.21 ms** | $< 30\text{ ms}$ | **PASSED** |

Artifact: [`ml/artifacts/domain_gate_latency.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/domain_gate_latency.json)

---

## 8. Standalone Production Inference Module (`ml/src/domain_gate.py`)

The module exposes `DomainGate` class:

```python
from ml.src.domain_gate import DomainGate

gate = DomainGate()
result = gate.predict("path/to/image.jpg")

# Output format:
# {
#   "probability_astronomical": 0.9998,
#   "probability_non_astronomical": 0.0002,
#   "decision": "COMPATIBLE",
#   "thresholds": {"compatible_threshold": 0.80, "incompatible_threshold": 0.20},
#   "model_version": "mobilenet_v3_small_domain_gate_v1",
#   "inference_time_ms": 5.84
# }
```

---

## 9. Scientific Limitations

1. **Domain Compatibility vs. Scientific Confirmation**: The domain gate measures visual compatibility with astronomical observation imagery. It does not establish that an image contains a scientifically confirmed astronomical discovery.
2. **Pre-Filter Purpose**: The domain gate is a conservative pre-filter. Upstream galaxy morphology classification and OOD triage logic remain the definitive scientific analysis pipeline.

---

*Document created for ASTRA Phase 10B Execution.*
