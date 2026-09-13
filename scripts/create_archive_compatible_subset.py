#!/usr/bin/env python3
"""
ASTRA — Archive-Compatible 10,000 Galaxy Zoo Subset Generator

Generates ml/data/splits/subset_10k_archive_compatible_splits.csv by taking
ml/data/splits/subset_10k_splits.csv, identifying the 21 missing images in
~/Downloads/galaxy-zoo-2-images.zip, and replacing them with 21 valid 'OTHER'
morphology galaxies that exist in the ZIP archive and preserve the exact 8,000/1,000/1,000
train/val/test split and 2,500 per category balance.
"""

import sys
import zipfile
import pandas as pd
import numpy as np
from pathlib import Path

# Path definitions
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "ml" / "data" / "raw" / "galaxy_zoo"
SPLITS_DIR = PROJECT_ROOT / "ml" / "data" / "splits"

ORIGINAL_SPLITS_CSV = SPLITS_DIR / "subset_10k_splits.csv"
NEW_SPLITS_CSV = SPLITS_DIR / "subset_10k_archive_compatible_splits.csv"

ZIP_PATH = Path.home() / "Downloads" / "galaxy-zoo-2-images.zip"
MERGED_DATA_PATH = RAW_DIR / "merged_zoo_data.csv.gz"
MAPPING_PATH = RAW_DIR / "gz2_filename_mapping.csv"
DOCS_PATH = PROJECT_ROOT / "docs" / "galaxy_zoo_archive_compatibility.md"

RANDOM_SEED = 42

def classify_broad_morphology(gz2class: str) -> str:
    """Categorizes GZ2 morphology into 4 broad categories."""
    if not isinstance(gz2class, str):
        return 'OTHER'
    if gz2class.startswith(('Ei', 'Er', 'Ec')):
        return 'SMOOTH'
    elif gz2class in ['Ser', 'Sen']:
        return 'DISK_FEATURE'
    elif gz2class.startswith(('Sb', 'Sc', 'SBb', 'SBc')):
        return 'SPIRAL'
    else:
        return 'OTHER'

def main():
    print("=== ASTRA — Archive-Compatible Subset Generation ===")
    
    # 1. Verify input files
    if not ORIGINAL_SPLITS_CSV.exists():
        raise FileNotFoundError(f"Missing original splits CSV: {ORIGINAL_SPLITS_CSV}")
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Missing ZIP archive: {ZIP_PATH}")
        
    print(f"Reading original subset: {ORIGINAL_SPLITS_CSV}")
    df_orig = pd.read_csv(ORIGINAL_SPLITS_CSV)
    
    # 2. Build ZIP Archive Member Index
    print(f"Inspecting archive index from {ZIP_PATH.name}...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        namelist = zf.namelist()
        archive_members = {Path(m).name for m in namelist if Path(m).name}
        
    print(f"Total archive members: {len(archive_members):,}")
    
    # 3. Identify unavailable rows
    is_available = df_orig['image_filename'].isin(archive_members)
    available_df = df_orig[is_available].copy()
    missing_df = df_orig[~is_available].copy()
    
    num_missing = len(missing_df)
    print(f"Original subset rows: {len(df_orig):,}")
    print(f"Available in archive: {len(available_df):,}")
    print(f"Missing from archive: {num_missing}")
    
    assert num_missing == 21, f"Expected exactly 21 missing rows, found {num_missing}"
    assert (missing_df['broad_morphology'] == 'OTHER').all(), "All missing rows should be 'OTHER' category"
    
    missing_split_counts = missing_df['split'].value_counts()
    print("Missing rows breakdown by split:")
    print(missing_split_counts)

    # 4. Load full dataset to find replacement candidates
    print("\nLoading raw dataset to find replacement candidates...")
    df_merged = pd.read_csv(MERGED_DATA_PATH)
    df_map = pd.read_csv(MAPPING_PATH)
    
    df_map_clean = df_map[['objid', 'asset_id']].drop_duplicates(subset=['objid'])
    if 'asset_id' in df_merged.columns:
        df_merged = df_merged.drop(columns=['asset_id'])
        
    joined = df_merged.merge(df_map_clean, left_on='dr7objid', right_on='objid', how='inner')
    joined['broad_morphology'] = joined['gz2class'].apply(classify_broad_morphology)
    joined['image_filename'] = joined['asset_id'].astype(str) + '.jpg'
    
    # Filter candidates:
    # 1. Must be in archive_members
    # 2. Must NOT be in df_orig (neither dr7objid nor asset_id)
    # 3. Must have broad_morphology == 'OTHER'
    already_selected_ids = set(df_orig['dr7objid'])
    
    candidate_mask = (
        joined['image_filename'].isin(archive_members) &
        ~joined['dr7objid'].isin(already_selected_ids) &
        (joined['broad_morphology'] == 'OTHER')
    )
    
    candidates = joined[candidate_mask].copy()
    print(f"Found {len(candidates):,} valid replacement candidates in raw dataset!")
    
    # 5. Sample replacement rows matching the exact split requirements of missing rows
    np.random.seed(RANDOM_SEED)
    shuffled_candidates = candidates.sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)
    
    replacement_rows = []
    current_idx = 0
    
    for split_name, count_needed in missing_split_counts.items():
        needed_df = shuffled_candidates.iloc[current_idx : current_idx + count_needed].copy()
        needed_df['split'] = split_name
        replacement_rows.append(needed_df)
        current_idx += count_needed
        
    replacements_df = pd.concat(replacement_rows, ignore_index=True)
    print(f"Selected {len(replacements_df)} replacement rows matching missing splits.")
    
    # Format replacement columns to match original subset schema
    for col in df_orig.columns:
        if col not in replacements_df.columns:
            replacements_df[col] = np.nan
            
    replacements_formatted = replacements_df[df_orig.columns].copy()
    
    # Combine available original rows + replacement rows
    new_subset_df = pd.concat([available_df, replacements_formatted], ignore_index=True)
    
    # Shuffle final dataset deterministically
    new_subset_df = new_subset_df.sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)
    
    # 6. Save new CSV
    new_subset_df.to_csv(NEW_SPLITS_CSV, index=False)
    print(f"\nSaved archive-compatible subset to: {NEW_SPLITS_CSV}")

    # 7. Perform Comprehensive Validation
    print("\n==================================================")
    print("VALIDATION REPORT FOR NEW SUBSET")
    print("==================================================")
    
    total_rows = len(new_subset_df)
    unique_asset_ids = new_subset_df['asset_id'].nunique()
    unique_filenames = new_subset_df['image_filename'].nunique()
    unique_dr7objids = new_subset_df['dr7objid'].nunique()
    
    morph_counts = new_subset_df['broad_morphology'].value_counts()
    split_counts = new_subset_df['split'].value_counts()
    
    in_archive_count = new_subset_df['image_filename'].isin(archive_members).sum()
    missing_archive_count = total_rows - in_archive_count
    
    duplicate_asset_ids = total_rows - unique_asset_ids
    duplicate_filenames = total_rows - unique_filenames
    
    # Split overlap check
    train_ids = set(new_subset_df[new_subset_df['split'] == 'train']['asset_id'])
    val_ids = set(new_subset_df[new_subset_df['split'] == 'val']['asset_id'])
    test_ids = set(new_subset_df[new_subset_df['split'] == 'test']['asset_id'])
    
    overlap_train_val = len(train_ids.intersection(val_ids))
    overlap_train_test = len(train_ids.intersection(test_ids))
    overlap_val_test = len(val_ids.intersection(test_ids))
    total_overlap = overlap_train_val + overlap_train_test + overlap_val_test
    
    print(f"Total Rows:                {total_rows:,}")
    print(f"Unique Asset IDs:          {unique_asset_ids:,}")
    print(f"Unique Image Filenames:    {unique_filenames:,}")
    print(f"Unique dr7objids:          {unique_dr7objids:,}")
    
    print("\nMorphology Distribution:")
    print(morph_counts)
    
    print("\nSplit Distribution:")
    print(split_counts)
    
    print(f"\nImages Present in Archive: {in_archive_count:,}")
    print(f"Images Missing from Archive:{missing_archive_count}")
    
    print(f"\nDuplicate Asset IDs:       {duplicate_asset_ids}")
    print(f"Duplicate Filenames:       {duplicate_filenames}")
    print(f"Split Overlap (Leakage):   {total_overlap}")
    
    # Assertions
    assert total_rows == 10000, f"Expected 10,000 total rows, got {total_rows}"
    assert unique_asset_ids == 10000, f"Expected 10,000 unique asset IDs, got {unique_asset_ids}"
    assert unique_filenames == 10000, f"Expected 10,000 unique filenames, got {unique_filenames}"
    assert missing_archive_count == 0, f"Expected 0 missing from archive, got {missing_archive_count}"
    assert duplicate_asset_ids == 0, f"Found duplicate asset IDs: {duplicate_asset_ids}"
    assert duplicate_filenames == 0, f"Found duplicate filenames: {duplicate_filenames}"
    assert total_overlap == 0, f"Found split overlap: {total_overlap}"
    
    assert split_counts['train'] == 8000, f"Expected 8,000 train rows, got {split_counts['train']}"
    assert split_counts['val'] == 1000, f"Expected 1,000 val rows, got {split_counts['val']}"
    assert split_counts['test'] == 1000, f"Expected 1,000 test rows, got {split_counts['test']}"
    
    for cat in ['SMOOTH', 'DISK_FEATURE', 'SPIRAL', 'OTHER']:
        assert morph_counts[cat] == 2500, f"Expected 2,500 for {cat}, got {morph_counts[cat]}"

    print("\n[SUCCESS] All archive-compatibility validation assertions passed!")

if __name__ == '__main__':
    main()
