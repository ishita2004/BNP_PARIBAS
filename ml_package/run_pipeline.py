# run_pipeline.py
import os
import pandas as pd
import json
import xml.etree.ElementTree as ET
from pymongo import MongoClient

# Optional: for OCR on image-based PDFs
from pdf2image import convert_from_path
import pytesseract

# -------------------------
# Helper: PDF extraction
# -------------------------
def pdf_to_dataframe(pdf_path):
    """
    Try to extract table from PDF using tabula/camelot,
    fallback to OCR if image-based PDF
    """
    try:
        import tabula
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        if tables:
            return pd.concat(tables, ignore_index=True)
    except:
        pass

    # OCR fallback
    images = convert_from_path(pdf_path)
    all_text = []
    for img in images:
        text = pytesseract.image_to_string(img)
        all_text.append(text)
    full_text = "\n".join(all_text)
    rows = [line.strip() for line in full_text.split("\n") if line.strip()]
    # Convert to DataFrame with generic columns
    max_cols = max(len(r.split()) for r in rows)
    data = [r.split() + [""]*(max_cols - len(r.split())) for r in rows]
    columns = [f"col{i+1}" for i in range(max_cols)]
    return pd.DataFrame(data, columns=columns)

# -------------------------
# Helper: extract single file
# -------------------------
def extract_file(file_path):
    ext = file_path.split('.')[-1].lower()
    if ext == "csv":
        return pd.read_csv(file_path)
    elif ext in ["xls", "xlsx"]:
        return pd.read_excel(file_path)
    elif ext == "json":
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.json_normalize(data)
    elif ext == "xml":
        tree = ET.parse(file_path)
        root = tree.getroot()
        data = [{child.tag: child.text for child in elem} for elem in root]
        return pd.DataFrame(data)
    elif ext == "pdf":
        return pdf_to_dataframe(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

# -------------------------
# Extract all files in folder
# -------------------------
def extract_all(folder_path="data"):
    file_df_map = {}
    files = os.listdir(folder_path)
    print("Files found:", files)
    for file in files:
        file_path = os.path.join(folder_path, file)
        try:
            df = extract_file(file_path)
            file_df_map[file] = df
            print(f"[EXTRACT] {file} -> shape: {df.shape}")
        except Exception as e:
            print(f"[ERROR] {file}: {e}")
    return file_df_map

# -------------------------
# Standardize & clean
# -------------------------
def standardize_columns(df):
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df

def clean_dataframe(df):
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].str.strip()
    # Fill numeric missing values with 0
    for col in df.select_dtypes(include=["int64","float64"]).columns:
        df[col] = df[col].fillna(0)
    return df.drop_duplicates()

def validate_dataframe(df):
    df = df.dropna(how="all")
    return df if not df.empty else None

# -------------------------
# MongoDB Setup
# -------------------------
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "ml_db"
COLLECTION_NAME = "processed_data"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# -------------------------
# Main Pipeline
# -------------------------
folder_path = "data"
file_df_map = extract_all(folder_path)

cleaned_dfs = {}
for fname, df in file_df_map.items():
    df = standardize_columns(df)
    df = clean_dataframe(df)
    df = validate_dataframe(df)
    if df is not None:
        cleaned_dfs[fname] = df
        print(f"[VALIDATED] {fname}: {df.shape}")
    else:
        print(f"[SKIP] {fname} - no valid data after cleaning")

# -------------------------
# Merge relationally by common keys
# -------------------------
merged_df = None
for fname, df in cleaned_dfs.items():
    if merged_df is None:
        merged_df = df
    else:
        common_cols = list(set(merged_df.columns) & set(df.columns))
        if common_cols:
            # Convert to str to avoid dtype conflicts
            for col in common_cols:
                merged_df[col] = merged_df[col].astype(str)
                df[col] = df[col].astype(str)
            merged_df = merged_df.merge(df, on=common_cols, how="left")
            print(f"[MERGE] {fname} merged on {common_cols} -> {merged_df.shape}")
        else:
            # No common columns, keep separately
            merged_df = pd.concat([merged_df, df], axis=1)
            print(f"[CONCAT] {fname} no common cols -> {merged_df.shape}")

# -------------------------
# Push to MongoDB
# -------------------------
if merged_df is not None and not merged_df.empty:
    records = merged_df.to_dict(orient="records")
    collection.delete_many({})  # optional: clear old data
    collection.insert_many(records)
    print(f"[INFO] Inserted {len(records)} records into MongoDB collection '{COLLECTION_NAME}'")
else:
    print("[INFO] No data to insert")
