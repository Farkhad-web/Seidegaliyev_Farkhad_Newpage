"""Guardrails applied before and around the LLM call.

Kept as small, explicit, testable functions rather than a black-box
"safety layer" — each one maps to a specific failure mode:
  - validate_message: bounds input size (cost + abuse control).
  - validate_upload: bounds file type/size (cost + parser-crash control).
  - assess_confidence: a numeric heuristic surfaced to the UI as a signal,
    deliberately NOT a hard block — see note below.

On the confidence threshold: retrieval score is a noisy, model-specific
number. Hard-blocking answers below a cosine-similarity cutoff produces
false negatives (a valid answer refused because the local embedding model
under-scored it) as often as it prevents hallucination. So the threshold is
used to *flag* low confidence to the user and to the model (which is told to
say so itself, per the system prompt) rather than to silently refuse — the
groundedness instruction in the prompt is the primary guardrail, this is a
secondary, transparent signal.
"""
from dataclasses import dataclass

from app.config import get_settings


class GuardrailError(ValueError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def validate_message(text: str) -> str:
    text = text.strip()
    if not text:
        raise GuardrailError("Message cannot be empty.")
    settings = get_settings()
    if len(text) > settings.max_message_chars:
        raise GuardrailError(
            f"Message is too long ({len(text)} chars). Limit is {settings.max_message_chars}."
        )
    return text


@dataclass
class UploadValidation:
    ok: bool
    reason: str = ""


def validate_upload(filename: str, size_bytes: int, existing_document_count: int) -> UploadValidation:
    settings = get_settings()
    lower = filename.lower()
    if not lower.endswith(settings.allowed_extensions):
        return UploadValidation(False, f"Unsupported file type. Allowed: {', '.join(settings.allowed_extensions)}")
    if size_bytes == 0:
        return UploadValidation(False, "File is empty.")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if size_bytes > max_bytes:
        return UploadValidation(False, f"File exceeds the {settings.max_upload_mb}MB limit.")
    if existing_document_count >= settings.max_documents:
        return UploadValidation(False, f"Document limit reached ({settings.max_documents}).")
    return UploadValidation(True)


def assess_confidence(top_score: float) -> tuple[float, bool]:
    settings = get_settings()
    return top_score, top_score < settings.confidence_threshold
