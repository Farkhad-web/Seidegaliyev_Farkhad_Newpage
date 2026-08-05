"""Local embedding model (sentence-transformers), loaded once as a singleton.

Why a local model instead of an embeddings API (OpenAI / Voyage):
  - Zero extra API key / cost — the only paid dependency is Anthropic, for
    generation.
  - Deterministic and works fully offline once the model is cached in the
    Docker image, which matters for a self-contained take-home deliverable.
  - "all-MiniLM-L6-v2" is a well-known, cheap (384-dim, ~80MB) baseline good
    enough to demonstrate the retrieval architecture end-to-end.
Trade-off, stated plainly: it lags OpenAI text-embedding-3 / Voyage-3 on
retrieval benchmarks (MTEB), especially for longer or more nuanced passages.
Swapping it out is a one-file change (this module) since every caller only
sees `embed_texts` / `embed_query`.
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
