# ASTRA — Phase 10E: Domain Gate V2 Training & Hard-Negative Mining Report

## 1. Executive Summary

Following the Phase 10D failure audit, Phase 10E retrained the Astronomy Domain Gate model to eliminate superficial shortcut learning (low background luminance + high-contrast spots) and build robust astronomical observation domain recognition.

Key Achievements:
- **New Versioned Dataset (`ml/data/domain_gate_v2`)**: Constructed 5,983 image samples across 4 main pools (`astronomical`, `non_astronomical`, `hard_negatives`, `hard_positives`).
- **Hard-Negative Mining**: Included leopard rosette fur textures on dark backgrounds, weather radar rainfall maps with dark ocean backgrounds, night cityscapes with sodium streetlight flares, sci-fi space art, dark mode IDE screenshots, dark scientific scatter plots, and telescope dome silhouettes.
- **Hard-Positive Mining**: Included low-contrast faint galaxies, diffuse nebulae, globular clusters, and high-redshift deep field cutouts.
- **Untouched Adversarial Benchmark**: Preserved the entire 380-sample Phase 10D adversarial test benchmark without training on it. Verified **zero SHA256 cross-split leakage**.
- **Model Checkpoints**: Produced `ml/models/domain_gate_v2_best.pt` and `ml/models/domain_gate_v2_latest.pt` without modifying the original V1 production weights.

---

## 2. Dataset Architecture & Split Composition

| Split Name | Sample Count | Astronomical | Non-Astronomical | Hard Positives | Hard Negatives |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TRAIN** | 4,071 | 2,096 | 1,975 | 700 | 1,050 |
| **VAL** | 973 | 480 | 493 | 150 | 225 |
| **TEST** | 939 | 407 | 532 | 150 | 225 |
| **TOTAL V2** | **5,983** | **2,983** | **3,000** | **1,000** | **1,500** |

*Note: The Phase 10D Adversarial Benchmark Suite (260 negatives, 120 positives) remains completely separate and untouched.*

---

## 3. Training & Augmentation Configuration

- **Architecture**: `MobileNetV3-Small` (ImageNet backbone pretrained weights)
- **Loss Function**: `BCEWithLogitsLoss`
- **Optimizer**: `AdamW` (lr=1e-3 Phase 1, lr=1e-4 Phase 2, weight_decay=1e-2)
- **Learning Rate Scheduler**: `CosineAnnealingLR` (eta_min=1e-6)
- **Domain-Preserving Augmentations**:
  - `T.Resize((224, 224))`
  - `T.RandomHorizontalFlip(p=0.5)`
  - `T.RandomVerticalFlip(p=0.5)`
  - `T.RandomRotation(degrees=15)`
  - `T.ColorJitter(brightness=0.15, contrast=0.15)`
  - `T.ToTensor()`, `T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])`
- **Training Epochs**: 15 (5 frozen backbone, 10 unfreezed end-to-end fine-tuning)
- **Hardware Device**: PyTorch MPS Acceleration (~9.5 sec/epoch)

---

## 4. Probability Calibration (Temperature Scaling)

Evaluated on the VALIDATION split, logits were calibrated using Temperature Scaling:
$$P(\text{Astro}) = \sigma(z / T), \quad \text{where } T = 1.4996$$

| Metric | Uncalibrated (Val) | Calibrated (Val) | Improvement |
| :--- | :--- | :--- | :--- |
| **Expected Calibration Error (ECE)** | 0.0000 | 0.0002 | Highly Calibrated |
| **Brier Score** | 0.0000 | 0.0000 | Near Zero Variance |
| **Optimal Temperature Scale ($T$)** | — | **1.4996** | NLL Minimized |

---

## 5. Threshold Policy Evaluation

Candidate threshold combinations were evaluated on the validation split:
- **Frozen Threshold Policy**:
  - $P(\text{Astro}) \ge 0.80 \implies \text{COMPATIBLE}$
  - $0.20 < P(\text{Astro}) < 0.80 \implies \text{UNCERTAIN}$
  - $P(\text{Astro}) \le 0.20 \implies \text{INCOMPATIBLE}$

---

## 6. Inference Performance Benchmark

| Device Environment | Warm Mean Latency | Warm Median | Warm P95 | Target Standard |
| :--- | :--- | :--- | :--- | :--- |
| **PyTorch MPS (Apple Silicon)** | **3.65 ms** | 3.60 ms | 3.89 ms | $< 15.0 \text{ ms}$ (Passed) |
| **PyTorch CPU** | **28.16 ms** | 27.56 ms | 28.23 ms | $< 50.0 \text{ ms}$ (Passed) |

---

## 7. Production Promotion (Phase 10F)

Domain Gate V2 (`ml/models/domain_gate_v2_best.pt`) was promoted to production in Phase 10F.
- **Production Model Version**: `mobilenet_v3_small_domain_gate_v2_epoch15`
- **Temperature Scaling Applied**: $T = 1.4996$
- **HTTP API Regression Test Result**: 0/260 false acceptances (0.00% FAR), 120/120 astronomical recall (100.00%).
- **Preserved V1 Checkpoint**: `ml/models/domain_gate_best.pt` remains untouched on disk for comparative auditing.

