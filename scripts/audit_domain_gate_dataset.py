import os
import sys
import pandas as pd
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MANIFEST_PATH = "ml/data/domain_gate_manifest.csv"
SPLITS_PATH = "ml/data/splits/domain_gate_splits.csv"
GRID_ARTIFACT_PATH = "ml/artifacts/domain_gate_sample_grid.png"

def run_scientific_audit():
    print("=" * 60)
    print("  ASTRA PHASE 10A — DOMAIN GATE SCIENTIFIC AUDIT SCRIPT")
    print("=" * 60)
    
    # 1. Required Files Existence Check
    for req_file in [MANIFEST_PATH, SPLITS_PATH]:
        if not os.path.exists(req_file):
            print(f"[ERROR] Required dataset file missing: {req_file}")
            sys.exit(1)
            
    df_manifest = pd.read_csv(MANIFEST_PATH)
    df_splits = pd.read_csv(SPLITS_PATH)
    
    # 2. Required Columns Validation
    req_cols = ['image_id', 'path', 'source', 'domain_label', 'group_id', 'split', 'width', 'height', 'channels', 'format', 'sha256']
    missing_cols = [c for c in req_cols if c not in df_manifest.columns]
    if missing_cols:
        print(f"[ERROR] Missing required columns in manifest: {missing_cols}")
        sys.exit(1)
        
    print(f"\n[OK] Manifest loaded successfully ({len(df_manifest)} total samples)")
    
    # 3. File Existence & Decodability Integrity Audit
    missing_files = 0
    corrupt_files = 0
    
    for idx, row in df_manifest.iterrows():
        p = row['path']
        if not os.path.exists(p):
            print(f"[FAIL] File missing: {p}")
            missing_files += 1
            continue
        try:
            with Image.open(p) as img:
                img.verify()
        except Exception as e:
            print(f"[FAIL] Corrupt image {p}: {e}")
            corrupt_files += 1
            
    if missing_files > 0 or corrupt_files > 0:
        print(f"[ERROR] File Integrity Audit FAILED! Missing: {missing_files}, Corrupt: {corrupt_files}")
        sys.exit(1)
    else:
        print("[OK] File Integrity Audit PASSED: 0 missing, 0 corrupt files.")
        
    # 4. Duplicate Check (SHA-256)
    dups = df_manifest[df_manifest.duplicated(subset=['sha256'], keep=False)]
    if len(dups) > 0:
        # Check if duplicates cross split boundaries
        dup_splits = dups.groupby('sha256')['split'].nunique()
        cross_split_dups = dup_splits[dup_splits > 1]
        if len(cross_split_dups) > 0:
            print(f"[ERROR] Cross-Split Duplicate Audit FAILED! {len(cross_split_dups)} duplicate hashes cross splits.")
            sys.exit(1)
        else:
            print(f"[WARNING] Found {len(dups)} intra-split duplicate files (same split).")
    else:
        print("[OK] Duplicate Audit PASSED: 0 SHA-256 duplicate files.")
        
    # 5. Group Leakage Check
    # Ensure no group_id appears in multiple splits
    group_splits = df_manifest.groupby('group_id')['split'].nunique()
    leaked_groups = group_splits[group_splits > 1]
    if len(leaked_groups) > 0:
        print(f"[ERROR] Group Leakage Audit FAILED! {len(leaked_groups)} group_ids leak across splits.")
        print(df_manifest[df_manifest['group_id'].isin(leaked_groups.index)][['image_id', 'group_id', 'split']])
        sys.exit(1)
    else:
        print("[OK] Group Leakage Audit PASSED: 0 group_ids leak across splits.")
        
    # 6. Class Distribution Report
    print("\n--- CLASS DISTRIBUTION ---")
    class_dist = df_manifest['domain_label'].value_counts()
    for cls, cnt in class_dist.items():
        pct = (cnt / len(df_manifest)) * 100
        print(f"  {cls:<18}: {cnt:>5} samples ({pct:.1f}%)")
        
    # 7. Split Distribution Report
    print("\n--- SPLIT DISTRIBUTION ---")
    split_dist = df_manifest['split'].value_counts()
    for s, cnt in split_dist.items():
        pct = (cnt / len(df_manifest)) * 100
        print(f"  {s:<18}: {cnt:>5} samples ({pct:.1f}%)")
        
    print("\n--- CLASS PER SPLIT BREAKDOWN ---")
    ct = pd.crosstab(df_manifest['split'], df_manifest['domain_label'])
    print(ct)
    
    # 8. Source Distribution Report
    print("\n--- SOURCE DISTRIBUTION ---")
    source_dist = df_manifest['source'].value_counts()
    for src, cnt in source_dist.items():
        pct = (cnt / len(df_manifest)) * 100
        print(f"  {src:<50}: {cnt:>5} samples ({pct:.1f}%)")

    # 9. Subcategory Breakdown Report
    print("\n--- SUBCATEGORY BREAKDOWN ---")
    sub_dist = df_manifest['subcategory'].value_counts()
    for sub, cnt in sub_dist.items():
        pct = (cnt / len(df_manifest)) * 100
        print(f"  {sub:<25}: {cnt:>5} samples ({pct:.1f}%)")

    # 10. Generate Visual Audit Grid Artifact
    print("\nGenerating visual audit sample grid artifact...")
    generate_sample_grid(df_manifest)

    print("\n" + "=" * 60)
    print("  ALL SCIENTIFIC AUDIT QUALITY GATES PASSED SUCCESSFULLY!")
    print("=" * 60)

def generate_sample_grid(df_manifest):
    fig, axes = plt.subplots(4, 5, figsize=(15, 12))
    fig.suptitle("ASTRA Domain Gate Visual Audit — Sample Grid", fontsize=16, fontweight='bold', y=0.98)
    
    # Select representative samples
    categories = [
        ('ASTRONOMICAL', 'Galaxy Zoo (SDSS)'),
        ('ASTRONOMICAL', 'Public Astronomical Survey Cutouts (SDSS/HST synth)'),
        ('NON_ASTRONOMICAL', 'natural_scenes'),
        ('NON_ASTRONOMICAL', 'hard_negatives'),
    ]
    
    # Grid Layout:
    # Row 0: Astronomical (Galaxy Zoo)
    # Row 1: Astronomical (Survey Cutouts)
    # Row 2: Non-Astronomical (Nature / Objects / Biological / Graphics)
    # Row 3: Non-Astronomical (Hard Negatives & Ambiguous)
    
    sample_queries = [
        df_manifest[df_manifest['source'] == 'Galaxy Zoo 2 (SDSS)'].sample(5, random_state=42),
        df_manifest[df_manifest['source'] == 'Public Astronomical Survey Cutouts (SDSS/HST synth)'].sample(5, random_state=42),
        df_manifest[df_manifest['subcategory'].isin(['natural_scenes', 'objects_vehicles', 'biological', 'graphics_ui'])].sample(5, random_state=42),
        pd.concat([
            df_manifest[df_manifest['subcategory'] == 'hard_negatives'].sample(3, random_state=42),
            df_manifest[df_manifest['domain_label'] == 'AMBIGUOUS'].sample(2, random_state=42)
        ])
    ]
    
    row_titles = [
        "ASTRONOMICAL: Galaxy Zoo Morphology",
        "ASTRONOMICAL: Survey Cutouts & Fields",
        "NON-ASTRONOMICAL: Nature, Objects, UI",
        "HARD NEGATIVES & AMBIGUOUS REVIEW"
    ]
    
    for r_idx in range(4):
        df_row = sample_queries[r_idx]
        for c_idx in range(5):
            ax = axes[r_idx, c_idx]
            if c_idx < len(df_row):
                item = df_row.iloc[c_idx]
                img_path = item['path']
                try:
                    img = Image.open(img_path)
                    ax.imshow(img)
                    title = f"{item['domain_label']}\n{item['subcategory']}"
                    ax.set_title(title, fontsize=9, color='navy' if item['domain_label']=='ASTRONOMICAL' else ('darkred' if item['domain_label']=='NON_ASTRONOMICAL' else 'purple'))
                except Exception as e:
                    ax.text(0.5, 0.5, f"Error: {e}", ha='center')
            ax.axis('off')
            
    plt.tight_layout()
    plt.savefig(GRID_ARTIFACT_PATH, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Visual audit grid saved to {GRID_ARTIFACT_PATH}")

if __name__ == '__main__':
    run_scientific_audit()
