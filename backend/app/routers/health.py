from fastapi import APIRouter

from app.config import get_settings
from app.rag.vectorstore import get_collection

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    try:
        chunk_count = get_collection().count()
        vectorstore_ok = True
    except Exception:
        chunk_count = 0
        vectorstore_ok = False
    return {
        "status": "ok" if vectorstore_ok else "degraded",
        "llm_model": settings.anthropic_model,
        "embedding_model": settings.embedding_model,
        "indexed_chunks": chunk_count,
        "anthropic_key_configured": bool(settings.anthropic_api_key),
    }
