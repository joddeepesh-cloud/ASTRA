#!/usr/bin/env python3
"""
ASTRA — Galaxy Zoo 10,000 Subset Generator

Creates a reproducible, balanced 10,000-galaxy subset with stratified
80% train / 10% validation / 10% test splits.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Path definitions relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "ml" / "data" / "raw" / "galaxy_zoo"
SPLITS_DIR = PROJECT_ROOT / "ml" / "data" / "splits"
OUTPUT_CSV = SPLITS_DIR / "subset_10k_splits.csv"

MERGED_DATA_PATH = RAW_DIR / "merged_zoo_data.csv.gz"
MAPPING_PATH = RAW_DIR / "gz2_filename_mapping.csv"

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
    print(f"=== ASTRA Galaxy Zoo 10,000 Subset Generation ===")
    print(f"Project root: {PROJECT_ROOT}")

    # 1. Verify inputs
    if not MERGED_DATA_PATH.exists():
        raise FileNotFoundError(f"Missing raw file: {MERGED_DATA_PATH}")
    if not MAPPING_PATH.exists():
        raise FileNotFoundError(f"Missing mapping file: {MAPPING_PATH}")

    print(f"Reading {MERGED_DATA_PATH.name}...")
    df_merged = pd.read_csv(MERGED_DATA_PATH)

    print(f"Reading {MAPPING_PATH.name}...")
    df_mapping = pd.read_csv(MAPPING_PATH)

    # 2. Join datasets on dr7objid == objid
    # Clean asset_id from mapping to avoid duplicate column confusion
    df_map_clean = df_mapping[['objid', 'asset_id']].drop_duplicates(subset=['objid'])
    
    # Drop asset_id from df_merged if present before join
    if 'asset_id' in df_merged.columns:
        df_merged = df_merged.drop(columns=['asset_id'])

    joined = df_merged.merge(df_map_clean, left_on='dr7objid', right_on='objid', how='inner')
    print(f"Successfully joined dataset: {len(joined):,} rows.")

    # 3. Create broad morphology category
    joined['broad_morphology'] = joined['gz2class'].apply(classify_broad_morphology)
    
    # Ensure mandatory fields are non-null
    mandatory_cols = ['dr7objid', 'ra', 'dec', 'gz2class', 'asset_id', 'broad_morphology']
    null_counts = joined[mandatory_cols].isnull().sum()
    if null_counts.sum() > 0:
        raise ValueError(f"Found null values in mandatory fields:\n{null_counts}")

    print("\nBroad morphology distribution in full joined dataset:")
    print(joined['broad_morphology'].value_counts())

    # 4. Create balanced 10,000 sample (2,500 per category)
    target_per_category = 2500
    subsets = []
    
    np.random.seed(RANDOM_SEED)

    categories = ['SMOOTH', 'DISK_FEATURE', 'SPIRAL', 'OTHER']
    for cat in categories:
        cat_df = joined[joined['broad_morphology'] == cat]
        available_count = len(cat_df)
        
        if available_count >= target_per_category:
            sampled_cat = cat_df.sample(n=target_per_category, random_state=RANDOM_SEED)
        else:
            print(f"Warning: Category {cat} has only {available_count} samples (less than {target_per_category}).")
            sampled_cat = cat_df
            
        subsets.append(sampled_cat)

    subset_df = pd.concat(subsets, ignore_index=True)
    
    # Shuffle subset deterministically
    subset_df = subset_df.sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)
    print(f"\nCreated subset of {len(subset_df):,} rows.")

    # 5. Stratified train/val/test splits (80% / 10% / 10%)
    train_dfs = []
    val_dfs = []
    test_dfs = []

    for cat in categories:
        cat_data = subset_df[subset_df['broad_morphology'] == cat].sample(frac=1.0, random_state=RANDOM_SEED)
        n_cat = len(cat_data)
        
        n_val = int(round(n_cat * 0.10))
        n_test = int(round(n_cat * 0.10))
        n_train = n_cat - n_val - n_test

        train_cat = cat_data.iloc[:n_train].copy()
        val_cat = cat_data.iloc[n_train:n_train + n_val].copy()
        test_cat = cat_data.iloc[n_train + n_val:].copy()

        train_cat['split'] = 'train'
        val_cat['split'] = 'val'
        test_cat['split'] = 'test'

        train_dfs.append(train_cat)
        val_dfs.append(val_cat)
        test_dfs.append(test_cat)

    final_df = pd.concat(train_dfs + val_dfs + test_dfs, ignore_index=True)
    
    # Shuffle final dataset
    final_df = final_df.sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)

    # 6. Add image_filename column
    final_df['image_filename'] = final_df['asset_id'].astype(str) + '.jpg'

    # Select and order key output columns
    key_cols = [
        'asset_id',
        'image_filename',
        'dr7objid',
        'ra',
        'dec',
        'gz2class',
        'broad_morphology',
        'split',
        'total_classifications',
        't01_smooth_or_features_a01_smooth_fraction',
        't01_smooth_or_features_a02_features_or_disk_fraction',
        't01_smooth_or_features_a03_star_or_artifact_fraction',
        't02_edgeon_a04_yes_fraction',
        't02_edgeon_a05_no_fraction',
        't03_bar_a06_bar_fraction',
        't04_spiral_a08_spiral_fraction',
        't06_odd_a14_yes_fraction',
        't07_rounded_a16_completely_round_fraction'
    ]

    final_output_df = final_df[key_cols]

    # Save output file
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    final_output_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved 10k split dataset to: {OUTPUT_CSV}")

    # 7. Perform Comprehensive Validation
    print("\n==================================================")
    print("VALIDATION CHECKS")
    print("==================================================")
    
    total_rows = len(final_output_df)
    train_rows = (final_output_df['split'] == 'train').sum()
    val_rows = (final_output_df['split'] == 'val').sum()
    test_rows = (final_output_df['split'] == 'test').sum()

    unique_assets = final_output_df['asset_id'].nunique()
    unique_dr7objids = final_output_df['dr7objid'].nunique()
    duplicate_count = final_output_df.duplicated(subset=['dr7objid']).sum()
    missing_vals = final_output_df.isnull().sum().sum()
    min_asset_id = final_output_df['asset_id'].min()
    max_asset_id = final_output_df['asset_id'].max()

    print(f"Total Rows: {total_rows:,}")
    print(f"Train Rows: {train_rows:,}")
    print(f"Val Rows:   {val_rows:,}")
    print(f"Test Rows:  {test_rows:,}")
    print(f"Unique asset_ids: {unique_assets:,}")
    print(f"Unique dr7objids: {unique_dr7objids:,}")
    print(f"Duplicate Count:  {duplicate_count}")
    print(f"Missing Values:   {missing_vals}")
    print(f"Min asset_id: {min_asset_id}, Max asset_id: {max_asset_id}")

    print("\nBroad Morphology Breakdown:")
    print(final_output_df['broad_morphology'].value_counts())

    print("\nBroad Morphology Breakdown by Split:")
    print(pd.crosstab(final_output_df['broad_morphology'], final_output_df['split']))

    # Assertions for verification
    assert total_rows == 10000, f"Expected 10,000 total rows, got {total_rows}"
    assert unique_assets == 10000, f"Expected 10,000 unique asset_ids, got {unique_assets}"
    assert unique_dr7objids == 10000, f"Expected 10,000 unique dr7objids, got {unique_dr7objids}"
    assert train_rows + val_rows + test_rows == 10000, "Splits do not sum to 10,000"
    assert train_rows == 8000, f"Expected 8,000 train rows, got {train_rows}"
    assert val_rows == 1000, f"Expected 1,000 val rows, got {val_rows}"
    assert test_rows == 1000, f"Expected 1,000 test rows, got {test_rows}"

    # Check leakages
    train_ids = set(final_output_df[final_output_df['split'] == 'train']['dr7objid'])
    val_ids = set(final_output_df[final_output_df['split'] == 'val']['dr7objid'])
    test_ids = set(final_output_df[final_output_df['split'] == 'test']['dr7objid'])

    assert len(train_ids.intersection(val_ids)) == 0, "Data leakage between train and val!"
    assert len(train_ids.intersection(test_ids)) == 0, "Data leakage between train and test!"
    assert len(val_ids.intersection(test_ids)) == 0, "Data leakage between val and test!"

    print("\n[SUCCESS] All validation assertions passed successfully!")

if __name__ == '__main__':
    main()
