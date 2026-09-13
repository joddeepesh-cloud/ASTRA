import pandas as pd
import numpy as np

# Load datasets
df_merged = pd.read_csv("ml/data/raw/galaxy_zoo/merged_zoo_data.csv.gz")
df_splits = pd.read_csv("ml/data/splits/subset_10k_archive_compatible_splits.csv")
df = df_splits.merge(df_merged, on="dr7objid", how="inner", suffixes=("", "_raw"))

print(f"Loaded 10k subset merged data shape: {df.shape}")

# Analyze gz2class code string prefix
# gz2class strings: E (Elliptical), S (Spiral), SB (Barred spiral), Se (Edge-on), etc.
def parse_gz2class(code):
    if pd.isna(code):
        return "UNKNOWN"
    if code.startswith("E"):
        return "SMOOTH_ELLIPTICAL"
    elif code.startswith("Ser") or code.startswith("Sen") or code.startswith("Seb") or code.startswith("Ec"):
        # Edge-on in GZ2 naming scheme
        return "EDGE_ON"
    elif code.startswith("SB") or code.startswith("S"):
        return "SPIRAL"
    else:
        return "OTHER"

df['gz2_broad_parsed'] = df['gz2class'].apply(parse_gz2class)
print("\n--- gz2class Broad Parsed Distribution ---")
print(df['gz2_broad_parsed'].value_counts())
print(df['gz2_broad_parsed'].value_counts(normalize=True) * 100)

# Analyze threshold-based decision tree labels (Willett et al. 2013 rules)
# 1. Smooth vs Featured (t01)
# 2. Edge-on (t02)
# 3. Spiral (t04)
# 4. Bar (t03)
# 5. Odd (t06)

def classify_gz2_rules_strict(row, threshold=0.6):
    p_smooth = row['t01_smooth_or_features_a01_smooth_debiased']
    p_features = row['t01_smooth_or_features_a02_features_or_disk_debiased']
    p_edgeon = row['t02_edgeon_a04_yes_debiased']
    p_spiral = row['t04_spiral_a08_spiral_debiased']
    
    if p_smooth >= threshold:
        return 'SMOOTH'
    elif p_features >= threshold:
        if p_edgeon >= threshold:
            return 'EDGE_ON'
        elif p_spiral >= threshold:
            return 'SPIRAL'
        else:
            return 'FEATURED_DISK'
    else:
        return 'AMBIGUOUS'

def classify_gz2_rules_winner(row):
    p_smooth = row['t01_smooth_or_features_a01_smooth_debiased']
    p_features = row['t01_smooth_or_features_a02_features_or_disk_debiased']
    p_edgeon = row['t02_edgeon_a04_yes_debiased']
    p_spiral = row['t04_spiral_a08_spiral_debiased']
    
    if p_smooth > p_features:
        return 'SMOOTH'
    else:
        # It is features/disk
        if p_edgeon >= 0.5:
            return 'EDGE_ON'
        elif p_spiral >= 0.5:
            return 'SPIRAL'
        else:
            return 'FEATURED_DISK'

# Test strict rules across thresholds
print("\n--- Strategy 1: Strict Threshold-based 4-Class Classification ---")
for th in [0.5, 0.6, 0.7, 0.8]:
    col_name = f'target_strict_{int(th*100)}'
    df[col_name] = df.apply(lambda r: classify_gz2_rules_strict(r, threshold=th), axis=1)
    print(f"\nThreshold = {th}:")
    print(df[col_name].value_counts())
    print(f"Ambiguous count: {(df[col_name] == 'AMBIGUOUS').sum()} ({((df[col_name] == 'AMBIGUOUS').mean()*100):.1f}%)")

print("\n--- Strategy 2: Dominant / Winner-take-all 4-Class Classification ---")
df['target_winner_4class'] = df.apply(classify_gz2_rules_winner, axis=1)
print(df['target_winner_4class'].value_counts())
print(df['target_winner_4class'].value_counts(normalize=True) * 100)

print("\n--- Strategy 3: Dominant / Winner-take-all 3-Class Classification ---")
def classify_gz2_rules_3class(row):
    p_smooth = row['t01_smooth_or_features_a01_smooth_debiased']
    p_features = row['t01_smooth_or_features_a02_features_or_disk_debiased']
    p_edgeon = row['t02_edgeon_a04_yes_debiased']
    
    if p_smooth > p_features:
        return 'SMOOTH'
    elif p_edgeon >= 0.5:
        return 'EDGE_ON'
    else:
        return 'DISK_SPIRAL'

df['target_winner_3class'] = df.apply(classify_gz2_rules_3class, axis=1)
print(df['target_winner_3class'].value_counts())
print(df['target_winner_3class'].value_counts(normalize=True) * 100)

# Check splits distribution for target_winner_4class and target_strict_60
print("\n=== SPLIT DISTRIBUTION CHECK (target_winner_4class) ===")
print(pd.crosstab(df['split'], df['target_winner_4class'], margins=True))

print("\n=== SPLIT DISTRIBUTION CHECK (target_strict_60) ===")
print(pd.crosstab(df['split'], df['target_strict_60'], margins=True))
