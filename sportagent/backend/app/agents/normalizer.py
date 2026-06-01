import logging
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

TOP_N_PER_NICHE = 20

SOURCE_AUTHORITY: dict[str, float] = {
    "rss_bbc_sport": 1.0,
    "rss_goal": 0.9,
    "rss_eurosport": 0.85,
    "rss_aa_spor": 0.8,
    "rss_ntv_spor": 0.75,
    "news_api": 0.7,
    "trends_rss_us": 0.9,
    "trends_rss_tr": 0.85,
    "trends_rss_gb": 0.8,
    "reddit_soccer": 0.7,
    "reddit_football": 0.7,
    "reddit_3dprinting": 0.65,
    "reddit_functionalprint": 0.6,
    "reddit_soccerjerseys": 0.65,
}
DEFAULT_AUTHORITY = 0.5


class NormalizedSignal(BaseModel):
    id: str
    niche: str
    source: str
    source_type: str
    title: str
    url: str
    fetched_at: str
    score: float


def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _title_hash(title: str) -> str:
    normalized = " ".join(title.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()


def _recency_score(fetched_at_str: str, now: datetime) -> float:
    try:
        if fetched_at_str.endswith("Z"):
            fetched_at_str = fetched_at_str[:-1] + "+00:00"
        fetched_at = datetime.fromisoformat(fetched_at_str)
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        age_hours = (now - fetched_at).total_seconds() / 3600
        return max(0.0, 1.0 - age_hours / 24.0)
    except Exception as exc:
        logger.debug("Could not parse fetched_at '%s': %s", fetched_at_str, exc)
        return 0.5


def normalize(signals: list[dict[str, Any]], top_n: int = TOP_N_PER_NICHE) -> list[NormalizedSignal]:
    """Deduplicate, score and return top-N signals."""
    now = datetime.now(timezone.utc)
    seen_url_hashes: set[str] = set()
    seen_title_hashes: set[str] = set()
    scored: list[tuple[float, NormalizedSignal]] = []

    for sig in signals:
        url = sig.get("url") or ""
        title = sig.get("title") or ""

        if url:
            uh = _url_hash(url)
            if uh in seen_url_hashes:
                logger.debug("Dedup URL: %s", url[:80])
                continue
            seen_url_hashes.add(uh)

        if title:
            th = _title_hash(title)
            if th in seen_title_hashes:
                logger.debug("Dedup title: %s", title[:80])
                continue
            seen_title_hashes.add(th)

        source = sig.get("source", "")
        authority = SOURCE_AUTHORITY.get(source, DEFAULT_AUTHORITY)
        recency = _recency_score(sig.get("fetched_at", ""), now)
        score = round(authority * 0.6 + recency * 0.4, 4)

        logger.debug("Signal id=%s score=%.4f (authority=%.2f recency=%.2f)", sig.get("id"), score, authority, recency)

        scored.append((score, NormalizedSignal(
            id=str(sig.get("id", "")),
            niche=sig.get("niche", ""),
            source=source,
            source_type=sig.get("source_type", ""),
            title=title,
            url=url,
            fetched_at=sig.get("fetched_at", ""),
            score=score,
        )))

    scored.sort(key=lambda x: x[0], reverse=True)
    result = [item for _, item in scored[:top_n]]
    logger.info("Normalized %d -> %d signals (top %d)", len(signals), len(result), top_n)
    return result


if __name__ == "__main__":
    import asyncio
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    async def main():
        from app.logging_config import setup_logging
        setup_logging()
        from app.db.base import AsyncSessionLocal
        from sqlalchemy import text
        from datetime import timezone

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        async with AsyncSessionLocal() as session:
            rows = await session.execute(
                text("""
                    SELECT id, niche, source, source_type, title, url, fetched_at
                    FROM raw_signals
                    WHERE fetched_at >= :since
                    ORDER BY fetched_at DESC
                """),
                {"since": since},
            )
            signals = [dict(r._mapping) for r in rows]

        if not signals:
            print("No signals in DB for last 24h. Using sample_signals.json")
            fixture = os.path.join(os.path.dirname(__file__), "..", "..", "..", "tests", "fixtures", "sample_signals.json")
            with open(fixture) as f:
                raw = json.load(f)
            signals = [s for niche_list in raw.values() for s in niche_list]

        by_niche: dict[str, list] = {}
        for s in signals:
            s["id"] = str(s["id"])
            s["fetched_at"] = str(s["fetched_at"])
            by_niche.setdefault(s["niche"], []).append(s)

        for niche, niche_signals in by_niche.items():
            normalized = normalize(niche_signals)
            print(f"\n=== {niche} ({len(normalized)} signals) ===")
            for ns in normalized[:5]:
                print(f"  [{ns.score:.3f}] {ns.title[:80]}")

    asyncio.run(main())
