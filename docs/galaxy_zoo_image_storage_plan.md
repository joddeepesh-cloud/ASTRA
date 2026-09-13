# Galaxy Zoo Image Storage & Subset Selection Strategy

**Project**: ASTRA — AI-Based Astronomical Observation Triage System  
**Document Path**: `docs/galaxy_zoo_image_storage_plan.md`  
**Date**: September 10, 2026  
**Environment**: `/Users/deepeshjoshi/Desktop/ASTRA/.venv`  

---

## 1. Executive Summary

This document details the storage-efficient strategy for acquiring, indexing, and organizing an initial training subset of **5,000 to 10,000 labeled Galaxy Zoo 2 images** for ASTRA.

Based on our inspection of `gz2_filename_mapping.csv` and `merged_zoo_data.csv.gz`, we have verified a **100% exact 1-to-1 match** across 243,500 labeled galaxies. The image filenames directly follow the `<asset_id>.jpg` convention.

By selecting a controlled, balanced subset of 10,000 galaxies, we can train high-performance morphology models and out-of-distribution (OOD) anomaly detectors while using **only ~200 MB of disk space**, avoiding the need to store the full 3.06 GB archive permanently on disk.

---

## 2. Local Image Archive Audit

* **System Search Scope**: Searched `~/Downloads`, `~/Desktop`, and user home directories for `galaxy-zoo-2-images.zip` or existing image folders.
* **Audit Result**: The 3.06 GB image archive is **NOT present locally** on the Mac.
* **Current Storage Available**: ~106 GiB.

---

## 3. Metadata & Image Filename Architecture

* **Available Labeled Galaxies**: `243,500` objects in `merged_zoo_data.csv.gz`.
* **Identifier Mapping Flow**:
  $$\text{SDSS Object ID (`dr7objid`)} \iff \text{GZ2 Mapping `objid`} \iff \text{Asset ID (`asset_id`)} \iff \text{Image Filename (`<asset_id>.jpg`)}$$
* **Filename Convention**: `<asset_id>.jpg` (e.g., `11.jpg`, `217750.jpg`).
* **Image Properties**: Standard Galaxy Zoo 2 images are RGB JPEGs at $424 \times 424$ resolution (~15 KB – 25 KB per image).

---

## 4. Stratified Subset Selection & Splitting Plan

To build a scientifically defensible model, the initial subset of 10,000 galaxies will be selected using **stratified sampling** across key galaxy morphology classes:

| Morphology Class | Class Criteria / GZ2 Flags | Target Count | Percentage |
| :--- | :--- | :--- | :--- |
| **Smooth / Ellipticals** | `gz2class` in (`Ei`, `Er`, `Ec`) | `3,500` | 35.0% |
| **Disk / Feature Galaxies** | `gz2class` in (`Ser`, `Sen`) | `2,500` | 25.0% |
| **Spirals & Barred Spirals** | `gz2class` starts with (`Sb`, `Sc`, `SBb`, `SBc`) | `3,000` | 30.0% |
| **Odd / Mergers / Anomalies** | `t06_odd_a14_yes_flag == 1` or `t08_odd_feature` | `1,000` | 10.0% |
| **Total Initial Subset** | | **`10,000`** | **100.0%** |

### Train / Validation / Test Partitioning

* **Random Seed**: `seed = 42` (Fixed for 100% scientific reproducibility).
* **Train Set**: `70%` (7,000 galaxies)
* **Validation Set**: `15%` (1,500 galaxies)
* **Test Set**: `15%` (1,500 galaxies)
* **Split Storage**: Saved as a lightweight CSV index at `ml/data/splits/subset_10k_splits.csv`.

---

## 5. Storage-Efficient Acquisition Options

### Option A: Selective ZIP Extraction (Recommended for Kaggle Download)
1. Download `galaxy-zoo-2-images.zip` (3.06 GB transient download).
2. Use Python `zipfile` module to extract **ONLY** the 10,000 target `<asset_id>.jpg` files directly into `ml/data/raw/galaxy_zoo/images/`.
3. Immediately delete the 3.06 GB `.zip` file after extraction.
4. **Disk Footprint**: ~200 MB total.

### Option B: Direct SDSS SkyServer API Fetching (Zero ZIP Download)
1. Use celestial coordinates (`ra`, `dec`) from `merged_zoo_data.csv.gz`.
2. Fetch individual $424 \times 424$ JPEG cutouts for the 10,000 targets via the official SDSS SkyServer Cutout HTTP API.
3. Save directly to `ml/data/raw/galaxy_zoo/images/`.
4. **Disk Footprint**: ~200 MB total (requires **zero ZIP downloads**).

---

## 6. Disk Space Comparison

| Approach | Transient Download | Permanent Storage | Storage Savings |
| :--- | :--- | :--- | :--- |
| **Full Dataset Archive** | 3.06 GB | ~3.5 GB (extracted) | 0% |
| **Selective 10,000 Image Subset (Option A)** | 3.06 GB (deleted after) | **~200 MB** | **94.3%** |
| **SDSS SkyServer API Subset (Option B)** | 0 GB | **~200 MB** | **94.3%** |

---

## 7. Recommended Next Steps

1. **User Approval**: Await user confirmation on the storage strategy.
2. **Generate Subset Index**: Run an offline Python script to select the stratified 10,000 galaxy subset and save `ml/data/splits/subset_10k_splits.csv`.
3. **Acquire Subset Images**: Execute selective download/extraction for ONLY the 10,000 target images (~200 MB total).
