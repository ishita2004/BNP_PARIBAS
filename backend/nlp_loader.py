# nlp_loader.py
import json
import pandas as pd

EXPORT_FILE = "exported_data.json"

# Load JSON
with open(EXPORT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert to DataFrame for analytics and graphs
df = pd.DataFrame(data)

# Optional: preprocessing for NLP
text_columns = df.select_dtypes(include='object').columns.tolist()
df.fillna("", inplace=True)  # Replace None/NaN
