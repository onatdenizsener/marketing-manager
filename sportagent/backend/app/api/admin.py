import logging
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.auth import verify_token
from app.agents.report_generator import generate_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


class SynthesizeRequest(BaseModel):
    since: datetime | None = None
    trigger: str = "manual"
    timestamp: str | None = None


@router.post("/run-now")
async def run_now(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_token),
):
    logger.info("Manual pipeline trigger: /admin/run-now")
    result = await generate_report(db)
    return result


@router.post("/synthesize")
async def synthesize_callback(
    body: SynthesizeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_token),
):
    logger.info("n8n callback /admin/synthesize trigger=%s since=%s", body.trigger, body.since)
    since = body.since
    if since and since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    result = await generate_report(db, since=since)
    return result
