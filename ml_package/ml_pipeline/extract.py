import pdfplumber
import pandas as pd
import os
import json
import xml.etree.ElementTree as ET

# -------------------------
# Text-based PDF extraction
# -------------------------
def pdf_to_dataframe(pdf_path):
    """
    Extract text from a text-based PDF and convert to structured DataFrame.
    Customize parsing depending on your PDF layout.
    """
    all_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                all_text.append(text)
            print(f"[PDF] Page {page_num} processed for {os.path.basename(pdf_path)}.")

    full_text = "\n".join(all_text)

    # Split lines and clean
    rows = [line.strip() for line in full_text.split("\n") if line.strip()]

    # Customize column names based on your PDF structure
    columns = [
        'transaction_id','customer_id','timestamp','transaction_type',
        'amount','fraud_flag','hour_of_day','day_of_week','is_weekend'
    ]

    records = []
    for line in rows:
        parts = line.split()
        if len(parts) >= len(columns):
            records.append(parts[:len(columns)])

    return pd.DataFrame(records, columns=columns)

# -------------------------
# Single file extraction
# -------------------------
def extract_file(file_path):
    ext = file_path.split('.')[-1].lower()

    if ext == 'csv':
        return pd.read_csv(file_path)
    elif ext in ['xls','xlsx']:
        return pd.read_excel(file_path)
    elif ext == 'json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.json_normalize(data)
    elif ext == 'xml':
        tree = ET.parse(file_path)
        root = tree.getroot()
        data = [{child.tag: child.text for child in elem} for elem in root]
        return pd.DataFrame(data)
    elif ext == 'pdf':
        try:
            import tabula
            tables = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
            if tables:
                return pd.concat(tables, ignore_index=True)
        except:
            pass
        # Use text-based extraction
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
            print(f"[EXTRACT] {file} processed successfully. Shape: {df.shape}")
            print(df.head(5))
        except Exception as e:
            print(f"[EXTRACT ERROR] {file}: {e}")
    return file_df_map
