from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.config import get_settings
from app.db import engine, init_db
from app.logging_config import configure_logging, get_logger
from app.rag.ingestion import rebuild_bm25_index
from app.rate_limit import SlidingWindowLimiter
from app.routers import chat, conversations, documents, health, traces

configure_logging()
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    with Session(engine) as session:
        rebuild_bm25_index(session)
    app.state.chat_limiter = SlidingWindowLimiter(settings.rate_limit_chat_per_minute)
    app.state.upload_limiter = SlidingWindowLimiter(settings.rate_limit_upload_per_minute)
    logger.info("DocuMind backend started")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="DocuMind API", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.include_router(conversations.router)
    app.include_router(traces.router)
    return app


app = create_app()
