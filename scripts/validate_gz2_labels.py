import pandas as pd
import numpy as np

# Load merged data and splits
df_merged = pd.read_csv("ml/data/raw/galaxy_zoo/merged_zoo_data.csv.gz")
df_splits = pd.read_csv("ml/data/splits/subset_10k_archive_compatible_splits.csv")
df = df_splits.merge(df_merged, on="dr7objid", how="inner", suffixes=("", "_raw"))

print("=== 1. DATASET INTEGRITY & LEAKAGE CHECK ===")
print(f"Total rows in 10k splits: {len(df_splits)}")
print(f"Unique image_filename in splits: {df_splits['image_filename'].nunique()}")
print(f"Unique asset_id in splits: {df_splits['asset_id'].nunique()}")
print(f"Unique dr7objid in splits: {df_splits['dr7objid'].nunique()}")

train_ids = set(df_splits[df_splits['split'] == 'train']['dr7objid'])
val_ids = set(df_splits[df_splits['split'] == 'val']['dr7objid'])
test_ids = set(df_splits[df_splits['split'] == 'test']['dr7objid'])

overlap_tv = train_ids.intersection(val_ids)
overlap_tt = train_ids.intersection(test_ids)
overlap_vt = val_ids.intersection(test_ids)

print(f"Train vs Val overlap: {len(overlap_tv)}")
print(f"Train vs Test overlap: {len(overlap_tt)}")
print(f"Val vs Test overlap: {len(overlap_vt)}")

print("\n=== 2. DECISION TREE VOTE CONFIDENCE DISTRIBUTION ===")
# Check distribution of vote fraction confidence
df['max_t01_prob'] = df[['t01_smooth_or_features_a01_smooth_debiased', 't01_smooth_or_features_a02_features_or_disk_debiased']].max(axis=1)

print("T01 (Smooth vs Features) Max Probability Percentiles:")
print(df['max_t01_prob'].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]))

high_conf_80 = (df['max_t01_prob'] >= 0.8).sum()
high_conf_60 = (df['max_t01_prob'] >= 0.6).sum()
low_conf = (df['max_t01_prob'] < 0.6).sum()

print(f"\nHigh confidence (>=0.8): {high_conf_80} ({high_conf_80/10000*100:.1f}%)")
print(f"Moderate confidence (0.6 - 0.8): {high_conf_60 - high_conf_80} ({(high_conf_60 - high_conf_80)/10000*100:.1f}%)")
print(f"Low confidence (<0.6): {low_conf} ({low_conf/10000*100:.1f}%)")

print("\n=== 3. ANOMALY / OOD CANDIDATE ANALYSIS ===")
# Odd feature (t06_odd) vote fractions
odd_cols = [c for c in df.columns if c.startswith('t08_odd_feature_') and c.endswith('_debiased')]
df['max_odd_prob'] = df['t06_odd_a14_yes_debiased']

print("t06_odd_a14_yes_debiased summary:")
print(df['max_odd_prob'].describe(percentiles=[0.5, 0.75, 0.9, 0.95, 0.99]))

odd_candidates = df[df['max_odd_prob'] >= 0.5]
print(f"\nGalaxies with high 'odd' feature probability (>=0.5): {len(odd_candidates)}")
print("Odd sub-types breakdown among these odd candidates:")
for oc in odd_cols:
    short_name = oc.replace('t08_odd_feature_', '').replace('_debiased', '')
    count = (odd_candidates[oc] >= 0.2).sum()
    print(f"  {short_name:<35}: {count} galaxies")

print("\n=== 4. GALAXY ZOO 2 DECISION TREE FIELD MAPPING VALIDATION ===")
# Build 4-class target with confidence flags
def assign_target(row):
    p_smooth = row['t01_smooth_or_features_a01_smooth_debiased']
    p_features = row['t01_smooth_or_features_a02_features_or_disk_debiased']
    p_edgeon = row['t02_edgeon_a04_yes_debiased']
    p_spiral = row['t04_spiral_a08_spiral_debiased']
    
    # Calculate confidence margin
    margin = abs(p_smooth - p_features)
    
    if p_smooth > p_features:
        label = 'SMOOTH'
        conf = p_smooth
    else:
        if p_edgeon >= 0.5:
            label = 'EDGE_ON'
            conf = p_edgeon
        elif p_spiral >= 0.5:
            label = 'SPIRAL'
            conf = p_spiral
        else:
            label = 'FEATURED_DISK'
            conf = p_features
            
    return pd.Series([label, conf, margin], index=['target_class', 'target_confidence', 't01_margin'])

target_df = df.apply(assign_target, axis=1)
df['target_class'] = target_df['target_class']
df['target_confidence'] = target_df['target_confidence']
df['t01_margin'] = target_df['t01_margin']

print("\nFinal Proposed 4-Class Morphology Target Breakdown:")
print(df['target_class'].value_counts())

print("\nMean Confidence by Class:")
print(df.groupby('target_class')['target_confidence'].mean())

print("\nMean T01 Margin by Class:")
print(df.groupby('target_class')['t01_margin'].mean())
