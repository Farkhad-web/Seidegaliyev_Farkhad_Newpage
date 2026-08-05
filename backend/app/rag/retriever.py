"""Hybrid retrieval: dense vector search + BM25 keyword search, combined with
Reciprocal Rank Fusion (RRF).

Why hybrid instead of vector-only: dense embeddings are great at semantic
similarity but routinely miss exact terms that matter in domain text — model
numbers, chemical names, error codes, acronyms — because those tokens are
often underrepresented in a small local embedding model's training data.
BM25 is the opposite: exact/lexical, blind to paraphrase. RRF fuses the two
rankings without needing to normalize incomparable score scales (cosine
similarity vs. BM25's unbounded score), which is what makes it a popular
default over a hand-tuned weighted sum.
"""
from dataclasses import dataclass

from sqlmodel import Session, select

from app.config import get_settings
from app.models import Chunk
from app.rag import bm25_index, vectorstore
from app.rag.embeddings import embed_query


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    page: int
    text: str
    vector_score: float
    bm25_score: float
    fused_score: float
    rank: int


def _rrf_scores(ranked_ids: list[str], k: int) -> dict[str, float]:
    return {cid: 1.0 / (k + rank) for rank, cid in enumerate(ranked_ids, start=1)}


def hybrid_retrieve(session: Session, query_text: str) -> list[RetrievedChunk]:
    settings = get_settings()

    vector_hits = vectorstore.query(embed_query(query_text), settings.vector_candidates)
    bm25_hits = bm25_index.search(query_text, settings.bm25_candidates)

    vector_scores = {h["chunk_id"]: h["score"] for h in vector_hits}
    bm25_scores = {cid: score for cid, score in bm25_hits}

    vector_rrf = _rrf_scores([h["chunk_id"] for h in vector_hits], settings.rrf_k)
    bm25_rrf = _rrf_scores([cid for cid, _ in bm25_hits], settings.rrf_k)

    all_ids = set(vector_rrf) | set(bm25_rrf)
    fused = {cid: vector_rrf.get(cid, 0.0) + bm25_rrf.get(cid, 0.0) for cid in all_ids}
    ranked_ids = sorted(fused, key=lambda cid: fused[cid], reverse=True)[: settings.retrieval_top_k]

    if not ranked_ids:
        return []

    chunks = session.exec(select(Chunk).where(Chunk.id.in_(ranked_ids))).all()
    chunk_by_id = {c.id: c for c in chunks}

    results: list[RetrievedChunk] = []
    for rank, chunk_id in enumerate(ranked_ids, start=1):
        chunk = chunk_by_id.get(chunk_id)
        if chunk is None:
            continue
        results.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                document_id=chunk.document_id,
                filename=chunk.filename,
                page=chunk.page,
                text=chunk.text,
                vector_score=round(vector_scores.get(chunk_id, 0.0), 4),
                bm25_score=round(bm25_scores.get(chunk_id, 0.0), 4),
                fused_score=round(fused[chunk_id], 5),
                rank=rank,
            )
        )
    return results


def top_confidence(results: list[RetrievedChunk]) -> float:
    """Highest raw vector cosine similarity among the retrieved chunks — used
    as a cheap, secondary groundedness signal (see guardrails.py)."""
    if not results:
        return 0.0
    return max(r.vector_score for r in results)
