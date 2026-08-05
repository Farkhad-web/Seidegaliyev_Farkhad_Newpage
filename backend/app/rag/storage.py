"""Raw uploaded-file storage.

Deliberately separate from the RAG pipeline: nothing here touches
embeddings, retrieval, or chunking. It exists purely to support two
presentation-layer features — serving the original file back to the
frontend for a source preview, and re-running ingestion (reindex) without
asking the user to re-upload a file we already received once.
"""
from pathlib import Path

from app.config import get_settings


def files_dir() -> Path:
    d = Path(get_settings().files_path)
    d.mkdir(parents=True, exist_ok=True)
    return d


def file_path(document_id: str) -> Path:
    return files_dir() / document_id


def save_file(document_id: str, content: bytes) -> None:
    file_path(document_id).write_bytes(content)


def load_file(document_id: str) -> bytes | None:
    path = file_path(document_id)
    return path.read_bytes() if path.exists() else None


def delete_file(document_id: str) -> None:
    path = file_path(document_id)
    if path.exists():
        path.unlink()
