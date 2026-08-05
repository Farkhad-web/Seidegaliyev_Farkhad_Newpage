import pytest

from app.rag.guardrails import GuardrailError, assess_confidence, validate_message, validate_upload


def test_validate_message_strips_and_passes_through():
    assert validate_message("  what is the return policy?  ") == "what is the return policy?"


def test_validate_message_rejects_empty():
    with pytest.raises(GuardrailError):
        validate_message("   ")


def test_validate_message_rejects_too_long():
    with pytest.raises(GuardrailError):
        validate_message("a" * 5000)


def test_validate_upload_rejects_bad_extension():
    result = validate_upload("resume.docx", 1000, existing_document_count=0)
    assert not result.ok
    assert "Unsupported" in result.reason


def test_validate_upload_rejects_empty_file():
    result = validate_upload("notes.txt", 0, existing_document_count=0)
    assert not result.ok
    assert "empty" in result.reason.lower()


def test_validate_upload_rejects_oversized_file():
    too_big = 21 * 1024 * 1024
    result = validate_upload("book.pdf", too_big, existing_document_count=0)
    assert not result.ok
    assert "limit" in result.reason.lower()


def test_validate_upload_accepts_reasonable_pdf():
    result = validate_upload("manual.pdf", 500_000, existing_document_count=3)
    assert result.ok


def test_assess_confidence_flags_low_scores():
    confidence, low = assess_confidence(0.1)
    assert confidence == 0.1
    assert low is True


def test_assess_confidence_accepts_high_scores():
    confidence, low = assess_confidence(0.8)
    assert low is False
