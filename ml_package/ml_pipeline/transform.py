import pandas as pd

# -------------------------
# Column standardization
# -------------------------
def standardize_columns(df):
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    return df

def clean_dataframe(df):
    df = df.drop_duplicates().reset_index(drop=True)

    # Clean string columns
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.strip().replace('', None)

    # Fill numeric columns
    for col in df.select_dtypes(include='number').columns:
        df[col] = df[col].fillna(0)
    
    return df

# -------------------------
# Standardize key column types
# -------------------------
def standardize_key_types(df, key_cols):
    for col in key_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

# -------------------------
# Merge multiple DataFrames
# -------------------------
def merge_dataframes(dfs, keys_map):
    merged = None
    dfs_copy = dfs.copy()

    # Merge on specified keys
    for (df1_name, df2_name), key in keys_map.items():
        df1 = dfs_copy.pop(df1_name) if df1_name in dfs_copy else merged
        df2 = dfs_copy.pop(df2_name)

        # Ensure key dtype consistency
        df1[key] = df1[key].astype(str).str.strip()
        df2[key] = df2[key].astype(str).str.strip()

        merged = df1.merge(df2, on=key, how='left')
        print(f"[MERGE] {df1_name} + {df2_name} on '{key}' -> shape: {merged.shape}")

    # Best-effort merges on remaining common columns
    for name, df in dfs_copy.items():
        common_cols = set(merged.columns) & set(df.columns)
        if common_cols:
            for col in common_cols:
                merged[col] = merged[col].astype(str).str.strip()
                df[col] = df[col].astype(str).str.strip()
            merged = merged.merge(df, on=list(common_cols), how='left')
            print(f"[MERGE-BEST] {name} merged on {common_cols} -> shape: {merged.shape}")
        else:
            print(f"[MERGE-SKIP] {name} has no common columns")

    return merged
