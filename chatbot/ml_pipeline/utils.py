# ml_pipeline/utils.py
import pandas as pd
import json

def save_to_json(df, path):
    df.to_json(path, orient="records", date_format="iso")

def save_to_csv(df, path):
    df.to_csv(path, index=False)

def load_json(path):
    with open(path, 'r') as f:
        return pd.json_normalize(json.load(f))
