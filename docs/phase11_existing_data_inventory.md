# ASTRA Phase 11 — Existing Data Inventory Report

## Executive Summary
This document provides a comprehensive, file-by-file forensic inventory of all datasets, raw catalogs, manifests, splits, observation libraries, and artifacts in the ASTRA repository (`ml/data/` and `ml/artifacts/`).

Each file has been audited for structural attributes (format, size, record count, column schemas, coordinate availability, authoritative label status) and evaluated against the target astronomical object taxonomy: `GALAXY`, `STAR`, `QUASAR CANDIDATE`, `NEBULA`, and `EXOPLANET`.

---

## 1. Raw Data Inventory (`ml/data/raw/`)

### 1.1 `ml/data/raw/galaxy_zoo/merged_zoo_data.csv.gz`
- **Format & Compression**: Gzip-compressed CSV (`.csv.gz`)
- **File Size**: 51.26 MB
- **Record Count**: 243,500 objects
- **Column Count**: 236 columns
- **Key Schema Columns**:
  - Identifiers: `specobjid`, `dr8objid`, `dr7objid`
  - Coordinates: `ra`, `dec`, `rastring`, `decstring`
  - Survey Metadata: `sample_x`, `total_classifications`, `total_votes`
  - Vote Fractions & Debiased Probabilities: `t01_smooth_or_features_a01_smooth_debiased`, `t01_smooth_or_features_a02_features_or_disk_debiased`, `t01_smooth_or_features_a03_star_or_artifact_fraction`, `t02_edgeon_a04_yes_debiased`, `t04_spiral_a08_spiral_debiased`, `t03_bar_a06_bar_debiased`, `t06_odd_a14_yes_debiased`
- **Image Count**: 0 (Catalog metadata only)
- **Coordinate Availability**: **100% (RA/DEC present for all 243,500 objects)**
- **Object IDs**: Authoritative SDSS DR7 / DR8 SpecObj and ObjIDs
- **Authoritative Labels**: Authoritative for SDSS galaxy morphology (debasing applied from $\ge 40$ votes per object). Contains `star_or_artifact_fraction` representing crowd consensus on non-galaxy artifacts.
- **Taxonomy Support Capability**:
  - `GALAXY`: **Supported (Authoritative)**
  - `STAR`: **Not Supported** (Contains star/artifact vote fraction only; lacks astrometry, parallax, proper motion, or stellar classification)
  - `QUASAR`: **Not Supported** (Lacks spectroscopic redshift, broad lines, or AGN catalog flags)
  - `NEBULA`: **Not Supported** (Contains 0 emission line / nebular data)
  - `EXOPLANET`: **Not Supported** (Contains 0 transit or light curve data)

### 1.2 `ml/data/raw/galaxy_zoo/gz2_filename_mapping.csv`
- **Format**: Uncompressed CSV
- **File Size**: 12.56 MB
- **Record Count**: 245,609 rows
- **Key Columns**: `objid` (SDSS DR7 ObjID), `sample` (`original` / `extra`), `asset_id` (Integer filename key corresponding to `asset_id.jpg`)
- **Authoritative Labels**: ID lookup mapping only.
- **Taxonomy Support**: Metadata join table.

---

## 2. Processed Image Inventory (`ml/data/processed/`)

### 2.1 `ml/data/processed/galaxy_zoo/images/`
- **Format**: JPEG Images (`RGB`, $424 \times 424$ pixels)
- **Image Count**: 10,000 files (`20027.jpg` to `100035.jpg`, etc.)
- **Total Directory Size**: ~115 MB
- **Coordinates**: Linked via `manifest.csv`
- **Authoritative Labels**: Linked via `manifest.csv`
- **Taxonomy Support Capability**:
  - `GALAXY`: **Supported** (High-resolution SDSS galaxy cutouts)
  - `STAR` / `QUASAR` / `NEBULA` / `EXOPLANET`: **Not Supported** (Exclusively galaxy cutouts)

### 2.2 `ml/data/processed/galaxy_zoo/manifest.csv`
- **Format**: CSV
- **File Size**: 1.76 MB
- **Record Count**: 10,000 rows
- **Columns**: `asset_id`, `image_filename`, `dr7objid`, `ra`, `dec`, `gz2class`, `broad_morphology`, `split`, `total_classifications`, debiased vote fractions (`t01` through `t07`), `image_path`, `width`, `height`, `file_size_bytes`
- **Coordinates**: **100% (RA/DEC present)**
- **Authoritative Labels**: Authoritative for 4-class galaxy morphology (`SMOOTH`, `FEATURED_DISK`, `EDGE_ON`, `SPIRAL`).

---

## 3. Data Splits (`ml/data/splits/`)

### 3.1 `ml/data/splits/subset_10k_scientific_targets.csv`
- **Format**: CSV (1.50 MB, 10,000 rows)
- **Columns**: `dr7objid`, `asset_id`, `image_filename`, `ra`, `dec`, `split`, `target_4class`, `target_3class`, `prob_smooth`, `prob_features`, `prob_edgeon`, `prob_spiral`, `prob_bar`, `prob_odd`, `t01_margin`, `is_high_confidence`, `is_odd_anomaly`
- **Authoritative Labels**: Authoritative 4-class galaxy targets.

### 3.2 `ml/data/splits/subset_10k_splits.csv` & `subset_10k_archive_compatible_splits.csv`
- **Format**: CSV (1.18 MB each, 10,000 rows)
- **Purpose**: Enforces strict train/val/test partitions by `dr7objid` to prevent data leakage.

### 3.3 `ml/data/splits/domain_gate_splits.csv` & `domain_gate_v2_splits.csv`
- **Format**: CSV (0.51 MB & 1.19 MB)
- **Purpose**: Train/val/test splits for binary domain validation.

---

## 4. Domain Validation Datasets (`ml/data/domain_gate/` & `domain_gate_v2/`)

### 4.1 `ml/data/domain_gate/`
- **Images**: 3,658 files ($1,798$ astronomical cutouts, $1,800$ non-astronomical images, $60$ ambiguous)
- **Adversarial Test Images**: 120 positive astronomical cutouts (15 per subfolder across `hst_style`, `unusual_astro`, `sdss_style`, `survey_cutouts`, `stellar_fields`, `crowded_fields`, `low_contrast`, `nebular_fields`) + 260 negative images.
- **Manifest**: `domain_gate_manifest.csv` (13 columns)
- **Authoritative Labels**: Binary domain tags (`ASTRONOMICAL` vs `NON_ASTRONOMICAL`).
- **Taxonomy Support**: Supports binary domain rejection (`INCOMPATIBLE — IMAGE REJECTED`).

### 4.2 `ml/data/domain_gate_v2/`
- **Images**: 6,483 files ($1,983$ astronomical, $1,500$ non-astronomical, $1,000$ hard positives, $1,500$ hard negatives)
- **Manifest**: `domain_gate_v2/manifest.csv` (11 columns)
- **Authoritative Labels**: Binary domain tags for MobileNetV3-Small training.

---

## 5. Observation Library (`ml/data/library/`)

### 5.1 `ml/data/library/observation_library.csv` & `.json`
- **Format**: CSV (0.92 MB, 2,000 rows) & JSON (2.52 MB)
- **Columns**: `id`, `asset_id`, `dr7objid`, `ra`, `dec`, `gz2class`, `broad_morphology`, `object_type`, `confidence`, `anomaly_score`, `ood_score`, `priority`, `catalog_status`, `catalog_name`, `observation_time`, `image_url`, `split`, `is_demo`, `explanation`, `provenance`
- **Coordinates**: **100% (RA/DEC present)**
- **Authoritative Labels**: Demo / UI library records. Note: `object_type` values in demo records are derived from Galaxy Zoo base targets or zero-shot prompts and are not independent multi-class ground truth.

---

## 6. Artifacts (`ml/artifacts/`)

- `galaxy_zoo_embeddings.npy` (48.83 MB): 512-dimensional ResNet34 feature embeddings for 10,000 galaxy images.
- `galaxy_zoo_embedding_index.csv` (0.53 MB): Index linking asset IDs to embedding row indices.
- `triage_reference.json` (0.14 MB): Reference distribution parameters for novelty ($N$), uncertainty ($U$), and oddity ($O$).

---

## 7. Data Capability Matrix Summary

| Object Taxonomy Target | Ground-Truth Images | Ground-Truth Catalogs | Authoritative Labels Available? | Can Train Model Now? | Missing Infrastructure / Data |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GALAXY** | 10,000 JPEGs | 243,500 CSV rows | **YES** (Galaxy Zoo 2) | **YES** | None (Fully supported) |
| **NEBULA** | 15 test cutouts | None | **NO** | **NO** | Requires H-alpha / IR diffuse nebula datasets |
| **STAR** | 15 test cutouts | Star vote fraction only | **NO** | **NO** | Requires Gaia DR3 astrometry ($\varpi, \mu$) |
| **QUASAR CANDIDATE** | 15 survey cutouts | None | **NO** | **NO** | Requires SDSS DR16Q spectroscopic redshift ($z$) |
| **EXOPLANET** | 0 | None | **NO** | **NO** | Requires TESS/Kepler light curves & NASA Exoplanet Archive |
