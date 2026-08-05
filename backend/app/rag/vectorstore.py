"""Thin wrapper around a persistent Chroma collection. Picked over
pgvector/Qdrant for the same reason as the local embedding model — runs
in-process, no extra service in docker-compose. First thing I'd swap for a
managed vector DB at real scale."""
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

_client: chromadb.ClientAPI | None = None
_collection = None

COLLECTION_NAME = "chunks"


def get_collection():
    global _client, _collection
    if _collection is None:
        settings = get_settings()
        _client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
    return _collection


def add_chunks(ids: list[str], embeddings: list[list[float]], metadatas: list[dict], documents: list[str]) -> None:
    if not ids:
        return
    get_collection().add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)


def delete_by_document(document_id: str) -> None:
    get_collection().delete(where={"document_id": document_id})


def query(embedding: list[float], top_k: int) -> list[dict]:
    """Returns ranked results as similarity in [0, 1] (1 = identical),
    converted from Chroma's cosine distance (0..2)."""
    collection = get_collection()
    if collection.count() == 0:
        return []
    top_k = min(top_k, collection.count())
    result = collection.query(query_embeddings=[embedding], n_results=top_k)
    ids = result["ids"][0]
    distances = result["distances"][0]
    metadatas = result["metadatas"][0]
    documents = result["documents"][0]
    out = []
    for i, chunk_id in enumerate(ids):
        similarity = max(0.0, 1.0 - distances[i] / 2.0)
        out.append({
            "chunk_id": chunk_id,
            "score": similarity,
            "metadata": metadatas[i],
            "text": documents[i],
        })
    return out


def reset() -> None:
    """Test helper: drop and recreate the collection."""
    global _client, _collection
    if _client is not None:
        _client.delete_collection(COLLECTION_NAME)
    _collection = None
    get_collection()
