# ASTRA — Galaxy Zoo Archive-Compatible Subset Specification

**Project**: ASTRA — AI-Based Astronomical Observation Triage System  
**Document Path**: `docs/galaxy_zoo_archive_compatibility.md`  
**Output CSV**: `ml/data/splits/subset_10k_archive_compatible_splits.csv`  
**Original Subset CSV**: `ml/data/splits/subset_10k_splits.csv` (100% Untouched)  
**Generator Script**: `scripts/create_archive_compatible_subset.py`  
**Archive File Inspected**: `~/Downloads/galaxy-zoo-2-images.zip` (3.056 GB)  
**Execution Environment**: `/Users/deepeshjoshi/Desktop/ASTRA/.venv`  

---

## 1. Executive Summary

An archive-compatible 10,000-image subset was created to resolve 21 missing asset IDs between our initial 10k subset and the actual contents of `~/Downloads/galaxy-zoo-2-images.zip`. 

All 21 missing entries (which were non-primary artifact/star entries of category `OTHER`) were replaced with 21 valid, in-archive `OTHER` category galaxies from the raw dataset, matching the exact split partitions (16 train, 2 val, 3 test).

The resulting dataset `subset_10k_archive_compatible_splits.csv` contains **10,000 images that are 100% present in the ZIP archive**, maintains perfect category balance (2,500 per broad morphology), adheres to the 80/10/10 train/val/test split, and has zero data leakage or duplicate objects.

---

## 2. Archive Inspection & Missing Image Root Cause

* **ZIP Archive Size**: `3.056 GB` (`3,281,872,000` bytes)
* **ZIP Archive Total Members**: `243,438`
* **Original Subset Size**: `10,000`
* **Images Present in Archive**: `9,979`
* **Images Unavailable in Archive**: `21`
* **Root Cause**: All 21 missing entries had `gz2class == 'A'` (Star / Artifact) belonging to non-primary sample sets (`extra` / `stripe82`) that were omitted from Kaggle's primary image archive.

---

## 3. Replacement Selection Methodology

* **Candidate Pool**: 7,910 valid candidate galaxies were identified in `merged_zoo_data.csv.gz` that:
  1. Are present in `galaxy-zoo-2-images.zip`.
  2. Are not present in the original 10k subset.
  3. Belong to `broad_morphology == 'OTHER'`.
* **Selection Rule**: 21 candidates were sampled using `random_state = 42` and assigned to match the exact split count of the missing rows:
  * **Train**: 16 replacement rows
  * **Validation**: 2 replacement rows
  * **Test**: 3 replacement rows

---

## 4. Final Dataset Metrics

### Broad Morphology Distribution

| Broad Morphology Category | Count | Percentage |
| :--- | :--- | :--- |
| **`SMOOTH`** | `2,500` | 25.0% |
| **`DISK_FEATURE`** | `2,500` | 25.0% |
| **`SPIRAL`** | `2,500` | 25.0% |
| **`OTHER`** | `2,500` | 25.0% |
| **Total** | **`10,000`** | **100.0%** |

### Split Distribution

| Split Partition | Count | Percentage |
| :--- | :--- | :--- |
| **`train`** | `8,000` | 80.0% |
| **`val`** | `1,000` | 10.0% |
| **`test`** | `1,000` | 10.0% |
| **Total** | **`10,000`** | **100.0%** |

---

## 5. Verification & Integrity Checklist

- [x] **100% Archive Matching**: `10,000 / 10,000` image filenames present in `galaxy-zoo-2-images.zip`.
- [x] **Missing Images**: `0`.
- [x] **Duplicate Asset IDs**: `0`.
- [x] **Duplicate Image Filenames**: `0`.
- [x] **Split Leakage**: `0` overlapping objects between train, val, and test.
- [x] **Original Subset Untouched**: `ml/data/splits/subset_10k_splits.csv` remains 100% intact.
- [x] **Raw Datasets Untouched**: `ml/data/raw/galaxy_zoo/` files remain 100% intact.
- [x] **Extraction Status**: `0` images extracted yet (ZIP remains unextracted).
