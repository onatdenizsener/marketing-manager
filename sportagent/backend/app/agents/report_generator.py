import asyncio
import json
import logging
import os
import time
import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.normalizer import normalize, NormalizedSignal
from app.agents.synthesizer import synthesize, NicheReport
from app.agents.markdown_renderer import render_html
from app.config import settings

logger = logging.getLogger(__name__)

NICHES = ["football", "sports_toys", "3d_printed_toys"]


async def _fetch_signals(db: AsyncSession, since: datetime) -> list[dict[str, Any]]:
    result = await db.execute(
        text("""
            SELECT id, niche, source, source_type, title, url, fetched_at
            FROM raw_signals
            WHERE fetched_at >= :since
            ORDER BY fetched_at DESC
        """),
        {"since": since},
    )
    rows = [dict(r._mapping) for r in result]
    logger.debug("Fetched %d raw signals since %s", len(rows), since.isoformat())
    return rows


async def _upsert_report(db: AsyncSession, report_date: date, status: str,
                         niches_data: dict, signals_used: int, llm_tokens: int,
                         duration_ms: int, errors: list[str], markdown: str | None = None) -> str:
    report_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO daily_reports (id, report_date, status, niches, markdown, signals_used, llm_tokens, duration_ms, errors)
            VALUES (:id, :report_date, :status, :niches, :markdown, :signals_used, :llm_tokens, :duration_ms, :errors)
            ON CONFLICT (report_date) DO UPDATE SET
                status = EXCLUDED.status,
                niches = EXCLUDED.niches,
                markdown = EXCLUDED.markdown,
                signals_used = EXCLUDED.signals_used,
                llm_tokens = EXCLUDED.llm_tokens,
                duration_ms = EXCLUDED.duration_ms,
                errors = EXCLUDED.errors,
                updated_at = NOW()
            RETURNING id
        """),
        {
            "id": report_id,
            "report_date": report_date,
            "status": status,
            "niches": json.dumps(niches_data),
            "markdown": markdown,
            "signals_used": signals_used,
            "llm_tokens": llm_tokens,
            "duration_ms": duration_ms,
            "errors": json.dumps(errors),
        },
    )
    await db.commit()
    return report_id


async def generate_report(db: AsyncSession, since: datetime | None = None) -> dict[str, Any]:
    t0 = time.monotonic()
    today = date.today()
    if since is None:
        since = datetime.now(timezone.utc) - timedelta(hours=24)

    logger.info("Starting report generation for %s (since %s)", today, since.isoformat())

    raw_signals = await _fetch_signals(db, since)
    if not raw_signals:
        logger.warning("No raw signals found")
        await _upsert_report(db, today, "failed", {}, 0, 0, 0, ["No signals found"])
        return {"status": "failed", "errors": ["No signals found"]}

    by_niche: dict[str, list[dict]] = {n: [] for n in NICHES}
    for s in raw_signals:
        s["id"] = str(s["id"])
        s["fetched_at"] = s["fetched_at"].isoformat() if isinstance(s["fetched_at"], datetime) else str(s["fetched_at"])
        niche = s.get("niche")
        if niche in by_niche:
            by_niche[niche].append(s)

    normalized_by_niche: dict[str, list[NormalizedSignal]] = {}
    for niche, sigs in by_niche.items():
        if sigs:
            normalized_by_niche[niche] = normalize(sigs)
            logger.info("Niche '%s': %d -> %d signals after normalize", niche, len(sigs), len(normalized_by_niche[niche]))

    if not normalized_by_niche:
        await _upsert_report(db, today, "failed", {}, 0, 0, 0, ["No signals after normalization"])
        return {"status": "failed", "errors": ["No signals after normalization"]}

    try:
        niche_reports: dict[str, NicheReport] = await synthesize(normalized_by_niche)
    except Exception as exc:
        logger.error("Synthesize failed: %s", exc)
        await _upsert_report(db, today, "failed", {}, len(raw_signals), 0, int((time.monotonic() - t0) * 1000), [str(exc)])
        return {"status": "failed", "errors": [str(exc)]}

    niches_data = {k: v.model_dump() for k, v in niche_reports.items()}
    failed_niches = [k for k, v in niche_reports.items() if v.insufficient_data]
    status = "partial" if failed_niches else "success"

    html = render_html(today, niche_reports)
    os.makedirs(settings.outputs_dir, exist_ok=True)
    html_path = os.path.join(settings.outputs_dir, f"report-{today.isoformat()}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info("HTML report written: %s", html_path)

    duration_ms = int((time.monotonic() - t0) * 1000)
    report_id = await _upsert_report(
        db, today, status, niches_data,
        signals_used=len(raw_signals),
        llm_tokens=0,
        duration_ms=duration_ms,
        errors=failed_niches,
        markdown=html,
    )

    logger.info("Report %s done: status=%s duration=%dms", report_id, status, duration_ms)
    return {
        "status": status,
        "report_id": report_id,
        "report_date": today.isoformat(),
        "signals_used": len(raw_signals),
        "duration_ms": duration_ms,
        "html_path": html_path,
        "failed_niches": failed_niches,
    }


if __name__ == "__main__":
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    async def main():
        from app.logging_config import setup_logging
        setup_logging()
        from app.db.base import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await generate_report(db)
            print(json.dumps(result, indent=2, default=str))

    asyncio.run(main())
