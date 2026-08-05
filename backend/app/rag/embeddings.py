"""Local embedding model (sentence-transformers), loaded once as a singleton.

Local instead of an API (OpenAI/Voyage) since Anthropic has no embeddings
endpoint anyway — this keeps it to one paid dependency, no extra key, works
offline once cached. It does lag the hosted models on retrieval benchmarks;
swapping it out later is contained to this file since callers only see
`embed_texts` / `embed_query`.
"""
import threading

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import get_settings

_model: SentenceTransformer | None = None
_lock = threading.Lock()


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                _model = SentenceTransformer(get_settings().embedding_model)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 384), dtype=np.float32)
    return get_model().encode(texts, normalize_embeddings=True, show_progress_bar=False)


def embed_query(text: str) -> list[float]:
    vec = get_model().encode([text], normalize_embeddings=True, show_progress_bar=False)[0]
    return vec.tolist()
