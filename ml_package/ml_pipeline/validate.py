# ml_pipeline/validate.py
import pandas as pd

def validate_dataframe(df):
    """
    Returns summary metrics for DataFrame
    """
    metrics = {}
    metrics['rows'] = df.shape[0]
    metrics['columns'] = df.shape[1]
    metrics['missing_percent'] = df.isnull().mean() * 100
    metrics['duplicate_rows'] = df.duplicated().sum()
    
    return metrics

def log_invalid_rows(df, log_file="logs/invalid_rows.csv"):
    invalid_rows = df[df.isnull().any(axis=1)]
    if not invalid_rows.empty:
        invalid_rows.to_csv(log_file, index=False)
