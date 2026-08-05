"""Recursive character splitter — no LangChain, just splits on the biggest
boundary first (blank line, then newline, sentence, word, hard cut) so
paragraphs stay intact more often than a fixed sliding window would. Overlap
gets layered on top after so a fact split across a boundary is still visible
to whichever chunk retrieval picks."""
from dataclasses import dataclass

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]


@dataclass
class ChunkPiece:
    text: str
    page: int
    chunk_index: int


def _split_on_separator(text: str, separators: list[str], chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    sep, remaining = separators[0], separators[1:]

    if sep == "":
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    raw_pieces = text.split(sep)
    pieces = [p + sep if i < len(raw_pieces) - 1 else p for i, p in enumerate(raw_pieces)]
    pieces = [p for p in pieces if p.strip()]

    merged: list[str] = []
    buffer = ""
    for piece in pieces:
        if len(piece) > chunk_size:
            if buffer:
                merged.append(buffer)
                buffer = ""
            if remaining:
                merged.extend(_split_on_separator(piece, remaining, chunk_size))
            else:
                merged.append(piece[:chunk_size])
            continue
        if len(buffer) + len(piece) <= chunk_size:
            buffer += piece
        else:
            if buffer:
                merged.append(buffer)
            buffer = piece
    if buffer:
        merged.append(buffer)
    return merged


def _apply_overlap(chunks: list[str], overlap: int) -> list[str]:
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    result = [chunks[0]]
    for chunk in chunks[1:]:
        prev = result[-1]
        tail = prev[-overlap:] if len(prev) > overlap else prev
        result.append(tail + chunk)
    return result


def split_text(
    text: str,
    chunk_size: int = 900,
    chunk_overlap: int = 150,
    separators: list[str] | None = None,
) -> list[str]:
    text = text.strip()
    if not text:
        return []
    raw = _split_on_separator(text, separators or DEFAULT_SEPARATORS, chunk_size)
    return _apply_overlap(raw, chunk_overlap)


def chunk_pages(
    pages: list[tuple[int, str]],
    chunk_size: int = 900,
    chunk_overlap: int = 150,
) -> list[ChunkPiece]:
    """Chunks each page independently so every chunk has one accurate page
    number. Trade-off: a chunk never spans a page break, so a sentence
    continuing onto the next page can lose some context."""
    pieces: list[ChunkPiece] = []
    global_index = 0
    for page_number, page_text in pages:
        for chunk_text in split_text(page_text, chunk_size, chunk_overlap):
            pieces.append(ChunkPiece(text=chunk_text, page=page_number, chunk_index=global_index))
            global_index += 1
    return pieces
