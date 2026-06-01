import logging
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}


@router.get("/healthz/db")
async def healthz_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        logger.debug("DB healthcheck passed")
        return {"status": "ok"}
    except Exception as exc:
        logger.error("DB healthcheck failed: %s", exc)
        return {"status": "error", "detail": str(exc)}


@router.get("/healthz/llm")
async def healthz_llm():
    import anthropic
    try:
        client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=httpx.Timeout(15.0, connect=5.0),
        )
        msg = await client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=5,
            messages=[{"role": "user", "content": "ping"}],
        )
        logger.debug("LLM healthcheck passed, stop_reason=%s", msg.stop_reason)
        return {"status": "ok"}
    except Exception as exc:
        logger.error("LLM healthcheck failed: %s", exc)
        return {"status": "error", "detail": str(exc)}


@router.get("/healthz/n8n")
async def healthz_n8n():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.head(settings.n8n_url)
        logger.debug("n8n healthcheck passed, status=%s", resp.status_code)
        return {"status": "ok", "http_status": resp.status_code}
    except Exception as exc:
        logger.error("n8n healthcheck failed: %s", exc)
        return {"status": "error", "detail": str(exc)}
