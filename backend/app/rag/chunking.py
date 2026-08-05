"""Recursive character-based text splitter.

Design: try to split on the "biggest" semantic boundary first (blank line),
falling back to progressively smaller ones (newline, sentence, word, hard
cut) only where a piece is still too large. This keeps paragraphs and
sentences intact far more often than a fixed-size sliding window, at the
cost of chunk sizes that vary a bit around the target instead of being exact.
Overlap is then layered on top so a fact split across a chunk boundary is
still visible to whichever chunk retrieval picks up.

Written by hand (no LangChain) — the algorithm is short enough to own
directly and keeping it in-house means no dependency on a framework's
internal chunk-boundary heuristics.
"""
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
    """Chunk each page independently so every chunk carries one accurate
    page number. Trade-off: a chunk never spans a page break, which can
    occasionally cut off context that continues onto the next page — see
    README for the sliding-window alternative considered."""
    pieces: list[ChunkPiece] = []
    global_index = 0
    for page_number, page_text in pages:
        for chunk_text in split_text(page_text, chunk_size, chunk_overlap):
            pieces.append(ChunkPiece(text=chunk_text, page=page_number, chunk_index=global_index))
            global_index += 1
    return pieces
