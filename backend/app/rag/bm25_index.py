"""In-memory BM25 keyword index, rebuilt from SQLite on startup and after
every document add/delete. Full rebuild is O(total chunks) — fine up to tens
of thousands of chunks, simpler than an incremental structure."""
import re
import threading

from rank_bm25 import BM25Okapi

_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")

_lock = threading.Lock()
_bm25: BM25Okapi | None = None
_chunk_ids: list[str] = []


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def build(chunk_id_to_text: list[tuple[str, str]]) -> None:
    global _bm25, _chunk_ids
    with _lock:
        _chunk_ids = [cid for cid, _ in chunk_id_to_text]
        corpus = [tokenize(text) for _, text in chunk_id_to_text]
        _bm25 = BM25Okapi(corpus) if corpus else None


def search(query: str, top_k: int) -> list[tuple[str, float]]:
    """Returns [(chunk_id, raw_bm25_score)], best first."""
    if _bm25 is None or not _chunk_ids:
        return []
    scores = _bm25.get_scores(tokenize(query))
    ranked = sorted(zip(_chunk_ids, scores), key=lambda x: x[1], reverse=True)
    return [(cid, score) for cid, score in ranked[:top_k] if score > 0]


def is_built() -> bool:
    return _bm25 is not None
