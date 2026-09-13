import pandas as pd
import numpy as np

# Load merged raw data and official splits
df_merged = pd.read_csv("ml/data/raw/galaxy_zoo/merged_zoo_data.csv.gz")
df_splits = pd.read_csv("ml/data/splits/subset_10k_archive_compatible_splits.csv")

# Merge
df = df_splits.merge(df_merged, on="dr7objid", how="inner", suffixes=("", "_raw"))

# Build 4-class and 3-class scientific targets
def derive_targets(row):
    p_smooth = row['t01_smooth_or_features_a01_smooth_debiased']
    p_features = row['t01_smooth_or_features_a02_features_or_disk_debiased']
    p_edgeon = row['t02_edgeon_a04_yes_debiased']
    p_spiral = row['t04_spiral_a08_spiral_debiased']
    p_bar = row['t03_bar_a06_bar_debiased']
    p_odd = row['t06_odd_a14_yes_debiased']
    
    # 4-class decision tree taxonomy
    if p_smooth > p_features:
        class_4 = 'SMOOTH'
    else:
        if p_edgeon >= 0.5:
            class_4 = 'EDGE_ON'
        elif p_spiral >= 0.5:
            class_4 = 'SPIRAL'
        else:
            class_4 = 'FEATURED_DISK'
            
    # 3-class taxonomy
    if p_smooth > p_features:
        class_3 = 'SMOOTH'
    elif p_edgeon >= 0.5:
        class_3 = 'EDGE_ON'
    else:
        class_3 = 'DISK_SPIRAL'
        
    margin = abs(p_smooth - p_features)
    is_high_conf = (max(p_smooth, p_features) >= 0.6)
    is_odd_anomaly = (p_odd >= 0.5)
    
    return pd.Series([
        class_4, class_3, p_smooth, p_features, p_edgeon, p_spiral, p_bar, p_odd,
        margin, is_high_conf, is_odd_anomaly
    ], index=[
        'target_4class', 'target_3class', 'prob_smooth', 'prob_features', 'prob_edgeon',
        'prob_spiral', 'prob_bar', 'prob_odd', 't01_margin', 'is_high_confidence', 'is_odd_anomaly'
    ])

targets = df.apply(derive_targets, axis=1)

# Combine with split metadata
output_df = pd.concat([
    df_splits[['dr7objid', 'asset_id', 'image_filename', 'ra', 'dec', 'split']],
    targets
], axis=1)

# Save to NEW CSV (never overwrite original splits file)
target_path = "ml/data/splits/subset_10k_scientific_targets.csv"
output_df.to_csv(target_path, index=False)

print(f"Successfully generated scientific targets CSV at {target_path}")
print(f"Shape: {output_df.shape}")
print("\nTarget 4-Class Counts:")
print(output_df['target_4class'].value_counts())
print("\nTarget 4-Class Breakdown by Split:")
print(pd.crosstab(output_df['split'], output_df['target_4class']))
