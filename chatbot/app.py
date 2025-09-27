# app.py
import streamlit as st
import pandas as pd
import os
import tempfile
import json
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from pdf2image import convert_from_path
import pytesseract
from google.genai import Client

# -------------------------
# Streamlit Title
# -------------------------
st.set_page_config(layout="wide")
st.title("Multi-File ETL + MongoDB + Dynamic NLP Chatbot")

# -------------------------
# Gemini API Setup
# -------------------------
try:
    client_gemini = Client()  # Ensure GEMINI_API_KEY is set in environment
    st.success("Gemini client initialized.")
except Exception as e:
    st.error(f"Failed to initialize Gemini client: {e}")
    client_gemini = None

def generate_response(prompt: str) -> str:
    if not client_gemini:
        return "Gemini client not initialized."
    try:
        response = client_gemini.chat(
            model="chat-bison-001",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_output_tokens=500
        )
        # Handle different response structures
        if hasattr(response, "last") and response.last:
            return response.last
        elif hasattr(response, "content"):
            return response.content
        else:
            return str(response)
    except Exception as e:
        return f"Error generating response: {e}"

# -------------------------
# MongoDB Setup
# -------------------------
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "ml_db"
COLLECTION_NAME = "processed_data"

try:
    client_mongo = MongoClient(MONGO_URI)
    db = client_mongo[DB_NAME]
    collection = db[COLLECTION_NAME]
    st.success("Connected to MongoDB.")
except Exception as e:
    st.error(f"MongoDB connection failed: {e}")
    collection = None

def get_database_text():
    if not collection:
        return "No database connection."
    records = list(collection.find())
    if not records:
        return "No data in database."
    df = pd.DataFrame(records)
    return df.to_csv(index=False)

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
    """Extract data from PDF (table or OCR fallback)."""
    try:
        import tabula
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        if tables:
            return pd.concat(tables, ignore_index=True)
    except:
        pass
    try:
        images = convert_from_path(pdf_path)
        all_text = [pytesseract.image_to_string(img) for img in images]
        full_text = "\n".join(all_text)
        rows = [line.strip() for line in full_text.split("\n") if line.strip()]
        if not rows:
            return pd.DataFrame()
        max_cols = max(len(r.split()) for r in rows)
        data = [r.split() + [""]*(max_cols - len(r.split())) for r in rows]
        columns = [f"col{i+1}" for i in range(max_cols)]
        return pd.DataFrame(data, columns=columns)
    except Exception as e:
        st.error(f"OCR PDF extraction failed: {e}")
        return pd.DataFrame()

def extract_file(file):
    ext = file.name.split('.')[-1].lower()
    try:
        if ext == "csv":
            return pd.read_csv(file, encoding='utf-8', errors='ignore')
        elif ext in ["xls", "xlsx"]:
            if ext == "xlsx":
                return pd.read_excel(file, engine="openpyxl")
            else:
                return pd.read_excel(file, engine="xlrd")
        elif ext == "json":
            data = json.load(file)
            return pd.json_normalize(data)
        elif ext == "xml":
            tree = ET.parse(file)
            root = tree.getroot()
            data = [{child.tag: child.text for child in elem} for elem in root]
            return pd.DataFrame(data)
        elif ext == "pdf":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file.read())
                tmp_path = tmp.name
            df = pdf_to_dataframe(tmp_path)
            os.remove(tmp_path)
            return df
        else:
            st.warning(f"Unsupported file type: {file.name}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error reading {file.name}: {e}")
        return pd.DataFrame()

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
# Process Uploaded Files
# -------------------------
if uploaded_files:
    st.info(f"Processing {len(uploaded_files)} file(s)...")
    file_df_map = {}
    progress_bar = st.progress(0)
    for i, file in enumerate(uploaded_files):
        df = extract_file(file)
        if df.empty:
            st.warning(f"Skipped {file.name} - no data extracted")
        else:
            file_df_map[file.name] = df
            st.success(f"Extracted: {file.name} -> shape: {df.shape}")
        progress_bar.progress((i+1)/len(uploaded_files))
    
    # Clean and validate
    cleaned_dfs = {}
    for fname, df in file_df_map.items():
        df = standardize_columns(df)
        df = clean_dataframe(df)
        df = validate_dataframe(df)
        if df is not None:
            cleaned_dfs[fname] = df
            st.success(f"Validated: {fname} -> {df.shape}")
        else:
            st.warning(f"Skipped {fname} - no valid data after cleaning")

    # Merge relationally
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
        try:
            records = merged_df.to_dict(orient="records")
            collection.delete_many({})  # optional
            collection.insert_many(records)
            st.success(f"Inserted {len(records)} records into MongoDB collection '{COLLECTION_NAME}'")
        except Exception as e:
            st.error(f"Failed to insert into MongoDB: {e}")
        
        st.subheader("Preview Merged Data")
        selected_file = st.selectbox("Select file to preview", options=list(cleaned_dfs.keys()))
        st.dataframe(cleaned_dfs[selected_file].head())

        # Download button for merged data
        csv_data = merged_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Merged Data as CSV",
            data=csv_data,
            file_name="merged_data.csv",
            mime="text/csv"
        )

        # -------------------------
        # Chatbot Section
        # -------------------------
        st.subheader("Ask Questions About Your Data")
        user_query = st.text_input("Enter your question:")
        if user_query:
            db_text = get_database_text()
            prompt = f"Here is the database:\n{db_text}\n\nAnswer the following question based on this data:\n{user_query}"
            answer = generate_response(prompt)
            st.markdown(f"**Answer:** {answer}")
    else:
        st.warning("No valid data to insert; chatbot not enabled")
