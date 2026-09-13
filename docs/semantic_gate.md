# ASTRA — Universal Open-World Semantic Domain Gate Specification

## Executive Overview
The **Universal Semantic Gate** (`ml/src/semantic_gate.py`) is a zero-shot vision-language pre-filter introduced in Phase 10H. Placed **BEFORE** Domain Gate V2, it replaces the fragile mindset of memorized hard-negative image blacklists with open-world visual concept reasoning.

```text
[ USER IMAGE UPLOAD ]
          │
          ▼
+------------------------------------+
|   UNIVERSAL SEMANTIC GATE (CLIP)   |
| (Prompt Family Ensemble & Margin)  |
+------------------------------------+
    │                     │
 SEMANTIC_INCOMPATIBLE /  │ SEMANTIC_COMPATIBLE
 SEMANTIC_UNCERTAIN       ▼
    │         +--------------------------+
    │         |  ASTRONOMY DOMAIN GATE   |
    │         |   (MobileNetV3-Small)    |
    │         +--------------------------+
    │            │                  │
    │        INCOMPATIBLE /      COMPATIBLE
    │        UNCERTAIN              │
    │            │                  ▼
    ▼            ▼        +-------------------+
 [ STOP: NO MORPHOLOGY ]  | Galaxy Zoo & OOD  |
 (Safe Response Returned) | Triage Inference  |
                          +-------------------+
```

---

## 1. Core Architecture & Model Selection
- **Model Architecture**: OpenCLIP `ViT-B-32` (`laion2b_s34b_b79k`) with HuggingFace CLIP fallback.
- **Parameters**: ~151M parameters.
- **Hardware Acceleration**: Apple Silicon PyTorch MPS / CUDA (~10-30 ms warm inference).
- **Startup Optimization**: Prompt text embeddings are pre-encoded and cached in memory once at server startup. Request time requires encoding the incoming image **only once**.

---

## 2. Zero-Shot Prompt Ensemble Families

The gate evaluates 5 distinct prompt families (55 total prompts):

1. **`astronomical` (12 prompts)**:
   - "an astronomical observation", "a scientific telescope observation", "an astronomical survey image", "a deep sky observation", "an astronomical imaging dataset", "a galaxy observation from a telescope", "a stellar field observed by a telescope", "a nebula observed by a telescope", "a star cluster observed by a telescope", "a space telescope scientific image", "scientific astronomical imaging data", "a deep-space scientific observation"
2. **`terrestrial` (10 prompts)**:
   - "a terrestrial photograph", "a wildlife photograph", "an animal photograph", "a human photograph", "a landscape photograph", "a building photograph", "a vehicle photograph", "an ordinary outdoor photograph", "a street photograph", "a close-up photograph of an animal"
3. **`visualization` (13 prompts)**:
   - "a geographic map", "a weather map", "a rainfall map", "a radar visualization", "a heatmap", "a scientific chart", "a data visualization", "a graph or plot", "a dashboard", "a computer screenshot", "an IDE screenshot", "a website screenshot", "a mobile application screenshot"
4. **`artwork` (12 prompts)**:
   - "digital artwork", "a painting", "an illustration", "a poster", "an infographic", "a 3D render", "computer-generated artwork", "science fiction artwork", "fantasy space artwork", "a movie frame", "a video game screenshot", "a space wallpaper"
5. **`fictional_space` (8 prompts)**:
   - "a fictional space scene", "a science fiction space scene", "a rendered planet", "an illustrated galaxy", "a fictional nebula", "a cinematic space scene", "a computer-generated galaxy", "a fantasy astronomical scene"

---

## 3. Ensemble Scoring & Semantic Margin Formula

For an input image vector $\vec{v}_{\text{img}}$ and prompt family embedding matrices $M_{\text{fam}}$:

1. **Family Score**: Calculated as the top-3 mean cosine similarity within each family:
   $$S_{\text{fam}} = \text{mean}\left(\text{Top3}\left(\vec{v}_{\text{img}} \cdot M_{\text{fam}}^T\right)\right)$$
2. **Semantic Positive**:
   $$S_{\text{positive}} = S_{\text{astronomical}}$$
3. **Semantic Negative**:
   $$S_{\text{negative}} = \max\left(S_{\text{terrestrial}}, S_{\text{visualization}}, S_{\text{artwork}}, S_{\text{fictional\_space}}\right)$$
4. **Semantic Margin**:
   $$\text{Margin} = S_{\text{positive}} - S_{\text{negative}}$$

---

## 4. Decision Policy & Fail-Closed Logic

| State | Condition | Downstream Action |
| :--- | :--- | :--- |
| **`SEMANTIC_COMPATIBLE`** | $S_{\text{astronomical}} \ge 0.2800$ AND $\text{Margin} \ge 0.0000$ | Proceed to Stage 2 (Domain Gate V2) |
| **`SEMANTIC_INCOMPATIBLE`** | $\text{Margin} \le -0.0100$ OR ($S_{\text{negative}} \ge 0.2750$ AND $S_{\text{astronomical}} < 0.2800$) | **STOP**. Return safe rejection message. Skip Galaxy Zoo. |
| **`SEMANTIC_UNCERTAIN`** | All other boundary conditions | **STOP**. Return safe uncertainty notice. Skip Galaxy Zoo. |

---

## 5. Measured Performance & Holdout Verification
- **False Acceptance Rate (FAR @ 380 samples)**: **0.00% (0 / 260)**
- **False Rejection Rate (FRR)**: **0.00% (0 / 120)**
- **Leopard Photo**: `SEMANTIC_INCOMPATIBLE` ($\text{Margin} = -0.0215$) $\rightarrow$ Rejected
- **India Rainfall Map**: `SEMANTIC_INCOMPATIBLE` ($\text{Margin} = -0.0707$) $\rightarrow$ Rejected
- **IDE Screenshot**: `SEMANTIC_INCOMPATIBLE` ($\text{Margin} = -0.0471$) $\rightarrow$ Rejected
- **Sci-Fi Space Art**: `SEMANTIC_UNCERTAIN` ($\text{Margin} = -0.0037$) $\rightarrow$ Rejected
- **Real Galaxy / Faint Galaxy**: `SEMANTIC_COMPATIBLE` ($\text{Margin} = +0.0264 / +0.0339$) $\rightarrow$ Passed
- **Warm Inference Latency (MPS)**: **29.17 ms**
