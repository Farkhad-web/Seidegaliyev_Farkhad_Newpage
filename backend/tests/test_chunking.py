from app.rag.chunking import chunk_pages, split_text


def test_short_text_is_a_single_chunk():
    assert split_text("hello world", chunk_size=900, chunk_overlap=150) == ["hello world"]


def test_empty_text_produces_no_chunks():
    assert split_text("   \n  ", chunk_size=900, chunk_overlap=150) == []


def test_splits_on_paragraph_boundary_before_hard_cutting():
    paragraphs = [f"Paragraph {i}. " * 6 for i in range(6)]
    text = "\n\n".join(paragraphs)
    chunks = split_text(text, chunk_size=200, chunk_overlap=0)
    assert len(chunks) > 1
    # None of the (non-overlapping) chunks should exceed the target size by much.
    assert all(len(c) <= 220 for c in chunks)


def test_overlap_repeats_trailing_context_in_next_chunk():
    text = "sentence one. " * 40
    chunks = split_text(text, chunk_size=100, chunk_overlap=30)
    assert len(chunks) > 1
    for prev, nxt in zip(chunks, chunks[1:]):
        tail = prev[-30:]
        assert nxt.startswith(tail)


def test_long_word_with_no_separators_is_hard_cut():
    text = "a" * 500
    chunks = split_text(text, chunk_size=100, chunk_overlap=0)
    assert sum(len(c) for c in chunks) == 500
    assert all(len(c) <= 100 for c in chunks)


def test_chunk_pages_assigns_correct_page_numbers_and_sequential_index():
    pages = [(1, "Short page one text."), (5, "Page five has more content here.")]
    pieces = chunk_pages(pages, chunk_size=900, chunk_overlap=0)
    assert [p.page for p in pieces] == [1, 5]
    assert [p.chunk_index for p in pieces] == [0, 1]


def test_chunk_pages_never_spans_a_page_break():
    pages = [(1, "x" * 50), (2, "y" * 50)]
    pieces = chunk_pages(pages, chunk_size=30, chunk_overlap=0)
    for piece in pieces:
        assert set(piece.text) <= {"x"} or set(piece.text) <= {"y"}
