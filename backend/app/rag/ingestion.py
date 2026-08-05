"""Document ingestion: parse -> chunk -> embed -> persist (SQLite + Chroma)
-> rebuild the BM25 index.

Runs synchronously inside the upload request for simplicity — acceptable for
demo-sized documents (a few dozen pages embeds in well under a second on
CPU). For large files or high upload volume this is the first thing I'd move
to a background task queue (see README "What's next").
"""
from sqlmodel import Session, select

from app.config import get_settings
from app.logging_config import get_logger, log_event
from app.models import Chunk, Document, DocumentStatus
from app.rag import bm25_index, storage, vectorstore
from app.rag.chunking import chunk_pages
from app.rag.embeddings import embed_texts
from app.rag.parsing import UnsupportedFileType, parse_document

logger = get_logger("rag.ingestion")


def _run_pipeline(session: Session, document: Document, content: bytes) -> None:
    """Parse/chunk/embed `content` and update `document` in place. Shared by
    both first-time ingestion and reindexing, so the two can't drift."""
    settings = get_settings()
    try:
        pages = parse_document(document.filename, content)
        if not pages:
            raise ValueError("No extractable text found in file")

        pieces = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
        if not pieces:
            raise ValueError("Document produced no chunks")

        chunk_rows = [
            Chunk(
                document_id=document.id,
                filename=document.filename,
                page=piece.page,
                chunk_index=piece.chunk_index,
                text=piece.text,
                char_count=len(piece.text),
            )
            for piece in pieces
        ]
        session.add_all(chunk_rows)
        session.commit()
        for row in chunk_rows:
            session.refresh(row)

        embeddings = embed_texts([c.text for c in chunk_rows])
        vectorstore.add_chunks(
            ids=[c.id for c in chunk_rows],
            embeddings=embeddings.tolist(),
            metadatas=[
                {"document_id": c.document_id, "filename": c.filename, "page": c.page}
                for c in chunk_rows
            ],
            documents=[c.text for c in chunk_rows],
        )

        document.num_pages = len({p for p, _ in pages})
        document.num_chunks = len(chunk_rows)
        document.status = DocumentStatus.ready
        document.error = None
        session.add(document)
        session.commit()
        session.refresh(document)

        rebuild_bm25_index(session)
        log_event(logger, "document ingested", document_id=document.id, filename=document.filename,
                  pages=document.num_pages, chunks=document.num_chunks)

    except (UnsupportedFileType, ValueError) as exc:
        document.status = DocumentStatus.failed
        document.error = str(exc)
        session.add(document)
        session.commit()
        session.refresh(document)
        log_event(logger, "document ingestion failed", document_id=document.id,
                  filename=document.filename, error=str(exc))


def ingest_document(session: Session, filename: str, content_type: str, content: bytes) -> Document:
    document = Document(
        filename=filename,
        content_type=content_type or "application/octet-stream",
        size_bytes=len(content),
        status=DocumentStatus.processing,
    )
    session.add(document)
    session.commit()
    session.refresh(document)

    storage.save_file(document.id, content)
    _run_pipeline(session, document, content)
    return document


def reindex_document(session: Session, document: Document) -> Document:
    """Re-run ingestion from the originally uploaded bytes — e.g. after a
    chunking/embedding config change — without asking the user to re-upload."""
    content = storage.load_file(document.id)
    if content is None:
        document.status = DocumentStatus.failed
        document.error = "Original file is no longer available; please re-upload."
        session.add(document)
        session.commit()
        session.refresh(document)
        return document

    vectorstore.delete_by_document(document.id)
    for chunk in session.exec(select(Chunk).where(Chunk.document_id == document.id)).all():
        session.delete(chunk)
    document.status = DocumentStatus.processing
    document.error = None
    document.num_pages = 0
    document.num_chunks = 0
    session.add(document)
    session.commit()
    session.refresh(document)

    _run_pipeline(session, document, content)
    return document


def delete_document(session: Session, document: Document) -> None:
    vectorstore.delete_by_document(document.id)
    chunks = session.exec(select(Chunk).where(Chunk.document_id == document.id)).all()
    for chunk in chunks:
        session.delete(chunk)
    session.delete(document)
    session.commit()
    storage.delete_file(document.id)
    rebuild_bm25_index(session)


def rebuild_bm25_index(session: Session) -> None:
    rows = session.exec(select(Chunk.id, Chunk.text)).all()
    bm25_index.build([(row[0], row[1]) for row in rows])
