# main_nlp.py
from fastapi import FastAPI
from pydantic import BaseModel
from nlp_loader import df, text_columns
from nlp_embed import model, doc_embeddings, docs_text
from nlp_query import query_docs
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

app = FastAPI(title="NLP Dynamic Query API")

class Query(BaseModel):
    question: str

@app.post("/chat")
def chat(query: Query):
    # Get top 3 semantic matches
    top_docs = query_docs(query.question, top_k=3)
    
    # Example KPI: count of records, sum of 'Value' if exists
    kpi = {}
    if 'Value' in df.columns:
        kpi['total_value'] = df['Value'].sum()
        kpi['average_value'] = df['Value'].mean()
    
    # Example: simple bar graph (Value per Year)
    fig, ax = plt.subplots()
    if 'Year' in df.columns and 'Value' in df.columns:
        df.groupby('Year')['Value'].sum().plot(kind='bar', ax=ax)
        ax.set_title("Value per Year")
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    else:
        img_base64 = None
    
    return {
        "top_docs": top_docs,
        "kpi": kpi,
        "graph_base64": img_base64
    }
