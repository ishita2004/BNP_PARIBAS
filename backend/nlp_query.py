# nlp_query.py
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from nlp_embed import model, doc_embeddings, docs_text

def query_docs(user_query, top_k=3):
    query_vec = model.encode([user_query], convert_to_numpy=True, normalize_embeddings=True)
    similarities = cosine_similarity(query_vec, doc_embeddings)[0]
    top_idx = np.argsort(similarities)[-top_k:][::-1]
    top_docs = [docs_text[i] for i in top_idx]
    return top_docs
