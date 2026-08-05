from app.rag.retriever import _rrf_scores, hybrid_retrieve
from app.rag.ingestion import ingest_document


def test_rrf_scores_rewards_rank_one_most():
    scores = _rrf_scores(["a", "b", "c"], k=60)
    assert scores["a"] > scores["b"] > scores["c"]
    assert scores["a"] == 1 / 61


def test_rrf_scores_empty_list():
    assert _rrf_scores([], k=60) == {}


def test_hybrid_retrieve_returns_nothing_with_empty_index(session):
    assert hybrid_retrieve(session, "any question") == []


def test_hybrid_retrieve_finds_keyword_match_via_bm25(session):
    # BM25 rewards exact term overlap even when the (fake) embedding space
    # is random noise, so a distinctive keyword should still surface.
    content = (
        b"Section on irrigation.\n\n"
        b"Drip irrigation reduces water usage by up to forty percent compared to flood irrigation.\n\n"
        b"Section on unrelated topic.\n\n"
        b"The quarterly report covers revenue and headcount changes."
    )
    ingest_document(session, "irrigation.txt", "text/plain", content)

    results = hybrid_retrieve(session, "How much water does drip irrigation save?")

    assert len(results) > 0
    assert any("drip irrigation" in r.text.lower() for r in results)
    ranks = [r.rank for r in results]
    assert ranks == sorted(ranks)


def test_hybrid_retrieve_fused_score_is_monotonic_with_rank(session):
    content = b"Alpha bravo charlie.\n\nDelta echo foxtrot.\n\nGolf hotel india.\n\nJuliet kilo lima."
    ingest_document(session, "words.txt", "text/plain", content)

    results = hybrid_retrieve(session, "alpha bravo charlie")
    fused_scores = [r.fused_score for r in results]
    assert fused_scores == sorted(fused_scores, reverse=True)
