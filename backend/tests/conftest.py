"""Test setup notes:

- All external network calls (the sentence-transformers model download, the
  Anthropic API) are replaced with deterministic fakes. Tests must run
  offline and fast — that's what makes them safe to run on every commit.
- Environment variables that control storage paths are set *before* any
  `app.*` module is imported (settings are read once, at import time, via
  an `lru_cache`d `get_settings()`), so each test session gets its own
  throwaway SQLite file and Chroma directory.
"""
import os
import shutil
import tempfile
from pathlib import Path

_TMP_DIR = Path(tempfile.mkdtemp(prefix="chat_with_your_docs_test_"))
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["SQLITE_PATH"] = str(_TMP_DIR / "test.db")
os.environ["CHROMA_PATH"] = str(_TMP_DIR / "chroma")

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app import db as db_module
from app.main import app
from app.models import Chunk, Conversation, Document, Message, Trace
from app.rag import bm25_index, embeddings, vectorstore


class FakeEmbeddingModel:
    """Deterministic, hash-seeded unit vectors — stands in for the real
    sentence-transformers model so tests never touch the network."""

    def encode(self, texts, normalize_embeddings=True, show_progress_bar=False):
        vectors = []
        for text in texts:
            rng = np.random.default_rng(abs(hash(text)) % (2**32))
            vec = rng.normal(size=384).astype("float32")
            vec = vec / np.linalg.norm(vec)
            vectors.append(vec)
        return np.array(vectors, dtype="float32")


@pytest.fixture(autouse=True, scope="session")
def _fake_embeddings():
    embeddings._model = FakeEmbeddingModel()
    yield


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    db_module.init_db()
    yield
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def _clean_state():
    """Reset SQL tables, the Chroma collection, and the BM25 index before
    every test so tests never leak state into one another."""
    with Session(db_module.engine) as session:
        for model in (Trace, Message, Chunk, Conversation, Document):
            session.exec(delete(model))
        session.commit()
    vectorstore.reset()
    bm25_index.build([])
    yield


@pytest.fixture()
def session():
    with Session(db_module.engine) as s:
        yield s


@pytest.fixture()
def client():
    # sse_starlette caches an anyio.Event bound to whichever event loop first
    # served an SSE response; TestClient spins up a fresh loop per test, so
    # without this reset the second SSE-hitting test crashes with "Event
    # object is bound to a different event loop". See sse_starlette#153.
    import sse_starlette.sse

    sse_starlette.sse.AppStatus.should_exit_event = None
    with TestClient(app) as c:
        yield c


class _FakeUsage:
    def __init__(self, input_tokens=42, output_tokens=7):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _FakeFinalMessage:
    def __init__(self, usage: _FakeUsage):
        self.usage = usage


class _FakeStreamManager:
    def __init__(self, tokens: list[str]):
        self._tokens = tokens

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    @property
    async def text_stream(self):
        for token in self._tokens:
            yield token

    async def get_final_message(self):
        return _FakeFinalMessage(_FakeUsage())


class _FakeTextBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _FakeMessagesAPI:
    def __init__(self, answer_tokens: list[str], condensed: str):
        self._answer_tokens = answer_tokens
        self._condensed = condensed

    async def create(self, **kwargs):
        class Resp:
            pass

        resp = Resp()
        resp.content = [_FakeTextBlock(self._condensed)]
        return resp

    def stream(self, **kwargs):
        return _FakeStreamManager(self._answer_tokens)


class FakeAnthropicClient:
    def __init__(self, answer_tokens=None, condensed="condensed standalone question"):
        self.messages = _FakeMessagesAPI(
            answer_tokens or ["This is a grounded answer ", "citing a source [1]."],
            condensed,
        )


@pytest.fixture()
def fake_llm(monkeypatch):
    fake_client = FakeAnthropicClient()

    def _get_client():
        return fake_client

    monkeypatch.setattr("app.rag.llm.get_client", _get_client)
    return fake_client
