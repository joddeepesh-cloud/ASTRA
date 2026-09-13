import pandas as pd
import numpy as np

df_merged = pd.read_csv("ml/data/raw/galaxy_zoo/merged_zoo_data.csv.gz")
df_splits = pd.read_csv("ml/data/splits/subset_10k_archive_compatible_splits.csv")
subset = df_splits.merge(df_merged, on="dr7objid", how="inner", suffixes=("", "_raw"))

print("=== ALL COLUMNS IN MERGED DATASET ===")
for i, col in enumerate(df_merged.columns):
    print(f"{i:3d}: {col}")

print("\n=== SAMPLE VOTE FRACTIONS SUMMARY (10k SUBSET) ===")
vote_cols = [c for c in subset.columns if any(c.startswith(prefix) for prefix in ['t01', 't02', 't03', 't04', 't05', 't06', 't07', 't08', 't09', 't10', 't11'])]
print(f"Total vote columns found: {len(vote_cols)}")

print("\nVote fraction columns:")
for c in vote_cols:
    print(f"  {c:<45} min={subset[c].min():.2f}, mean={subset[c].mean():.2f}, max={subset[c].max():.2f}")
