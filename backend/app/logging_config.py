"""Structured (JSON) logging so every request and RAG trace is machine-readable.

This is the cheap half of "observability": no external APM, just logs shaped
so they could be piped into anything that reads JSON lines. The other half
(the Trace / TraceChunk DB tables) captures the *content* of each RAG call for
the in-app Observability panel; this module captures *operational* events.
"""
import json
import logging
import sys
import time
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": round(time.time(), 3),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    # Quiet noisy third-party loggers down to warnings.
    for noisy in ("uvicorn.access", "httpx", "sentence_transformers", "chromadb"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    # Chroma's telemetry pings a version-mismatched posthog signature and
    # logs it as an ERROR even with anonymized_telemetry disabled — harmless,
    # but noisy enough in every request log to be worth silencing outright.
    logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, message: str, **fields: Any) -> None:
    logger.info(message, extra={"extra_fields": fields})
