# ASTRA — Reproducible 10,000 Galaxy Zoo Subset & Split Specification

**Project**: ASTRA — AI-Based Astronomical Observation Triage System  
**Document Path**: `docs/galaxy_zoo_subset_10k.md`  
**Output CSV Path**: `ml/data/splits/subset_10k_splits.csv`  
**Generator Script**: `scripts/create_galaxy_zoo_subset.py`  
**Random Seed**: `42` (Fixed for 100% scientific reproducibility)  
**Execution Environment**: `/Users/deepeshjoshi/Desktop/ASTRA/.venv`  

---

## 1. Executive Summary

A reproducible 10,000-galaxy subset was extracted from the 243,500 joined Galaxy Zoo 2 dataset. The subset is perfectly balanced across four broad morphology categories (2,500 objects each) and partitioned into **80% Train (8,000)**, **10% Validation (1,000)**, and **10% Test (1,000)** splits. 

All validation assertions passed with **zero data leakage**, zero duplicate objects, zero missing values, and zero unneeded raw data downloads or modifications.

---

## 2. Source Datasets & Join Specification

1. **Classification Catalog**: `ml/data/raw/galaxy_zoo/merged_zoo_data.csv.gz` (243,500 rows, 236 columns)
2. **Filename Mapping Catalog**: `ml/data/raw/galaxy_zoo/gz2_filename_mapping.csv` (355,990 rows, 3 columns)
3. **Join Key**: `merged_zoo_data.dr7objid == gz2_filename_mapping.objid`
4. **Join Integrity**: 243,500 / 243,500 1-to-1 match.

---

## 3. Broad Morphology Definitions

Broad morphology categories were mapped from the official `gz2class` string column without altering the underlying `gz2class` labels:

| Broad Category | `gz2class` Rule / Prefix | Population in Full Data | Selected Subset Count |
| :--- | :--- | :--- | :--- |
| **`SMOOTH`** | Begins with `Ei`, `Er`, `Ec` | `103,515` | `2,500` |
| **`DISK_FEATURE`** | Equals `Ser` or `Sen` | `22,374` | `2,500` |
| **`SPIRAL`** | Begins with `Sb`, `Sc`, `SBb`, `SBc` | `107,156` | `2,500` |
| **`OTHER`** | All other GZ2 morphology classes | `10,455` | `2,500` |
| **Total** | | **`243,500`** | **`10,000`** |

---

## 4. Sampling Method & Train/Val/Test Partitioning

* **Sampling Method**: Balanced random sampling per category using `random_state = 42`.
* **Partition Ratios**:
  * **Train**: `80.0%` (8,000 rows)
  * **Validation**: `10.0%` (1,000 rows)
  * **Test**: `10.0%` (1,000 rows)
* **Stratification**: Partitioned independently per broad morphology category to ensure identical class distributions across splits.

### Category Distribution by Split

| Broad Category | Train (80%) | Validation (10%) | Test (10%) | Total |
| :--- | :--- | :--- | :--- | :--- |
| **`SMOOTH`** | 2,000 | 250 | 250 | **2,500** |
| **`DISK_FEATURE`** | 2,000 | 250 | 250 | **2,500** |
| **`SPIRAL`** | 2,000 | 250 | 250 | **2,500** |
| **`OTHER`** | 2,000 | 250 | 250 | **2,500** |
| **Total** | **8,000** | **1,000** | **1,000** | **10,000** |

---

## 5. Output CSV Schema (`subset_10k_splits.csv`)

The output file contains **18 columns** including core identifiers, coordinates, broad morphology, split assignments, and key task fraction metrics:

1. `asset_id`: Kaggle Galaxy Zoo 2 Asset ID (e.g. `217750`)
2. `image_filename`: Formatted image filename string (`<asset_id>.jpg`, e.g. `217750.jpg`)
3. `dr7objid`: SDSS DR7 Photometric Object ID (`587738569780428805`)
4. `ra`: Right Ascension in degrees (`192.41083`)
5. `dec`: Declination in degrees (`15.164207`)
6. `gz2class`: Official GZ2 morphology class designation (`Ser`)
7. `broad_morphology`: Assigned broad morphology (`DISK_FEATURE`)
8. `split`: Assigned split partition (`train`, `val`, `test`)
9. `total_classifications`: Volunteer vote count
10–18. Key GZ2 task fraction votes (`t01_smooth`, `t01_features`, `t01_artifact`, `t02_edgeon_yes`, `t02_edgeon_no`, `t03_bar`, `t04_spiral`, `t06_odd`, `t07_rounded`)

---

## 6. Empirical Validation Results

* **Total Row Count**: `10,000`
* **Unique `asset_id` Count**: `10,000` (100% unique)
* **Unique `dr7objid` Count**: `10,000` (100% unique)
* **Duplicate Rows**: `0`
* **Null / Missing Values**: `0`
* **Asset ID Range**: Min `37`, Max `295,279`
* **Data Leakage Checks**:
  * `train ∩ val`: `0` overlapping objects
  * `train ∩ test`: `0` overlapping objects
  * `val ∩ test`: `0` overlapping objects
* **Raw Datasets State**: `ml/data/raw/galaxy_zoo/` files remain completely untouched.
* **Image Download State**: `0` images downloaded.
