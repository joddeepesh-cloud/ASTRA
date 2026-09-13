# Merged Galaxy Zoo 2 Dataset Inspection Report

**Project**: ASTRA — AI-Based Astronomical Observation Triage System  
**Document Path**: `docs/merged_zoo_data_inspection.md`  
**Target File**: `ml/data/raw/galaxy_zoo/merged_zoo_data.csv.gz`  
**Original File Source**: `~/Downloads/merged_zoo_data.csv.gz` (Copied, original preserved)  
**Environment Used**: `/Users/deepeshjoshi/Desktop/ASTRA/.venv`  

---

## 1. Executive Summary

The compressed `merged_zoo_data.csv.gz` file (51 MB) was copied from `~/Downloads/` into `ml/data/raw/galaxy_zoo/` without decompressing on disk or modifying the original file in `~/Downloads/`.

Inspection via Pandas in the `.venv` environment confirms this file contains **243,500 rows** and **236 columns**, providing complete morphological classification labels, volunteer vote counts, debiased probabilities, sky coordinates (`ra`, `dec`), and SDSS Object IDs (`dr7objid`).

Crucially, **100% of the 243,500 rows** in `merged_zoo_data.csv.gz` match the `objid`s in `gz2_filename_mapping.csv`, providing the complete morphology ground truth required for galaxy classification, triage priority scoring, and out-of-distribution (OOD) anomaly detection.

---

## 2. Measured Dataset Metrics

| Metric | Value |
| :--- | :--- |
| **File Path** | `ml/data/raw/galaxy_zoo/merged_zoo_data.csv.gz` |
| **File Size** | `51 MB` (compressed) |
| **Total Rows** | `243,500` |
| **Total Columns** | `236` |
| **`dr7objid` Match Rate** | `100.00%` (243,500 / 243,500 match `gz2_filename_mapping.csv`) |
| **Columns with Nulls** | Only `2` out of 236 columns (`specobjid`: 14 nulls, `dr8objid`: 3,752 nulls) |
| **Morphology Columns** | `224` detailed task classification columns (`t01` through `t11`) |

---

## 3. Key Identifiers & Celestial Coordinates

| Column | Data Type | Null Count | Description |
| :--- | :--- | :--- | :--- |
| `dr7objid` | `int64` | `0` | Primary SDSS DR7 Photometric Object ID (Matches `objid` in mapping CSV) |
| `dr8objid` | `float64` | `3,752` | SDSS DR8 Photometric Object ID |
| `specobjid` | `float64` | `14` | SDSS Spectroscopic Object ID |
| `ra` | `float64` | `0` | Right Ascension (Degrees) |
| `dec` | `float64` | `0` | Declination (Degrees) |
| `gz2class` | `object` | `0` | Galaxy Zoo 2 Morphology Class Designation (e.g., `Ei`, `Er`, `Sb`, `Sc`, ` Ser`, `SBb`) |
| `total_classifications` | `int64` | `0` | Total volunteer classifications per galaxy |

---

## 4. Galaxy Zoo 2 Decision Tree Tasks (`t01` – `t11`)

The dataset contains complete vote counts, raw fractions, weighted fractions, debiased probabilities, and flags for all 11 Galaxy Zoo 2 decision tree questions:

* **Task 01**: Smooth vs Features/Disk vs Star/Artifact (`t01_smooth_or_features_*`)
* **Task 02**: Edge-on Disk (`t02_edgeon_*`)
* **Task 03**: Bar Structure (`t03_bar_*`)
* **Task 04**: Spiral Arms (`t04_spiral_*`)
* **Task 05**: Bulge Prominence (`t05_bulge_prominence_*`)
* **Task 06**: Odd / Unusual Features (`t06_odd_*`)
* **Task 07**: Galaxy Roundness (`t07_rounded_*`)
* **Task 08**: Odd Feature Type — Ring, Lens, Disturbed, Irregular, Merger, Dust Lane (`t08_odd_feature_*`)
* **Task 09**: Bulge Shape (`t09_bulge_shape_*`)
* **Task 10**: Arm Winding Tightness (`t10_arms_winding_*`)
* **Task 11**: Spiral Arm Count (`t11_arms_number_*`)

---

## 5. Sample Preview (First 5 Rows)

| `dr7objid` | `ra` | `dec` | `gz2class` | `total_classifications` | `t01_smooth_fraction` | `t01_features_fraction` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `588017703996096547` | `160.99040` | `11.703790` | `SBb?t` | `44` | `0.023` | `0.955` |
| `587738569780428805` | `192.41083` | `15.164207` | `Ser` | `45` | `0.111` | `0.844` |
| `587735695913320507` | `210.80220` | `54.348953` | `Sc+t` | `46` | `0.000` | `0.957` |
| `587742775634624545` | `185.30342` | `18.382704` | `SBc(r)` | `45` | `0.178` | `0.822` |
| `587732769983889439` | `187.36679` | `8.749928` | `Ser` | `49` | `0.245` | `0.735` |

---

## 6. Final Verification Checklist

- [x] **File Existence**: `ml/data/raw/galaxy_zoo/merged_zoo_data.csv.gz` verified (51 MB).
- [x] **Original Preserved**: `~/Downloads/merged_zoo_data.csv.gz` remains intact.
- [x] **No Unnecessary Decompression**: File inspected directly in compressed form via Pandas Gzip reader.
- [x] **Rows Verified**: `243,500` rows.
- [x] **Columns Verified**: `236` columns.
- [x] **ObjID Verification**: `dr7objid` present with 100% match rate to `gz2_filename_mapping.csv`.
- [x] **Morphology Labels Verified**: 224 morphology columns present covering all 11 GZ2 classification tasks.
- [x] **Missing Values Verified**: Only 2 columns have missing values (`specobjid`: 14, `dr8objid`: 3,752); all 234 other columns have 0 missing values.
