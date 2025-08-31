import os
import threading
from typing import List, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer

# Minimalni prag sličnosti rezultata
EMB_MIN_SCORE = float(os.getenv("EMB_MIN_SCORE", "0.50"))

# Globalni resursi
_model_lock = threading.Lock()
_model = None

_documents: List[Dict[str, Any]] = []
_embeddings: np.ndarray = np.zeros((0, 384), dtype=np.float32)

# Thread-sigurnost za index strukture
_index_lock = threading.Lock()

def get_model():
    global _model
    with _model_lock:
        if _model is None:
            _model = SentenceTransformer("all-MiniLM-L6-v2") 
        return _model

def _norm(s: str) -> str:
    if not s:
        return ""
    return " ".join(s.split()).casefold()

def clear_index():
    global _documents, _embeddings
    with _index_lock:
        _documents = []
        _embeddings = np.zeros((0, 384), dtype=np.float32)

def add_doc_to_index(doc_id: int, title: str, content: str, category: str):
    global _documents, _embeddings
    text_for_embedding = _norm(f"{title}. {content}")
    model = get_model()
    emb = model.encode(
        [text_for_embedding],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype(np.float32)  # (1, D)
    with _index_lock:
        _embeddings = emb if _embeddings.size == 0 else np.vstack([_embeddings, emb])
        _documents.append({
            "id": doc_id,
            "title": title,
            "content": content,
            "category": category
        })

def search_index(query: str, top_k: int = 5):
    global _documents, _embeddings
    if len(_documents) == 0:
        return []

    q_norm = _norm(query)
    model = get_model()
    qv = model.encode(
        [q_norm],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype(np.float32)  # (1, D)

    with _index_lock:
        scores = np.dot(_embeddings, qv.T).flatten()
        top_idx = np.argsort(-scores)[:top_k]

        results = []
        for idx in top_idx:
            if idx < len(_documents):
                score = float(scores[idx])
                if score >= EMB_MIN_SCORE:
                    d = _documents[idx]
                    results.append({
                        "id": d["id"],
                        "title": d["title"],
                        "content": d["content"],
                        "category": d["category"],
                        "score": score
                    })
        return results
