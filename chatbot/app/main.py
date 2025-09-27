from fastapi import FastAPI, UploadFile, File
from typing import List
import pandas as pd

from app.etl_pipeline import process_and_store
from app.config import collection
from app.nlp_parser import parse_query_with_llm
from app.dynamic_query import run_dynamic_query
from app.utils import df_to_bar_chart

app = FastAPI(title="Customer Data NLP Chatbot")

# Upload & Process Endpoint
@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    file_paths = []
    for f in files:
        path = f"data/{f.filename}"
        with open(path, "wb") as file_object:
            file_object.write(await f.read())
        file_paths.append(path)
    result = process_and_store(file_paths)
    return result

# NLP Query Endpoint
@app.post("/ask")
async def ask_query(query: str):
    df = pd.DataFrame(list(collection.find({})))
    if df.empty:
        return {"error": "No data in MongoDB"}

    columns = [col for col in df.columns if col != "_id"]

    parsed_query = parse_query_with_llm(query, columns)
    if "error" in parsed_query:
        return parsed_query

    result = run_dynamic_query(df, parsed_query)

    graph = None
    if isinstance(result, list) and parsed_query.get("group_by") and parsed_query.get("column"):
        result_df = pd.DataFrame(result)
        if parsed_query["column"] in result_df.columns:
            graph = df_to_bar_chart(result_df, parsed_query["group_by"], parsed_query["column"])

    return {
        "query": query,
        "parsed_query": parsed_query,
        "result": result,
        "graph_base64": graph
    }
