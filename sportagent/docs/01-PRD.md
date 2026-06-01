# PRD — Sport Trends Marketing Agent

## Ne yapar
Her sabah 07:00'de futbol, spor oyuncakları ve 3D-printed oyuncak nişlerinde trendleri RSS/Reddit/NewsAPI'den çeken (n8n), Claude ile sentezleyen (FastAPI), ve dashboard + chat ile sunan kişisel kullanım amaçlı agent.

## Kullanıcı
Sadece sahibi (Onat). Tek kullanıcı, Bearer token auth.

## Scope IN
- 3 niche için günlük rapor (trending, news summary, content angles, campaign plan)
- Email YOK; rapor `backend/outputs/report-YYYY-MM-DD.html` olarak diske
- Dashboard: rapor listesi + detay + sources health
- Chat: Claude'un web_search tool'u ile canlı arama yapan SSE streaming agent
- n8n source ingestion (RSS, Reddit RSS, NewsAPI)
- Layered healthchecks (db, llm, n8n)

## Scope OUT
- Multi-user, signup, billing
- Sayısal ROI/bütçe tahmini (hallucination riski)
- Otomatik sosyal medya posting
- Resim/video üretimi
- Mobile app
- Email entegrasyonu (Phase 2)
- pytrends ve Printables scrape (Phase 2 — n8n native source'lar yeterli)

## Tech stack
- Backend: Python 3.11 + FastAPI + SQLAlchemy 2.0 (async) + asyncpg + httpx + pydantic v2
- LLM: Anthropic Claude (`claude-sonnet-4-5`), web_search tool tipi `web_search_20250305`
- Frontend: Next.js 14 App Router + TS + Tailwind + shadcn/ui
- DB: PostgreSQL 16 (Docker)
- Workflow: n8n (Docker)
- Auth: Bearer token

## Niche listesi
1. **football** — dünya futbolu (transferler, maçlar, viral anlar)
2. **sports_toys** — formalar, toplar, branded merch, koleksiyon
3. **3d_printed_toys** — Printables/Reddit trendleri, viral modeller, niş talepler

## Source listesi (n8n'de yapılandırılacak)
- BBC Sport RSS, Goal.com RSS, Eurosport RSS, AA Spor RSS, NTV Spor RSS
- Reddit RSS: r/soccer, r/football, r/3Dprinting, r/functionalprint, r/SoccerJerseys
- NewsAPI (keyword arama, opsiyonel)
- Google Trends RSS (geo=TR, US, GB)

## Hallucination önleme
- Synthesizer schema-constrained (Pydantic)
- `source_signal_ids` her item'da zorunlu, en az 1
- Validation: signal ID gerçek mi? Yoksa retry/drop
- System prompt: sayısal tahmin yasağı
