import asyncio
import json
import logging
import os
from typing import Literal, Any
import anthropic
import httpx
from pydantic import BaseModel, field_validator, model_validator

from app.config import settings
from app.agents.normalizer import NormalizedSignal

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 8192
TIMEOUT = 150.0
MAX_RETRIES = 1

_SYSTEM_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "prompts", "synthesizer_system.md"
)


def _load_system_prompt() -> str:
    with open(_SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
        return f.read()


class TrendItem(BaseModel):
    keyword: str
    momentum: Literal["rising", "stable", "declining"]
    source_signal_ids: list[str]
    rationale: str

    @field_validator("rationale")
    @classmethod
    def truncate_rationale(cls, v: str) -> str:
        return v[:200]


class NewsSummaryItem(BaseModel):
    headline: str
    summary_one_liner: str
    source_signal_ids: list[str]


_FORMAT_ALIASES: dict[str, str] = {
    "twitter_thread": "tweet",
    "thread": "tweet",
    "instagram_reel": "reels",
    "tiktok": "reels",
    "short": "youtube_short",
    "instagram_story": "story",
}

_VALID_FORMATS = {"reels", "story", "tweet", "post", "youtube_short"}


class ContentAngle(BaseModel):
    idea: str
    format: str
    target_audience: str
    hashtags: list[str]
    source_signal_ids: list[str]

    @field_validator("format", mode="before")
    @classmethod
    def normalize_format(cls, v: str) -> str:
        v = str(v).lower().strip()
        return _FORMAT_ALIASES.get(v, v if v in _VALID_FORMATS else "post")


class CampaignPlan(BaseModel):
    theme: str
    hook: str | None = None
    target_audience: str | None = None
    channel_recommendations: list[str] = []
    content_pillar: str | None = None

    @field_validator("content_pillar", "hook", "target_audience", mode="before")
    @classmethod
    def coerce_str_or_list(cls, v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, list):
            return ", ".join(str(i) for i in v) if v else None
        return str(v)

    @field_validator("channel_recommendations", mode="before")
    @classmethod
    def coerce_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return [str(i) for i in v]


class NicheReport(BaseModel):
    insufficient_data: bool = False
    trending: list[TrendItem] = []
    news_summary: list[NewsSummaryItem] = []
    content_angles: list[ContentAngle] = []
    campaign_plan: CampaignPlan | None = None
    errors: list[str] = []


class SynthesisResult(BaseModel):
    football: NicheReport
    sports_toys: NicheReport
    three_d_printed_toys: NicheReport = NicheReport(insufficient_data=True, errors=["alias mapping"])

    model_config = {"populate_by_name": True}


def _validate_signal_ids(report: NicheReport, valid_ids: set[str]) -> NicheReport:
    """Drop items whose source_signal_ids are not in the valid_ids set."""
    def _has_valid(ids: list[str]) -> bool:
        return any(i in valid_ids for i in ids)

    report.trending = [t for t in report.trending if _has_valid(t.source_signal_ids)]
    report.news_summary = [n for n in report.news_summary if _has_valid(n.source_signal_ids)]
    report.content_angles = [c for c in report.content_angles if _has_valid(c.source_signal_ids)]
    if report.campaign_plan is not None:
        pass  # campaign_plan has no signal IDs
    return report


async def synthesize(signals_by_niche: dict[str, list[NormalizedSignal]]) -> dict[str, NicheReport]:
    """Call Claude with all niche signals and return validated NicheReport per niche."""
    system_prompt = _load_system_prompt()
    client = anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        timeout=httpx.Timeout(TIMEOUT, connect=10.0),
    )

    signals_payload: dict[str, list[dict]] = {}
    valid_ids_by_niche: dict[str, set[str]] = {}
    for niche, sigs in signals_by_niche.items():
        signals_payload[niche] = [
            {"id": s.id, "title": s.title, "url": s.url, "fetched_at": s.fetched_at}
            for s in sigs
        ]
        valid_ids_by_niche[niche] = {s.id for s in sigs}

    user_content = json.dumps({"signals": signals_payload}, ensure_ascii=False)
    total_signals = sum(len(v) for v in signals_payload.values())
    input_bytes = len(user_content.encode("utf-8"))

    for attempt in range(1, MAX_RETRIES + 2):
        logger.info("Synthesizer attempt %d/%d | signals=%d input_kb=%.1f",
                    attempt, MAX_RETRIES + 1, total_signals, input_bytes / 1024)
        logger.debug("LLM call: model=%s max_tokens=%d", MODEL, MAX_TOKENS)

        try:
            response = await asyncio.wait_for(
                client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_content}],
                ),
                timeout=TIMEOUT,
            )
            raw_text = response.content[0].text.strip()
            # Strip markdown code fences if Claude wraps response despite instructions
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
            logger.debug("LLM response length=%d tokens_in=%d tokens_out=%d",
                         len(raw_text), response.usage.input_tokens, response.usage.output_tokens)

            raw_json: dict[str, Any] = json.loads(raw_text)
            break
        except asyncio.TimeoutError:
            logger.warning("Attempt %d: LLM call timed out after %ss", attempt, TIMEOUT)
            if attempt > MAX_RETRIES:
                return {n: NicheReport(insufficient_data=True, errors=["LLM timeout"]) for n in signals_by_niche}
        except json.JSONDecodeError as exc:
            logger.warning("Attempt %d: JSON parse error: %s", attempt, exc)
            if attempt > MAX_RETRIES:
                logger.error("All retries exhausted, returning empty reports")
                return {n: NicheReport(insufficient_data=True, errors=[f"JSON parse failed: {exc}"]) for n in signals_by_niche}
        except Exception as exc:
            logger.error("Attempt %d: LLM call failed: %s", attempt, exc)
            if attempt > MAX_RETRIES:
                return {n: NicheReport(insufficient_data=True, errors=[str(exc)]) for n in signals_by_niche}

    results: dict[str, NicheReport] = {}
    niche_key_map = {
        "football": "football",
        "sports_toys": "sports_toys",
        "3d_printed_toys": "3d_printed_toys",
    }

    for niche, key in niche_key_map.items():
        try:
            raw_niche = raw_json.get(key, {})
            report = NicheReport.model_validate(raw_niche)
            valid_ids = valid_ids_by_niche.get(niche, set())
            report = _validate_signal_ids(report, valid_ids)
            results[niche] = report
            logger.info("Niche '%s': %d trends, %d news, %d angles",
                        niche, len(report.trending), len(report.news_summary), len(report.content_angles))
        except Exception as exc:
            logger.error("Failed to parse niche '%s': %s", niche, exc)
            results[niche] = NicheReport(insufficient_data=True, errors=[str(exc)])

    return results


if __name__ == "__main__":
    import asyncio
    import sys
    import os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    async def main():
        from app.logging_config import setup_logging
        setup_logging()

        fixture = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "tests", "fixtures", "sample_signals.json"
        )
        with open(fixture, encoding="utf-8") as f:
            raw = json.load(f)

        from app.agents.normalizer import normalize
        signals_by_niche: dict[str, list[NormalizedSignal]] = {}
        for niche, sigs in raw.items():
            normalized = normalize(sigs)
            signals_by_niche[niche] = normalized

        result = await synthesize(signals_by_niche)
        for niche, report in result.items():
            print(f"\n{'='*60}")
            print(f"NICHE: {niche}")
            print(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))

    asyncio.run(main())
