import pandas as pd

# --- Step 1: Load the Excel file into a DataFrame ---
excel_file = "Customer_UPI_transactions.xlsx"
df = pd.read_excel(excel_file, sheet_name=0)

# --- Step 2: Convert datetime columns to string (optional, if needed) ---
for col in df.select_dtypes(include=['datetime64[ns]']).columns:
    df[col] = df[col].astype(str)

# --- Step 3: Save DataFrame to a file ---

# Option 1: Save as CSV
df.to_csv("UPi_dataframe.csv", index=False, encoding='utf-8')

# Option 2: Save as a pickle file (preserves dtypes and DataFrame structure)
df.to_pickle("UPi_dataframe.pkl")

print(f"Excel file converted to DataFrame and saved as CSV and pickle. Rows: {len(df)}")
