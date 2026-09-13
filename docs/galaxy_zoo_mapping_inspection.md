# Galaxy Zoo 2 Filename Mapping Inspection Report

**Project**: ASTRA — AI-Based Astronomical Observation Triage System  
**Document Path**: `docs/galaxy_zoo_mapping_inspection.md`  
**Inspected File**: `ml/data/raw/galaxy_zoo/gz2_filename_mapping.csv`  
**Original File Source**: `~/Downloads/gz2_filename_mapping.csv` (Copied, original preserved)  
**Environment Used**: `/Users/deepeshjoshi/Desktop/ASTRA/.venv`  

---

## 1. Executive Summary

The `gz2_filename_mapping.csv` dataset was copied from `~/Downloads/` into `ml/data/raw/galaxy_zoo/` without modifying or deleting the original download. The file was verified and inspected using Pandas in the local `.venv` environment.

The mapping file contains **355,990 rows** and **3 columns**, providing a direct lookup between SDSS photometric object IDs (`objid`), sample split categories (`sample`), and Kaggle Galaxy Zoo 2 asset IDs (`asset_id`). 

---

## 2. Measured Dataset Metrics

| Metric | Value |
| :--- | :--- |
| **Total Rows** | `355,990` |
| **Total Columns** | `3` |
| **Missing Values (Nulls)** | `0` across all columns |
| **Unique `objid`s** | `325,651` |
| **Unique `asset_id`s** | `355,990` (1 to 355,990) |
| **Unique `sample`s** | `5` (`original`, `stripe82_coadd_1`, `stripe82_coadd_2`, `extra`, `stripe82`) |

### Column Schema & Data Types

| Column Name | Data Type | Null Count | Unique Count | Description |
| :--- | :--- | :--- | :--- | :--- |
| `objid` | `int64` | `0` | `325,651` | SDSS 64-bit Photometric Object Identifier |
| `sample` | `object` (string) | `0` | `5` | Galaxy Zoo 2 sample category |
| `asset_id` | `int64` | `0` | `355,990` | Kaggle GZ2 Asset ID corresponding to image filename |

---

## 3. Sample Breakdown (`sample` Column)

| Sample Category | Count | Percentage |
| :--- | :--- | :--- |
| **`original`** | `245,609` | 68.99% |
| **`stripe82_coadd_1`** | `30,346` | 8.52% |
| **`stripe82_coadd_2`** | `30,339` | 8.52% |
| **`extra`** | `28,174` | 7.91% |
| **`stripe82`** | `21,522` | 6.05% |
| **Total** | **`355,990`** | **100.00%** |

> **Note**: The `original` sample set contains **245,609 images**, matching the ~243,000 galaxy image dataset specification for Galaxy Zoo 2.

---

## 4. Head and Tail Data Inspection

### First 5 Rows (`head(5)`)

```
                objid    sample  asset_id
0  587722981736120347  original         1
1  587722981736579107  original         2
2  587722981741363294  original         3
3  587722981741363323  original         4
4  587722981741559888  original         5
```

### Last 5 Rows (`tail(5)`)

```
                      objid            sample  asset_id
355985  8647475122541625731  stripe82_coadd_2    355986
355986  8647475122541625762  stripe82_coadd_2    355987
355987  8647475122541625774  stripe82_coadd_2    355988
355988  8647475122761762019  stripe82_coadd_2    355989
355989  8647475122761762804  stripe82_coadd_2    355990
```

---

## 5. Key Column Identifications & Filename Format

### Filename Format Verification
* **Image Filename Format**: `<asset_id>.jpg`
* **Sample Filenames**: `1.jpg`, `2.jpg`, ..., `11.jpg`, `12.jpg`, `13.jpg`, `14.jpg`, `15.jpg`, ..., `355990.jpg`.
* **Verification Result**: The dataset uses `asset_id` to construct filenames. For instance, `asset_id = 11` corresponds directly to `11.jpg`.

### Key Column Mapping
1. **Image Filename / Identifier**: `asset_id` (converted to string with `.jpg` extension).
2. **Astronomical Object ID**: `objid` (SDSS ObjID).
3. **Sample Category**: `sample`.
4. **Morphology Labels Status**: `gz2_filename_mapping.csv` is strictly a **filename-to-object lookup table**. It does **not** contain the Galaxy Zoo 2 morphological classification columns (e.g., `smooth`, `features/disk`, `edge-on`, `spiral arms`). To obtain morphology labels for training and evaluation, `objid` must be joined with the main Galaxy Zoo 2 catalog (such as `gz2_hart16.csv` or `zoo2MainSpecz.csv`).

---

## 6. Final Verification Checklist

- [x] **Project Exists**: `/Users/deepeshjoshi/Desktop/ASTRA` verified.
- [x] **Local `.venv` Exists**: `/Users/deepeshjoshi/Desktop/ASTRA/.venv` verified.
- [x] **Target Directory Created**: `ml/data/raw/galaxy_zoo/` initialized.
- [x] **CSV Copied Safely**: Copied to `ml/data/raw/galaxy_zoo/gz2_filename_mapping.csv`.
- [x] **Original Download Intact**: `/Users/deepeshjoshi/Downloads/gz2_filename_mapping.csv` remains untouched in Downloads.
- [x] **Pandas Read Success**: File loaded cleanly with 0 nulls.
- [x] **Row Count**: `355,990` rows.
- [x] **Column Count**: `3` columns (`objid`, `sample`, `asset_id`).
- [x] **Filename Format Identified**: `<asset_id>.jpg` (`11.jpg`, `12.jpg`, etc.).
- [x] **Morphology Labels Identified**: Requires joining on `objid` with Galaxy Zoo 2 classifications catalog (`gz2_hart16.csv`).
