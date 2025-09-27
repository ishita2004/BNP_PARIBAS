import os
import json
from google.generativeai import client as genai_client

# Initialize Gemini
genai_client.configure(api_key=os.getenv("GEN_API_KEY"))

def parse_query_with_llm(query: str, columns: list):
    """
    Converts natural language query into structured JSON for dynamic query.
    """
    prompt = f"""
    You are a data assistant. Dataset has columns: {columns}.
    Convert this query into JSON:
    - aggregation: sum, mean, count, max, min, or None
    - column: column to aggregate (or None)
    - filters: dictionary of filters
    - group_by: column to group by (or None)

    Query: "{query}"
    Respond ONLY in valid JSON.
    """
    try:
        response = genai_client.chat.create(
            model="gemini-1.5-t",
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.candidates[0].content)
    except Exception as e:
        return {"error": f"Failed to parse query with Gemini: {str(e)}"}
