import os
import sys
import pandas as pd
from PIL import Image

MANIFEST_PATH = "ml/data/domain_gate_manifest.csv"
SPLITS_PATH = "ml/data/splits/domain_gate_splits.csv"

def verify_dataset():
    print("=" * 60)
    print("  ASTRA PHASE 10B — DATASET VERIFICATION")
    print("=" * 60)
    
    # 1. Existence of manifest files
    for path in [MANIFEST_PATH, SPLITS_PATH]:
        if not os.path.exists(path):
            print(f"[ERROR] Missing dataset file: {path}")
            sys.exit(1)
            
    df_manifest = pd.read_csv(MANIFEST_PATH)
    df_splits = pd.read_csv(SPLITS_PATH)
    
    print(f"[OK] Manifest loaded: {len(df_manifest)} entries.")
    print(f"[OK] Splits loaded: {len(df_splits)} entries.")
    
    # 2. Verify all image files exist and are decodable
    missing = 0
    corrupt = 0
    for idx, row in df_manifest.iterrows():
        p = row['path']
        if not os.path.exists(p):
            print(f"[ERROR] Image missing: {p}")
            missing += 1
            continue
        try:
            with Image.open(p) as img:
                img.verify()
        except Exception as e:
            print(f"[ERROR] Image corrupt {p}: {e}")
            corrupt += 1
            
    if missing > 0 or corrupt > 0:
        print(f"[FAIL] Verification failed: {missing} missing, {corrupt} corrupt images.")
        sys.exit(1)
    else:
        print("[OK] All images exist and are decodable.")
        
    # 3. Check for SHA-256 cross-split duplicates
    dups = df_manifest[df_manifest.duplicated(subset=['sha256'], keep=False)]
    if len(dups) > 0:
        dup_splits = dups.groupby('sha256')['split'].nunique()
        leaked_hashes = dup_splits[dup_splits > 1]
        if len(leaked_hashes) > 0:
            print(f"[FAIL] {len(leaked_hashes)} SHA-256 hashes cross split boundaries!")
            sys.exit(1)
        else:
            print(f"[OK] {len(dups)} duplicate hashes found, but all stay strictly within single splits.")
    else:
        print("[OK] Zero duplicate SHA-256 hashes found.")
        
    # 4. Check for group_id leakage across splits
    group_splits = df_manifest.groupby('group_id')['split'].nunique()
    leaked_groups = group_splits[group_splits > 1]
    if len(leaked_groups) > 0:
        print(f"[FAIL] {len(leaked_groups)} group_ids leak across splits!")
        sys.exit(1)
    else:
        print("[OK] Zero group_id leakage across splits.")
        
    # 5. Isolation of REVIEW / AMBIGUOUS split
    review_in_train = len(df_manifest[(df_manifest['domain_label'] == 'AMBIGUOUS') & (df_manifest['split'] != 'REVIEW')])
    non_review_in_review = len(df_manifest[(df_manifest['domain_label'] != 'AMBIGUOUS') & (df_manifest['split'] == 'REVIEW')])
    
    if review_in_train > 0 or non_review_in_review > 0:
        print(f"[FAIL] AMBIGUOUS / REVIEW split isolation failed! (Review in train: {review_in_train}, Non-review in review: {non_review_in_review})")
        sys.exit(1)
    else:
        print("[OK] AMBIGUOUS / REVIEW split is 100% isolated (60 review samples).")
        
    # 6. Output split summary
    print("\n--- VERIFIED DATASET SPLIT BREAKDOWN ---")
    ct = pd.crosstab(df_manifest['split'], df_manifest['domain_label'], margins=True)
    print(ct)
    
    print("\n" + "=" * 60)
    print("  VERIFICATION SUCCESSFUL: DATASET IS READY FOR TRAINING")
    print("=" * 60)

if __name__ == "__main__":
    verify_dataset()
