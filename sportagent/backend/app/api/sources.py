import logging
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/health")
async def sources_health(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_token),
):
    result = await db.execute(
        text("""
            SELECT
                source,
                COUNT(*) FILTER (WHERE attempted_at >= NOW() - INTERVAL '7 days') AS total_7d,
                COUNT(*) FILTER (WHERE success AND attempted_at >= NOW() - INTERVAL '7 days') AS success_7d,
                MAX(attempted_at) AS last_attempt,
                SUM(signals_count) FILTER (WHERE attempted_at >= NOW() - INTERVAL '7 days') AS signals_7d
            FROM sources_health
            GROUP BY source
            ORDER BY source
        """)
    )
    rows = []
    for r in result:
        d = dict(r._mapping)
        total = d["total_7d"] or 0
        success = d["success_7d"] or 0
        d["success_rate_7d"] = round(success / total, 3) if total > 0 else None
        d["last_attempt"] = d["last_attempt"].isoformat() if d["last_attempt"] else None
        rows.append(d)
    return rows
