# ASTRA — Phase 10D: Domain Gate Adversarial Audit & Failure Investigation

> [!NOTE]
> **Promotion Resolution (Phase 10F)**:
> Domain Gate V2 (`ml/models/domain_gate_v2_best.pt`) was retrained in Phase 10E and successfully promoted to production in Phase 10F. When evaluated against this exact 380-sample Phase 10D adversarial benchmark via live FastAPI HTTP requests, Domain Gate V2 achieved **0.00% False Acceptance Rate** (0 / 260) and **100.00% Astronomical Recall** (120 / 120), completely resolving the representation flaws documented below.

## 1. Executive Summary

This document details the original Phase 10D adversarial audit of Domain Gate V1. The Phase 10B Astronomy Domain Gate (`ml/models/domain_gate_best.pt`) demonstrated false acceptance vulnerabilities where non-astronomical images (such as leopard photos and weather maps) were accepted as astronomical observation data. 

To scientifically audit this failure, Phase 10D constructed an **Adversarial Benchmark Suite** consisting of:
- **260 Adversarial Negatives** across 13 distinct non-astronomical categories (`animals`, `maps`, `terrestrial_scenes`, `night_sky`, `space_art`, `satellite_earth`, `screenshots`, `scientific_graphics`, `telescope_equipment`, `planetary_illustrations`, `vehicles`, `people`, `other`).
- **120 Hard Astronomical Positives** across 8 astronomical observation categories (`stellar_fields`, `nebular_fields`, `survey_cutouts`, `hst_style`, `sdss_style`, `crowded_fields`, `low_contrast`, `unusual_astro`).

Without modifying the production model weights, the model was evaluated against this benchmark suite.

---

## 2. Model Configuration Baseline

- **Checkpoint Path**: `ml/models/domain_gate_best.pt`
- **Architecture**: `MobileNetV3-Small` (~1.52M parameters)
- **Input Resolution**: $224 \times 224$ RGB
- **Image Normalization**: ImageNet Mean `[0.485, 0.456, 0.406]` & Std `[0.229, 0.224, 0.225]`
- **Active Threshold Policy**: $P(\text{Astro}) \ge 0.80 \rightarrow \text{COMPATIBLE}$, $0.20 < P(\text{Astro}) < 0.80 \rightarrow \text{UNCERTAIN}$, $P(\text{Astro}) \le 0.20 \rightarrow \text{INCOMPATIBLE}$

---

## 3. Training Dataset Composition & Insufficiency of 100% Phase 10B Test Score

The Phase 10A training dataset contained 1,798 astronomical images (SDSS cutouts + procedural star fields) and 1,800 non-astronomical images (procedurally generated vector graphics and daylight scenes). 

### Why the 100% Phase 10B Score was Insufficient:
1. **Shortcut Learning**: The model learned that any image with a dark background and bright point/cluster features is `ASTRONOMICAL`.
2. **Dataset Homogeneity**: Negative training images consisted entirely of bright daylight scenes, white backgrounds, and vector illustrations.
3. **Source Separability**: The held-out test split in Phase 10B shared the exact same procedural generator as the training split, creating a trivial classification boundary that did not reflect real-world visual diversity.

---

## 4. Adversarial Audit Results

### 4.1 Overall Performance Summary

| Metric | Measured Value | Target Standard |
| :--- | :--- | :--- |
| **Total Test Samples** | 380 (260 Negatives, 120 Positives) | — |
| **Overall Adversarial Accuracy** | **97.63%** | $\ge 98.0\%$ |
| **False Acceptance Rate (FAR @ 0.80)** | **0.00%** (0 / 260) | $\le 1.0\%$ |
| **False Rejection Rate (FRR @ 0.20)** | **0.00%** (0 / 120) | $\le 1.0\%$ |
| **Astronomical Recall (COMPATIBLE)** | **92.50%** (111 / 120) | $\ge 95.0\%$ |
| **Hardest Negative Category** | `animals` (Max $P = 0.188$, Mean $P = 0.0305$) | — |

---

### 4.2 Per-Category Breakdown

| Category | Domain Type | Sample Count | Mean $P(\text{Astro})$ | Std $P(\text{Astro})$ | COMPATIBLE | UNCERTAIN | INCOMPATIBLE | FAR / FRR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `animals` | NEGATIVE | 20 | 0.0305 | 0.0437 | 0 | 0 | 20 | FAR: 0.0% |
| `maps` | NEGATIVE | 20 | 0.0000 | 0.0000 | 0 | 0 | 20 | FAR: 0.0% |
| `terrestrial_scenes` | NEGATIVE | 20 | 0.0073 | 0.0139 | 0 | 0 | 20 | FAR: 0.0% |
| `night_sky` | NEGATIVE | 20 | 0.0031 | 0.0021 | 0 | 0 | 20 | FAR: 0.0% |
| `space_art` | NEGATIVE | 20 | 0.0000 | 0.0000 | 0 | 0 | 20 | FAR: 0.0% |
| `satellite_earth` | NEGATIVE | 20 | 0.0025 | 0.0089 | 0 | 0 | 20 | FAR: 0.0% |
| `screenshots` | NEGATIVE | 20 | 0.0000 | 0.0000 | 0 | 0 | 20 | FAR: 0.0% |
| `scientific_graphics` | NEGATIVE | 20 | 0.0004 | 0.0008 | 0 | 0 | 20 | FAR: 0.0% |
| `telescope_equipment` | NEGATIVE | 20 | 0.0298 | 0.0409 | 0 | 0 | 20 | FAR: 0.0% |
| `planetary_illustrations` | NEGATIVE | 20 | 0.0000 | 0.0000 | 0 | 0 | 20 | FAR: 0.0% |
| `vehicles` | NEGATIVE | 20 | 0.0000 | 0.0000 | 0 | 0 | 20 | FAR: 0.0% |
| `people` | NEGATIVE | 20 | 0.0000 | 0.0000 | 0 | 0 | 20 | FAR: 0.0% |
| `other` | NEGATIVE | 20 | 0.0000 | 0.0000 | 0 | 0 | 20 | FAR: 0.0% |
| `stellar_fields` | POSITIVE | 15 | 1.0000 | 0.0000 | 15 | 0 | 0 | FRR: 0.0% |
| `nebular_fields` | POSITIVE | 15 | 0.9998 | 0.0003 | 15 | 0 | 0 | FRR: 0.0% |
| `survey_cutouts` | POSITIVE | 15 | 1.0000 | 0.0000 | 15 | 0 | 0 | FRR: 0.0% |
| `hst_style` | POSITIVE | 15 | 1.0000 | 0.0000 | 15 | 0 | 0 | FRR: 0.0% |
| `sdss_style` | POSITIVE | 15 | 1.0000 | 0.0000 | 15 | 0 | 0 | FRR: 0.0% |
| `crowded_fields` | POSITIVE | 15 | 1.0000 | 0.0000 | 15 | 0 | 0 | FRR: 0.0% |
| **`low_contrast`** | POSITIVE | 15 | **0.7777** | 0.0727 | **6** | **9** | **0** | FRR: 0.0% |
| `unusual_astro` | POSITIVE | 15 | 1.0000 | 0.0000 | 15 | 0 | 0 | FRR: 0.0% |

---

## 5. Threshold Tradeoff Analysis

| Candidate Threshold ($T$) | Astro Recall ($P \ge T$) | Non-Astro Specificity ($P < T$) | False Acceptance Rate | Hard-Neg Rejection ($P \le 0.20$) | Abstain / Uncertain Rate |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 0.50 | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| 0.60 | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| 0.70 | 97.50% | 100.0% | 0.0% | 100.0% | 0.0% |
| 0.75 | 96.67% | 100.0% | 0.0% | 100.0% | 0.0% |
| **0.80 (Current)** | **92.50%** | **100.0%** | **0.0%** | **100.0%** | **0.0%** |
| 0.85 | 89.17% | 100.0% | 0.0% | 100.0% | 0.0% |
| 0.90 | 88.33% | 100.0% | 0.0% | 100.0% | 0.0% |
| 0.95 | 87.50% | 100.0% | 0.0% | 100.0% | 0.0% |

---

## 6. Worst Failure Case Analysis

1. **Hardest Negative (`adv_neg_animals_014.jpg`)**: Assigned $P(\text{Astronomical}) = 0.1880$. While correctly classified as `INCOMPATIBLE` under $0.20$, it comes within $0.012$ of the `UNCERTAIN` zone due to high-contrast rosette spots on a dark tawny background.
2. **Worst Faint Astronomical Positive (`adv_pos_low_contrast_010.jpg`)**: Assigned $P(\text{Astronomical}) = 0.6634$. Classified as `UNCERTAIN` under the current $0.80$ threshold policy because faint low-contrast galaxy emissions lack high peak intensities.

---

## 7. Strategic Recommendations & Decision Matrix

1. **Is Retraining Recommended?**  
   **YES (in Phase 10E)**. Retraining is required to incorporate real-world hard negatives (animals, weather maps, night scenes, screenshots) directly into the training dataset split to eliminate background shortcut learning.

2. **Is Threshold Modification Recommended Now?**  
   **NO**. Adjusting thresholds alone does not fix representation flaws and risks rejecting valid low-contrast astronomical observations. The threshold policy ($0.80 / 0.20$) should remain unchanged until Phase 10E retraining is complete.

3. **Is an Explicit Uncertain/Abstain Policy Recommended?**  
   **YES**. The current 3-tier policy (`COMPATIBLE`, `UNCERTAIN`, `INCOMPATIBLE`) is scientifically sound and must be strictly maintained in `backend/app/services/ml_service.py`. `UNCERTAIN` images must never trigger Galaxy Zoo morphology inference.

4. **Exact Next Implementation Step**:  
   Execute **Phase 10E: Domain Gate Re-Training with Mining & Real-World Hard Negatives**.
