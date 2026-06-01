import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.logging_config import setup_logging
from app.db.base import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Sport Trends Marketing Agent starting up")
    yield
    await engine.dispose()
    logger.info("Sport Trends Marketing Agent shut down")


app = FastAPI(
    title="Sport Trends Marketing Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import health, reports, chat, sources, admin  # noqa: E402

app.include_router(health.router)
app.include_router(reports.router)
app.include_router(chat.router)
app.include_router(sources.router)
app.include_router(admin.router)
