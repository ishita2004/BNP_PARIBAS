# nlp_embed.py
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
import json

EXPORT_FILE = "exported_data.json"
with open(EXPORT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)
text_columns = df.select_dtypes(include='object').columns.tolist()

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_texts(text_list):
    return model.encode(text_list, convert_to_numpy=True, normalize_embeddings=True)

# Fix: convert None to str safely
docs_text = df[text_columns].apply(
    lambda row: " ".join([str(x) for x in row if x is not None]),
    axis=1
).tolist()

doc_embeddings = embed_texts(docs_text)
