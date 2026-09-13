# ASTRA Scientific Triage Engine & OOD / Novelty Layer Documentation

---

## 1. Purpose & Scientific Scope

The **ASTRA Scientific Triage Engine** ([`ml/src/triage.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/triage.py)) is a deterministic prioritization system built on top of the multi-head Galaxy Zoo CNN ([`ml/models/best_model.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/best_model.pt)). Its primary purpose is to process single incoming astronomical observations, evaluate embedding novelty relative to a reference morphological distribution, measure classification uncertainty, extract scientific oddity attributes, and compute a prioritized triage score for expert scientific review.

> [!IMPORTANT]
> **Mandatory Disclaimer Statement**
> *"The ASTRA triage score is an experimental prioritization heuristic intended to help allocate expert attention. It is not a calibrated anomaly probability and does not establish the discovery of a new astronomical object."*

---

## 2. Core Architecture & Pipeline Flow

The execution pipeline processes single image observations deterministically:

```
[ Incoming Image ]
       ↓
[ GalaxyZooInference (best_model.pt) ]
       ↓
  • 4 Class Logits / Probabilities
  • 6 Continuous Attributes (prob_odd, prob_bar, etc.)
  • 1280-D Latent Embedding Tensor
       ↓
[ ASTRATriageEngine (triage_reference.json) ]
       ├─► 1. Embedding Novelty Score (Cosine distance to 8k training class centroids)
       ├─► 2. Classification Uncertainty Score (1.0 - max_confidence & entropy)
       ├─► 3. Scientific Oddity Score (prob_odd)
       ↓
[ Experimental Triage Score & Operational Priority ]
       ↓
[ Deterministic Explanation Generator ]
       ↓
[ Structured Output Payload ]
```

---

## 3. Input & Output Specification

### Input
- Single astronomical observation: image file path, `PIL.Image` object, or `np.ndarray`.

### Output Payload
```json
{
  "predicted_class": "FEATURED_DISK",
  "class_confidence": 0.7841,
  "class_probabilities": {
    "SMOOTH": 0.0812,
    "EDGE_ON": 0.0124,
    "FEATURED_DISK": 0.7841,
    "SPIRAL": 0.1223
  },
  "scientific_attributes": {
    "prob_smooth": 0.1124,
    "prob_features": 0.7841,
    "prob_edgeon": 0.0124,
    "prob_spiral": 0.3214,
    "prob_bar": 0.4512,
    "prob_odd": 0.5781
  },
  "raw_embedding_distance": 0.5382,
  "nearest_reference_class": "FEATURED_DISK",
  "novelty_score": 0.4643,
  "classification_entropy_bits": 1.1245,
  "uncertainty_score": 0.2879,
  "oddity_score": 0.5781,
  "experimental_triage_score": 0.4367,
  "priority_level": "MEDIUM",
  "explanation": "Galaxy Zoo-derived oddity attribute is elevated (prob_odd >= 0.50). Prioritize for scientific review (MEDIUM priority).",
  "model_version": "Epoch 10",
  "inference_time_ms": 15.615,
  "total_triage_ms": 15.75
}
```

---

## 4. Triage Signal Components

### 4.1 Embedding Novelty Score ($S_{\text{novelty}}$)
1. The 1,280-dimensional latent embedding $\mathbf{e}$ is L2 normalized: $\hat{\mathbf{e}} = \mathbf{e} / \|\mathbf{e}\|_2$.
2. Cosine distance to each normalized class centroid $\hat{\boldsymbol{\mu}}_c$ (constructed **strictly from the 8,000 training samples**):
   $$d_c = 1.0 - \hat{\mathbf{e}} \cdot \hat{\boldsymbol{\mu}}_c$$
3. The nearest centroid distance $d_{\text{nearest}} = \min_{c} d_c$ is selected as the raw embedding distance.
4. $d_{\text{nearest}}$ is normalized into $S_{\text{novelty}} \in [0.0, 1.0]$ using training set bounds ($d_{\min} = 0.21416$, $d_{\max} = 0.912095$):
   $$S_{\text{novelty}} = \text{clip}\left(\frac{d_{\text{nearest}} - 0.21416}{0.912095 - 0.21416}, 0.0, 1.0\right)$$

### 4.2 Classification Uncertainty Score ($S_{\text{uncertainty}}$)
Derived from the maximum predicted class probability $C = \max_c P(Y=c|X)$:
$$S_{\text{uncertainty}} = \text{clip}\left(\frac{1.0 - C}{0.75}, 0.0, 1.0\right)$$
Classification entropy $H = -\sum_{i=1}^4 P_i \log_2(P_i + \epsilon)$ is also recorded in bits.

### 4.3 Scientific Oddity Score ($S_{\text{oddity}}$)
Directly utilizes the continuous multi-head regression output for irregular/anomalous structure consensus:
$$S_{\text{oddity}} = P_{\text{odd}}$$

---

## 5. Experimental Triage Score & Operational Priority Thresholds

$$\text{experimental\_triage\_score} = 0.35 \times S_{\text{novelty}} + 0.35 \times S_{\text{uncertainty}} + 0.30 \times S_{\text{oddity}}$$

| Priority Level | Score Range | Operational Meaning | UI Language |
| :--- | :--- | :--- | :--- |
| **`LOW`** | `[0.00, 0.30)` | Routine observation consistent with reference distribution | "Routine observation" |
| **`MEDIUM`** | `[0.30, 0.50)` | Subtle novelty or minor classification ambiguity | "Worth monitoring" |
| **`HIGH`** | `[0.50, 0.70)` | Elevated novelty, uncertainty, or oddity attribute | "Prioritize for scientific review" |
| **`CRITICAL`** | `[0.70, 1.00]` | Multiple strongly elevated triage signals | "Strongly prioritize for scientific review" |

---

## 6. Training Reference Distribution Integrity

The reference artifact [`ml/artifacts/triage_reference.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/triage_reference.json) (`142.96 KB`) was generated using **strictly the 8,000 training set samples**. No validation or test set samples were used to construct centroids, bounds, or percentiles.

---

## 7. What ASTRA Does NOT Claim

- **No Anomaly Confirmation**: ASTRA does not claim an observation is a "confirmed anomaly" or "new discovery".
- **No Object Identification Beyond learned classes**: ASTRA does not label unknown physical mechanisms (e.g. gravitational lenses, vorontsov-vel'yaminov interactions) automatically.
- **No Epistemic Certainty**: High confidence is not claimed as scientific certainty.

---

## 8. Future Scientific Validation Requirements

1. **Out-of-Distribution Benchmark Testing**: Evaluate the triage score on real astronomical anomaly catalogs (e.g. Ring Galaxies, Gravitational Lenses, Merging Systems).
2. **Expert Astronomer Review Feedback Loop**: Incorporate human-in-the-loop triage labels to calibrate priority thresholds.
