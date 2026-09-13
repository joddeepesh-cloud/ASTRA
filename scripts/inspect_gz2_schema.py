import pandas as pd
import numpy as np

# Load merged data and 10k subset splits
print("Loading data...")
df_merged = pd.read_csv("ml/data/raw/galaxy_zoo/merged_zoo_data.csv.gz")
df_splits = pd.read_csv("ml/data/splits/subset_10k_archive_compatible_splits.csv")

print(f"Merged shape: {df_merged.shape}")
print(f"Splits shape: {df_splits.shape}")

print("\n--- All Columns in merged_zoo_data ---")
print(list(df_merged.columns))

# Join 10k subset with full merged metadata
subset_full = df_splits.merge(df_merged, on="dr7objid", how="inner", suffixes=("", "_raw"))
print(f"\nJoined 10k subset shape: {subset_full.shape}")

# Inspect vote fraction columns
t_cols = [c for c in subset_full.columns if c.startswith("t")]
print(f"\n--- Decision Tree Columns ({len(t_cols)}) ---")
print(t_cols)

# Check gz2class distribution in 10k subset
print("\n--- Top gz2class values in 10k subset ---")
print(subset_full["gz2class"].value_counts().head(20))

# Check missing values in t_cols
missing_t = subset_full[t_cols].isnull().sum()
print("\n--- Missing values in decision tree columns ---")
print(missing_t[missing_t > 0])
