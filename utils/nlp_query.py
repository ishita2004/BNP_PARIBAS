# utils/nlp_query.py
from google import genai
import pandas as pd

class GeminiQuery:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def query(self, user_input: str, df: pd.DataFrame):
        """
        Send user query + dataset schema to Gemini.
        Returns filtered DataFrame (if any) and raw model response.
        """
        # Prepare prompt
        prompt = f"""
        You are given a dataset with columns: {', '.join(df.columns.tolist())}.
        The user asks: "{user_input}".
        If possible, return a list of row indices (0-based) as Python list 
        that matches the query, else return '[]'.
        """

        # Send to Gemini
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        # Try to extract indices
        try:
            indices = eval(response.text) if response.text.startswith("[") else []
            filtered_df = df.iloc[indices] if indices else pd.DataFrame()
        except:
            filtered_df = pd.DataFrame()

        return filtered_df, response.text
