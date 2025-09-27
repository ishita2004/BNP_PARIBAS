import os
import pandas as pd
import camelot
import tabula
from app.config import collection
from app.utils import log_error

def extract_file(file_path):
    """
    Extracts a file into a DataFrame.
    Supports CSV, Excel, JSON, XML, PDF (tables).
    """
    ext = file_path.split(".")[-1].lower()
    try:
        if ext == "csv":
            df = pd.read_csv(file_path)
        elif ext in ["xls", "xlsx"]:
            df = pd.read_excel(file_path)
        elif ext == "json":
            df = pd.read_json(file_path)
        elif ext == "xml":
            df = pd.read_xml(file_path)
        elif ext == "pdf":
            # Try Tabula first
            tables = tabula.read_pdf(file_path, pages="all", multiple_tables=True)
            if tables:
                df = pd.concat(tables, ignore_index=True)
            else:
                # fallback to Camelot
                tables = camelot.read_pdf(file_path, pages="all")
                df = pd.concat([t.df for t in tables], ignore_index=True)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        return df
    except Exception as e:
        log_error(f"Failed to extract {file_path}: {str(e)}")
        return None

def clean_and_validate(df):
    """
    Clean & validate dataframe:
    - drop duplicates
    - drop empty rows
    - fill missing numeric values with 0
    """
    if df is None or df.empty:
        return None
    df = df.drop_duplicates()
    df = df.dropna(how='all')
    for col in df.select_dtypes(include='number').columns:
        df[col] = df[col].fillna(0)
    return df if not df.empty else None

def process_and_store(file_paths: list):
    """
    Process uploaded files and store validated data into MongoDB
    """
    all_dfs = []
    for file_path in file_paths:
        df = extract_file(file_path)
        df = clean_and_validate(df)
        if df is not None:
            df["source_file"] = os.path.basename(file_path)
            all_dfs.append(df)
    
    if not all_dfs:
        return {"error": "No valid data to process."}
    
    # Optional: Cross join all files to preserve all combinations
    merged_df = all_dfs[0]
    for df in all_dfs[1:]:
        merged_df = merged_df.merge(df, how="cross")

    # Push to MongoDB
    records = merged_df.to_dict(orient="records")
    if records:
        collection.delete_many({})  # clear old data
        collection.insert_many(records)
    return {"message": f"Processed {len(records)} records from {len(all_dfs)} files"}
