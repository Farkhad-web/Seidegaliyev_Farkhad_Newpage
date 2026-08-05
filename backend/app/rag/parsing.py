"""Turn an uploaded file into a list of (page_number, text) pairs.

Parsing is intentionally kept per-page: it lets every downstream chunk carry
an accurate page citation. Plain text/Markdown files have no page concept, so
they're treated as a single "page 1" — good enough for the assignment's
scope; a real improvement would be splitting long .md/.txt files into
synthetic pages by heading or line-count (see README "What's next").
"""
import io

from pypdf import PdfReader

SUPPORTED_EXTENSIONS = (".pdf", ".txt", ".md")


class UnsupportedFileType(ValueError):
    pass


def parse_document(filename: str, content: bytes) -> list[tuple[int, str]]:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return _parse_pdf(content)
    if lower.endswith((".txt", ".md")):
        return _parse_text(content)
    raise UnsupportedFileType(f"Unsupported file type: {filename}")


def _parse_pdf(content: bytes) -> list[tuple[int, str]]:
    reader = PdfReader(io.BytesIO(content))
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((i, text))
    return pages


def _parse_text(content: bytes) -> list[tuple[int, str]]:
    text = content.decode("utf-8", errors="replace").strip()
    return [(1, text)] if text else []
