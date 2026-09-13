# ASTRA Phase 10A — Astronomy Domain Gate Dataset & Scientific Audit

This document details the dataset design, class taxonomy, curation methodology, leakage prevention strategies, and automated quality audits for the **Astronomy Domain Gate** (`ASTRONOMICAL` vs. `NON_ASTRONOMICAL`).

---

## 1. Domain Purpose & Scientific Scope

### Primary Objective
The Astronomy Domain Gate is a conservative binary gate positioned *before* ASTRA's Galaxy Zoo 4-class morphology model.

```
                              [ USER IMAGE UPLOAD ]
                                        │
                                        ▼
                           +--------------------------+
                           |  ASTRONOMY DOMAIN GATE   |
                           +--------------------------+
                             /          |           \
                            /           |            \
                           /            |             \
            [ COMPATIBLE ]       [ INCOMPATIBLE ]    [ UNCERTAIN ]
                 │                      │                  │
                 ▼                      ▼                  ▼
       Galaxy Zoo Morphology     Reject Upload &      Route to Safe
        & Scientific Triage      Display Friendly     Human Review
             Inference              Warning UI             Queue
```

### Key Scientific Boundaries
- **Question Answered**: *"Is this image compatible in visual domain with astronomical observation imagery suitable for ASTRA's Galaxy Zoo morphology pipeline?"*
- **What it does NOT do**:
  - Does NOT replace the 4-class morphology classifier.
  - Does NOT claim to discover new astronomical objects.
  - Does NOT label legitimate astronomical non-galaxy data (e.g. nebulae, star fields) as non-astronomical.

---

## 2. Dataset Size & Class Balance

| Domain Class | Sample Count | Percentage | Primary Subcategories |
|---|---|---|---|
| **`ASTRONOMICAL`** | 1,798 | 49.2% | Galaxy Zoo 2 survey cutouts, Stellar fields, Nebulae, Globular clusters, Deep-field survey cutouts |
| **`NON_ASTRONOMICAL`** | 1,800 | 49.2% | Natural landscapes, Vehicles/Buildings, Biological (people/animals), Graphics/Plots/UI, Hard Negatives |
| **`AMBIGUOUS`** | 60 | 1.6% | Public outreach posters, composite digital space art, telescope control rooms |
| **TOTAL** | **3,658** | **100.0%** | **Balanced Research Dataset** |

---

## 3. Data Source Documentation & License References

| Source Name | Domain Class | License / Usage Terms | Image Count | Description |
|---|---|---|---|---|
| **Galaxy Zoo 2 (SDSS DR7/DR16)** | `ASTRONOMICAL` | Open Scientific License / Public Domain (SDSS SkyServer Data Use Policy) | 1,198 | Representative galaxy morphology cutouts across smooth, featured, spiral, and edge-on types. |
| **Public Astronomical Survey Cutouts** | `ASTRONOMICAL` | Public Domain / NASA/STScI Open Archives | 600 | Synthetic/curated star fields, nebular gas clouds (H-alpha/OIII), globular cluster cutouts, and deep field surveys. |
| **Natural Scenes** | `NON_ASTRONOMICAL` | Public Domain / CC0 | 450 | Sky, clouds, sunsets, forests, mountains, water landscapes. |
| **Objects & Vehicles** | `NON_ASTRONOMICAL` | Public Domain / CC0 | 450 | Vehicles, architecture, buildings, electronic devices, food. |
| **Biological** | `NON_ASTRONOMICAL` | Public Domain / CC0 | 360 | Human portraits, faces, domestic animals, wildlife, plants/flowers. |
| **Graphics, Plots & UI** | `NON_ASTRONOMICAL` | Public Domain / Open Source | 270 | Scientific matplotlib plots, bar charts, code screenshots, UI dialogs. |
| **Hard Negatives** | `NON_ASTRONOMICAL` | Public Domain / CC0 | 270 | Night sky photos with streetlights/trees, sci-fi space art, planetary digital art, telescope hardware/engineers. |
| **Ambiguous Review Set** | `AMBIGUOUS` | Public Domain / Educational | 60 | Hybrid space posters, public outreach graphics, composite sci-fi banners. |

---

## 4. Split Distribution & Group Leakage Prevention

### Split Rationale & Percentages
- **TRAIN**: 2,518 samples (68.8%)
- **VAL**: 660 samples (18.0%)
- **TEST**: 420 samples (11.5%)
- **REVIEW**: 60 samples (1.6% — Reserved for ambiguity evaluation)

### Cross-Split Breakdown Table
```
domain_label  AMBIGUOUS  ASTRONOMICAL  NON_ASTRONOMICAL
split                                                  
REVIEW               60             0                 0
TEST                  0           240               180
TRAIN                 0          1258              1260
VAL                   0           300               360
```

### Data Leakage Prevention Rules
1. **Galaxy Zoo Grouping**: Galaxy Zoo images retain their original `group_id` matching `subset_10k_splits.csv` and keep their original train/val/test split assignments.
2. **Category Grouping**: Non-astronomical and synthetic survey images use group-level split assignment (`group_id` tag) so no multi-crop or near-duplicate series crosses split boundaries.
3. **SHA-256 Hash Verification**: Automated checks verify **0 cross-split duplicates**.

---

## 5. Automated Scientific Audit Script (`scripts/audit_domain_gate_dataset.py`)

The automated audit script enforces strict quality gates:

```bash
PYTHONPATH=. python3 scripts/audit_domain_gate_dataset.py
```

### Quality Gate Checks Executed
- [x] **File Existence & Integrity**: Checks all 3,658 files exist and are fully decodable by PIL (`0 missing, 0 corrupt`).
- [x] **SHA-256 Cross-Split Duplicate Check**: Asserts no exact hash appears in multiple splits (`0 cross-split duplicates`).
- [x] **Group Leakage Check**: Asserts no `group_id` appears in multiple splits (`0 group_ids leaked`).
- [x] **Schema Validation**: Verifies manifest columns (`image_id`, `path`, `source`, `domain_label`, `group_id`, `split`, `width`, `height`, `channels`, `format`, `sha256`).
- [x] **Visual Grid Generation**: Saves visual inspection artifact to `ml/artifacts/domain_gate_sample_grid.png`.

---

## 6. Recommended Future Model & Inference Policy Preview

### Recommended Candidate Architectures for Phase 10B
1. **MobileNetV3-Small / EfficientNet-B0**: Extremely lightweight (~1.5M–4M parameters), fast forward pass (< 5 ms on CPU/MPS), small disk footprint (< 15 MB).
2. **Conservative 3-Way Decision Thresholds**:
   - `COMPATIBLE` (Confidence $> 0.85$ Astronomical) $\rightarrow$ Proceed to Galaxy Zoo inference.
   - `INCOMPATIBLE` (Confidence $> 0.85$ Non-Astronomical) $\rightarrow$ Display non-blocking reject warning.
   - `UNCERTAIN` ($0.15 \le \text{Confidence} \le 0.85$) $\rightarrow$ Route to safe handling / non-blocking warning without crashing.

---

*Document created for ASTRA Phase 10A Dataset Curation.*
