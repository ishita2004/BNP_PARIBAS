import pandas as pd
import pdfplumber
import os

# --- PDF file path ---
pdf_file = "customer_trade.pdf"
output_folder = "data"

# --- Ensure output folder exists ---
os.makedirs(output_folder, exist_ok=True)

# --- Function to extract PDF to DataFrame ---
def pdf_to_dataframe(pdf_path):
    all_text = []

    # Open PDF and extract text
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                all_text.append(text)
            print(f"[PDF] Page {page_num} processed for {os.path.basename(pdf_path)}.")

    full_text = "\n".join(all_text)
    rows = [line.strip() for line in full_text.split("\n") if line.strip()]

    # Customize columns based on your PDF layout
    columns = [
        'transaction_id', 'customer_id', 'timestamp', 'transaction_type',
        'amount', 'fraud_flag', 'hour_of_day', 'day_of_week', 'is_weekend'
    ]

    records = []
    for line in rows:
        parts = line.split()
        if len(parts) >= len(columns):
            records.append(parts[:len(columns)])

    df = pd.DataFrame(records, columns=columns)

    # Convert numeric columns
    numeric_cols = ['amount', 'fraud_flag', 'hour_of_day', 'is_weekend']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert timestamp column to datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    return df

# --- Extract PDF to DataFrame ---
df_trade = pdf_to_dataframe(pdf_file)

# --- Save to CSV and pickle like Excel file ---
base_name = os.path.splitext(os.path.basename(pdf_file))[0]
csv_file = os.path.join(output_folder, f"{base_name}.csv")
pickle_file = os.path.join(output_folder, f"{base_name}.pkl")

df_trade.to_csv(csv_file, index=False, encoding='utf-8')
df_trade.to_pickle(pickle_file)

print(f"PDF file converted to DataFrame and saved as CSV ({csv_file}) and pickle ({pickle_file}). Rows: {len(df_trade)}")
