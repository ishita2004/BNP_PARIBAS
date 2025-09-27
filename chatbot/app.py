# app.py
import streamlit as st
import pandas as pd
import os
import tempfile
from pymongo import MongoClient
import json
import xml.etree.ElementTree as ET
from pdf2image import convert_from_path
import pytesseract

st.title("Multi-File ETL & MongoDB Pipeline")

# -------------------------
# File Upload
# -------------------------
uploaded_files = st.file_uploader(
    "Upload your files (CSV, Excel, JSON, XML, PDF)",
    type=['csv', 'xls', 'xlsx', 'json', 'xml', 'pdf'],
    accept_multiple_files=True
)

# -------------------------
# Helper Functions
# -------------------------
def pdf_to_dataframe(pdf_path):
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
    max_cols = max(len(r.split()) for r in rows)
    data = [r.split() + [""]*(max_cols - len(r.split())) for r in rows]
    columns = [f"col{i+1}" for i in range(max_cols)]
    return pd.DataFrame(data, columns=columns)

def extract_file(file):
    ext = file.name.split('.')[-1].lower()
    if ext == "csv":
        return pd.read_csv(file)
    elif ext in ["xls", "xlsx"]:
        return pd.read_excel(file)
    elif ext == "json":
        data = json.load(file)
        return pd.json_normalize(data)
    elif ext == "xml":
        tree = ET.parse(file)
        root = tree.getroot()
        data = [{child.tag: child.text for child in elem} for elem in root]
        return pd.DataFrame(data)
    elif ext == "pdf":
        # Save temp file for pdf processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        df = pdf_to_dataframe(tmp_path)
        os.remove(tmp_path)
        return df
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def standardize_columns(df):
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df

def clean_dataframe(df):
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].str.strip()
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
# Process Files
# -------------------------
if uploaded_files:
    st.info(f"Processing {len(uploaded_files)} file(s)...")
    file_df_map = {}
    for file in uploaded_files:
        try:
            df = extract_file(file)
            file_df_map[file.name] = df
            st.success(f"Extracted: {file.name} -> shape: {df.shape}")
        except Exception as e:
            st.error(f"Failed to process {file.name}: {e}")

    cleaned_dfs = {}
    for fname, df in file_df_map.items():
        df = standardize_columns(df)
        df = clean_dataframe(df)
        df = validate_dataframe(df)
        if df is not None:
            cleaned_dfs[fname] = df
            st.success(f"Validated: {fname} -> {df.shape}")
        else:
            st.warning(f"Skipped {fname} - no valid data")

    # Merge relationally by common keys
    merged_df = None
    for fname, df in cleaned_dfs.items():
        if merged_df is None:
            merged_df = df
        else:
            common_cols = list(set(merged_df.columns) & set(df.columns))
            if common_cols:
                for col in common_cols:
                    merged_df[col] = merged_df[col].astype(str)
                    df[col] = df[col].astype(str)
                merged_df = merged_df.merge(df, on=common_cols, how="left")
                st.info(f"Merged {fname} on {common_cols} -> {merged_df.shape}")
            else:
                merged_df = pd.concat([merged_df, df], axis=1)
                st.info(f"Concatenated {fname} (no common cols) -> {merged_df.shape}")

    # Push to MongoDB
    if merged_df is not None and not merged_df.empty:
        records = merged_df.to_dict(orient="records")
        collection.delete_many({})  # optional: clear old data
        collection.insert_many(records)
        st.success(f"Inserted {len(records)} records into MongoDB collection '{COLLECTION_NAME}'")
        st.dataframe(merged_df.head())
    else:
        st.warning("No data to insert")
