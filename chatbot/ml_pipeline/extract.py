import pandas as pd
import pdfplumber
import os

def pdf_to_dataframe(pdf_path, output_folder="data"):
    """
    Extract text from a text-based PDF and convert it into a structured DataFrame.
    Save CSV and pickle inside output_folder.
    """
    all_text = []

    # Open PDF
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                all_text.append(text)
            print(f"[PDF] Page {page_num} processed for {os.path.basename(pdf_path)}.")

    # Combine all pages
    full_text = "\n".join(all_text)

    # Split lines and clean
    rows = [line.strip() for line in full_text.split("\n") if line.strip()]

    # Define column names (customize as per PDF layout)
    columns = [
        'transaction_id', 'customer_id', 'timestamp', 'transaction_type',
        'amount', 'fraud_flag', 'hour_of_day', 'day_of_week', 'is_weekend'
    ]

    # Parse rows
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

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Save to CSV and pickle inside data folder
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    csv_file = os.path.join(output_folder, f"{base_name}.csv")
    pickle_file = os.path.join(output_folder, f"{base_name}.pkl")

    df.to_csv(csv_file, index=False, encoding='utf-8')
    df.to_pickle(pickle_file)

    print(f"PDF converted to DataFrame and saved as CSV ({csv_file}) and pickle ({pickle_file}). Rows: {len(df)}")
    return df

# --- Run the function for your PDF ---
pdf_file = "customer_trade.pdf"
df_trade = pdf_to_dataframe(pdf_file, output_folder="data")
