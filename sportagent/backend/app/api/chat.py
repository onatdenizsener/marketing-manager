import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator

import anthropic
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_token
from app.config import settings
from app.db.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 4096
TIMEOUT = 60.0
RECENT_REPORTS_LIMIT = 5

_SYSTEM_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "prompts", "chat_system.md"
)


def _load_system_prompt() -> str:
    with open(_SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
        return f.read()


async def _get_recent_reports_context(db: AsyncSession) -> str:
    result = await db.execute(
        text("""
            SELECT report_date, status, niches
            FROM daily_reports
            WHERE status IN ('success','partial')
            ORDER BY report_date DESC
            LIMIT :n
        """),
        {"n": RECENT_REPORTS_LIMIT},
    )
    rows = result.fetchall()
    if not rows:
        return ""
    parts = ["## Son Raporlar (Özet)"]
    for row in rows:
        d = dict(row._mapping)
        date_str = d["report_date"].isoformat() if d["report_date"] else "?"
        niches_data = d["niches"] or {}
        parts.append(f"\n### {date_str}")
        for niche, ndata in niches_data.items():
            if isinstance(ndata, dict) and not ndata.get("insufficient_data"):
                trends = [t.get("keyword", "") for t in (ndata.get("trending") or [])[:3]]
                if trends:
                    parts.append(f"- **{niche}**: {', '.join(trends)}")
    return "\n".join(parts)


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


async def _stream_response(
    user_message: str,
    conversation_id: str,
    db: AsyncSession,
) -> AsyncIterator[str]:
    system_base = _load_system_prompt()
    reports_ctx = await _get_recent_reports_context(db)
    system_prompt = f"{system_base}\n\n{reports_ctx}" if reports_ctx else system_base

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": user_message}]

    full_text = ""
    tool_calls_log = []

    try:
        async with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            timeout=TIMEOUT,
            system=system_prompt,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages,
        ) as stream:
            async for event in stream:
                if hasattr(event, "type"):
                    etype = event.type

                    if etype == "content_block_delta":
                        delta = event.delta
                        if hasattr(delta, "text") and delta.text:
                            full_text += delta.text
                            yield _sse("text", json.dumps({"chunk": delta.text}, ensure_ascii=False))

                    elif etype == "content_block_start":
                        block = event.content_block
                        if hasattr(block, "type") and block.type == "tool_use":
                            if hasattr(block, "name") and block.name == "web_search":
                                yield _sse("status", json.dumps({"msg": "🔎 web'de araştırılıyor..."}, ensure_ascii=False))
                                tool_calls_log.append({"name": block.name, "id": block.id})
                                logger.debug("Tool use started: %s id=%s", block.name, block.id)

                    elif etype == "content_block_stop":
                        pass

        # After stream, save messages
        await db.execute(
            text("""
                INSERT INTO chat_messages (id, conversation_id, role, content, tool_calls)
                VALUES (:id, :conv_id, 'user', :content, NULL)
            """),
            {"id": str(uuid.uuid4()), "conv_id": conversation_id, "content": user_message},
        )
        await db.execute(
            text("""
                INSERT INTO chat_messages (id, conversation_id, role, content, tool_calls)
                VALUES (:id, :conv_id, 'assistant', :content, :tool_calls)
            """),
            {
                "id": str(uuid.uuid4()),
                "conv_id": conversation_id,
                "content": full_text,
                "tool_calls": json.dumps(tool_calls_log) if tool_calls_log else None,
            },
        )
        await db.commit()

        yield _sse("done", json.dumps({"conversation_id": conversation_id}, ensure_ascii=False))

    except Exception as exc:
        logger.error("Chat stream error: %s", exc)
        yield _sse("error", json.dumps({"detail": str(exc)}, ensure_ascii=False))


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


@router.post("")
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_token),
):
    conv_id = body.conversation_id or str(uuid.uuid4())
    logger.info("Chat request conv_id=%s msg_len=%d", conv_id, len(body.message))

    return StreamingResponse(
        _stream_response(body.message, conv_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
