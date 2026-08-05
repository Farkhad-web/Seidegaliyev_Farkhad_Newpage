"""Raw uploaded-file storage — separate from the RAG pipeline, just here to
support the PDF preview and reindex-without-re-upload endpoints."""
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
