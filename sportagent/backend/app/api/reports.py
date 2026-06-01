import logging
import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
async def list_reports(
    limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_token),
):
    result = await db.execute(
        text("""
            SELECT id, report_date, status, signals_used, llm_tokens, duration_ms, created_at
            FROM daily_reports
            ORDER BY report_date DESC
            LIMIT :limit
        """),
        {"limit": limit},
    )
    rows = [dict(r._mapping) for r in result]
    for r in rows:
        r["id"] = str(r["id"])
        r["report_date"] = r["report_date"].isoformat() if r["report_date"] else None
        r["created_at"] = r["created_at"].isoformat() if r["created_at"] else None
    return rows


@router.get("/by-date/{report_date}")
async def get_report_by_date(
    report_date: date,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_token),
):
    result = await db.execute(
        text("SELECT * FROM daily_reports WHERE report_date = :d"),
        {"d": report_date},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    data = dict(row._mapping)
    data["id"] = str(data["id"])
    data["report_date"] = data["report_date"].isoformat()
    data["created_at"] = data["created_at"].isoformat()
    data["updated_at"] = data["updated_at"].isoformat()
    return data


@router.get("/{report_id}")
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_token),
):
    result = await db.execute(
        text("SELECT * FROM daily_reports WHERE id = :id"),
        {"id": report_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    data = dict(row._mapping)
    data["id"] = str(data["id"])
    data["report_date"] = data["report_date"].isoformat()
    data["created_at"] = data["created_at"].isoformat()
    data["updated_at"] = data["updated_at"].isoformat()
    return data
