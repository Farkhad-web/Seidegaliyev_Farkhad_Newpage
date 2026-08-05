"""Central runtime configuration, loaded from environment variables / .env.

Every tunable that affects retrieval quality or cost lives here rather than
scattered through the codebase, so the trade-offs documented in the README
map onto one place in the code.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- LLM ---
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-latest"
    condense_model: str = "claude-3-5-haiku-latest"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1024

    # --- Embeddings ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Chunking ---
    chunk_size: int = 900
    chunk_overlap: int = 150

    # --- Retrieval ---
    retrieval_top_k: int = 6
    vector_candidates: int = 20
    bm25_candidates: int = 20
    rrf_k: int = 60
    confidence_threshold: float = 0.30

    # --- Context management ---
    max_history_turns: int = 6
    condense_after_turns: int = 1

    # --- Guardrails ---
    max_message_chars: int = 4000
    max_upload_mb: int = 20
    allowed_extensions: tuple[str, ...] = (".pdf", ".txt", ".md")
    max_documents: int = 200

    # --- Rate limiting ---
    rate_limit_chat_per_minute: int = 20
    rate_limit_upload_per_minute: int = 10

    # --- Storage ---
    sqlite_path: str = str(DATA_DIR / "documind.db")
    chroma_path: str = str(DATA_DIR / "chroma")

    # --- CORS ---
    # 5173 = Vite dev server (frontend run outside Docker); 8080 = the nginx
    # container published by docker-compose.
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.sqlite_path}"


@lru_cache
def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
