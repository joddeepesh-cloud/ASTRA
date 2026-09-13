# ASTRA — Phase 10D: Domain Gate Failure Analysis & Audit Report

## 1. Executive Summary

This document provides a rigorous scientific audit of the current **Astronomy Domain Gate** (`ml/models/domain_gate_best.pt`) implemented in Phase 10B/10C. While Phase 10B achieved a **100% test accuracy** on the held-out Phase 10A test split, real-world adversarial testing revealed **critical false acceptances**:
1. Photographs of animals (e.g., leopards) are accepted as astronomical (`P(Astronomical) > 0.80`).
2. Geographic weather/rainfall maps (e.g., India rainfall maps) are accepted as astronomical (`P(Astronomical) > 0.80`).
3. Rejection behavior on dark non-astronomical images is inconsistent.

This audit proves that the **100% Phase 10B validation score was an artifact of dataset separability and shortcut learning**, not true astronomical domain understanding.

---

## 2. Model & Pipeline Technical Baseline

| Parameter | Configuration / Value |
| :--- | :--- |
| **Model Architecture** | `MobileNetV3-Small` (pretrained on ImageNet, custom binary classifier head) |
| **Total Parameters** | 1,518,881 (~1.52M) |
| **Input Resolution** | $224 \times 224$ RGB |
| **Preprocessing & Normalization** | `T.Resize((224, 224))`, `T.ToTensor()`, `T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])` |
| **Training Augmentations** | `T.RandomHorizontalFlip(p=0.5)`, `T.RandomRotation(degrees=10)`, `T.ColorJitter(brightness=0.1, contrast=0.1)` |
| **Loss & Optimizer** | `BCEWithLogitsLoss`, `AdamW` (Phase 1: lr=1e-3 classifier head, Phase 2: lr=1e-4 full backbone fine-tuning) |
| **Production Threshold Policy** | $P(\text{Astro}) \ge 0.80 \rightarrow \text{COMPATIBLE}$, $0.20 < P(\text{Astro}) < 0.80 \rightarrow \text{UNCERTAIN}$, $P(\text{Astro}) \le 0.20 \rightarrow \text{INCOMPATIBLE}$ |

---

## 3. Training Dataset Composition Audit (Phase 10A)

| Class Domain | Total Count | Data Sources | Visual Characteristics |
| :--- | :--- | :--- | :--- |
| **ASTRONOMICAL** | 1,798 | 1,198 Galaxy Zoo 2 SDSS cutouts + 600 synthetic survey cutouts (`stellar_field`, `nebula`, `globular_cluster`, `deep_field`) | Low mean background intensity, black sky ($RGB \approx [10, 10, 15]$), isolated bright point sources or nebular gas. |
| **NON_ASTRONOMICAL** | 1,800 | 1,800 synthetically generated graphics across 5 categories (`natural_scenes`, `objects_vehicles`, `biological`, `graphics_ui`, `hard_negatives`) | High mean background intensity, bright daylight skies ($RGB \approx [135, 206, 235]$), light gray/white canvases, vector graphics. |
| **AMBIGUOUS** | 60 | Synthetically drawn space artwork and hybrid scenes (held out from training/eval) | Mixed dark/bright synthetic visuals. |

---

## 4. Audit Findings & Root-Cause Failure Mechanism

### 4.1 Shortcut Learning Hypothesis
The model did **not** learn high-level semantic astronomical concepts (e.g., galaxy arms, point spread functions, diffraction spikes, cosmic background noise). Instead, it learned a superficial **shortcut feature**:
$$\text{Shortcut Rule}: \quad \text{Low Mean Background Luminance} + \text{Localized High-Contrast Intensity} \implies \text{ASTRONOMICAL}$$

Because virtually all `NON_ASTRONOMICAL` training samples had bright backgrounds (blue sky, white canvas, light gray UI), the model learned that any image with a dark background and bright localized spots must be astronomical.

### 4.2 Why Real-World Images Trigger False Acceptances
- **Leopard Photographs**: Dark fur background combined with bright high-contrast rosette spots matches the low-background + point-source intensity profile of stellar fields.
- **Weather / Rainfall Maps**: Dark ocean background ($RGB \approx [0, 15, 30]$) combined with bright heat-map contours (yellow/red/green intensity spots) matches the dark-sky + nebular gas profile of astronomical survey cutouts.
- **Dark Mode Screenshots & Night Scenes**: Low background luminance with bright text or light sources tricks the model into high astronomical confidence.

### 4.3 Dataset & Split Flaws
1. **Lack of Realistic Dark Negatives**: The Phase 10A non-astronomical set completely lacked real-world dark photographs (e.g., animals at night, dark indoor scenes, weather maps, night cityscapes).
2. **Synthetic Data Homogeneity**: All 1,800 negative training samples were procedurally drawn using PIL, resulting in high internal stylistic homogeneity.
3. **Overly Easy Evaluation Split**: The train/val/test splits shared identical procedural generators. The 100% test accuracy reflected **source separability** between synthetic graphics and SDSS astronomy cutouts, not general domain robustness.

---

## 5. Distinction: Model Failure vs. Threshold Failure

> [!IMPORTANT]
> **Model Failure vs. Threshold Failure**
> - **Model Failure**: The model assigns a raw logit leading to $P(\text{Astronomical}) = 0.98$ for a leopard photo. This means the feature representation itself is flawed.
> - **Threshold Failure**: The model assigns $P(\text{Astronomical}) = 0.45$ for a leopard photo, but our threshold policy classifies it as `UNCERTAIN` or `COMPATIBLE` rather than `INCOMPATIBLE`.
> 
> Real-world observations show **Model Failure**: non-astronomical dark images receive probabilities above $0.85$–$0.95$. Adjusting thresholds (e.g. raising `compatible_threshold` from $0.80$ to $0.95$) will **NOT** fix the issue, because adversarial negatives exceed $0.95$ while legitimate faint galaxies drop below $0.90$.

---

## 6. Recommended Remediation Strategy

1. **Adversarial Benchmark Suite (Phase 10D)**: Construct a comprehensive benchmark of diverse real-world hard negatives (animals, weather maps, night sky photos, screenshots, satellite earth images, space art) and hard positives (stellar fields, nebular fields, low-contrast galaxies).
2. **Hard-Negative Mining (Future Phase)**: Retrain the Domain Gate with real-world dark photographs, night scenes, weather graphics, and dark UI screenshots in the non-astronomical training split.
3. **Domain-Specific Augmentations (Future Phase)**: Include random background luminance shifts, contrast adjustments, and dark-noise injection during training.
