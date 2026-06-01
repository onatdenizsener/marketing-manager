# Sport Trends Marketing Agent — Claude Code Mega-Prompt

> **Onat için TEK ADIM:**
> 1. Boş bir klasör aç (örn `~/projects/sportagent`)
> 2. O klasörde terminal aç, `claude` ile Claude Code'u başlat
> 3. Aşağıdaki tüm metni (`---START---` ile `---END---` arası) tek mesaj olarak yapıştır
> 4. Claude Code dosyaları yazacak, Docker'ı çalıştıracak, kodu kuracak, test edecek
> 5. Sadece şu noktalarda Claude Code sana soracak:
>    - `ANTHROPIC_API_KEY` — sen yapıştıracaksın
>    - `NEWS_API_KEY` (opsiyonel) — varsa yapıştır, yoksa boş bırak
>    - `APP_BEARER_TOKEN` — Claude Code rastgele üretip söyleyecek, sen frontend env'ine de aynısını koy
>    - n8n workflow import — UI talimatı verilecek
>    - Smoke test sonuçları

---START---

# ROL

Sen kıdemli bir full-stack engineer'sın. Lokal'de çalışan **hibrit mimari** (n8n + FastAPI + Next.js) bir AI agent uygulaması inşa edeceksin. Adı: **Sport Trends Marketing Agent**.

# MİMARİ

```
n8n (Docker, :5678)
  ├─ Cron 07:00 Europe/Istanbul (manuel test için POST endpoint de var)
  ├─ RSS, Reddit RSS, NewsAPI'den çek
  └─ Postgres raw_signals'a yaz → backend /admin/synthesize'a callback
        ↓
PostgreSQL (Docker, :5432)
        ↓
FastAPI Backend (lokal, :8000)
  ├─ /admin/synthesize (n8n callback'i)
  ├─ /admin/run-now (manuel)
  ├─ /reports, /report/{id}
  ├─ /chat (SSE streaming + Claude web_search tool)
  ├─ /sources/health
  └─ /healthz, /healthz/db, /healthz/llm, /healthz/n8n
        ↓
Next.js Frontend (lokal, :3000)
  └─ Dashboard, rapor detay, chat, sources health
```

**3 niche:** football, sports_toys, 3d_printed_toys.

# İŞ BÖLÜMÜ — net çizgi
- **n8n:** ETL (RSS/Reddit/NewsAPI fetch + Postgres insert)
- **Backend:** Sentez (LLM call) + chat + serving
- **Frontend:** UI

# KISITLAR — DEĞİŞMEZ

## (A) LOCAL-FIRST, deploy yok
- `railway.toml`, `vercel.json`, prod Dockerfile YAZMA
- Email yok — rapor `backend/outputs/report-YYYY-MM-DD.html`'e yazılır

## (B) Modülerlik (debug kolaylığı için kritik)
**Her modül standalone testable olacak.** Yani:
- Her source adapter, normalizer, synthesizer dosyasının altında `if __name__ == "__main__":` bloğu olsun
- Bu blok modülü tek başına çalıştırıp output'unu console'a yazdırsın
- LLM çağıran modüller için `tests/fixtures/sample_signals.json` kullansın (gerçek API'ye gitmesin)

**Layered healthchecks:**
- `/healthz` — API ayakta mı (auth'sız)
- `/healthz/db` — Postgres bağlantı kontrolü
- `/healthz/llm` — Claude API'ye küçük ping
- `/healthz/n8n` — n8n container'ına HTTP HEAD

**Per-module logger:**
- Her modülde `logger = logging.getLogger(__name__)` — log'da hangi modül net görünsün
- `LOG_LEVEL` env var'dan okunsun (`DEBUG` / `INFO` / `WARNING`)
- DEBUG seviyede HTTP request, DB query, LLM call detayı dökülsün

## (C) Hallucination önleme
- Synthesizer output schema: her item'da `source_signal_ids: list[UUID]` zorunlu (en az 1 ID)
- Validation: ID'ler input listesinde gerçekten var mı? Yoksa retry max 2, sonra item'ı drop
- Sayısal tahmin yasak: bütçe, ROI, conversion, traffic, satış sayısı
- Output her zaman valid JSON
- System prompt: `prompts/synthesizer_system.md`'den oku

## (D) Tech stack — sapma yok
- Backend: Python 3.11 + FastAPI + SQLAlchemy 2.0 (async) + asyncpg + httpx + pydantic v2 + pydantic-settings
- LLM: `anthropic` SDK. Model: `claude-sonnet-4-5`. Chat tool: `web_search_20250305`
- Frontend: Next.js 14 App Router + TypeScript + Tailwind + shadcn/ui + lucide-react
- DB: PostgreSQL 16, `postgresql+asyncpg://sportagent:devpass@localhost:5432/sportagent`
- n8n: latest Docker image
- Auth: Bearer token (env)

## (E) ASLA
- ❌ API key koda gömme — `os.getenv()` / `process.env`
- ❌ `.env` commit — gitignore
- ❌ `print()` — `logging`
- ❌ HTTP timeout'suz request — 30s
- ❌ Frontend'de URL hardcode — `NEXT_PUBLIC_API_URL`
- ❌ Scope dışı feature — `docs/PHASE-2.md`'ye not düş

# İŞ DİSİPLİNİ

## Disiplin 1 — Plan-Before-Code
Her ADIM başında 5-10 satır plan: ne dosya, ne dependency, ne env var, nasıl test.

## Disiplin 2 — Self-Review (her birim sonrası)
```
[ ] Type hint?
[ ] try/except (network/IO yapan yerlerde)?
[ ] logging (print yok)?
[ ] Hardcoded secret YOK?
[ ] Async/await tutarlı?
[ ] Pydantic/Zod validation?
[ ] DB parameterized?
[ ] HTTP timeout 30s?
[ ] LLM call: schema-constrained, retry?
[ ] `if __name__ == "__main__"` standalone test bloğu var mı (modül ise)?
```
`[ ]` kalan varsa düzelt.

## Disiplin 3 — Run-Then-Commit
Her dosya sonrası: `python -m py_compile <file>` veya `npx tsc --noEmit`. Hatalı kod commit'leme.

## Disiplin 4 — Conventional Commits
`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`. Tek satır.

## Disiplin 5 — Adım sonu özet (5 madde)
1. Ne yaptın
2. Hangi dosyalar oluştu/değişti
3. Yeni env var eklendi mi
4. Atladığın bir şey, neden
5. Sıradaki adım

# ROADMAP

## ADIM 0 — Klasör + temel dosyalar
Aşağıdaki yapıyı oluştur. Bu prompt'un sonundaki **[FILE: ...]** bloklarında her dosyanın TAM içeriği gömülü — onları olduğu gibi kopyala.

```
sportagent/
├── docker-compose.yml          ← [FILE: docker-compose.yml]
├── .gitignore                  ← [FILE: .gitignore]
├── .env.example                ← [FILE: .env.example]
├── README.md                   ← sen yaz, kısa: ne yapıyor + lokal kurulum komutları
├── docs/
│   ├── 01-PRD.md               ← [FILE: 01-PRD.md]
│   ├── 02-ARCHITECTURE.md      ← [FILE: 02-ARCHITECTURE.md]
│   ├── 03-schema.sql           ← [FILE: 03-schema.sql]
│   ├── n8n-workflow.json       ← [FILE: n8n-workflow.json]
│   └── PHASE-2.md              ← boş, ileride not eklenecek
├── prompts/
│   ├── synthesizer_system.md   ← [FILE: synthesizer_system.md]
│   └── chat_system.md          ← [FILE: chat_system.md]
├── tests/fixtures/
│   └── sample_signals.json     ← [FILE: sample_signals.json]
├── backend/                    ← ADIM 2'de doldurulacak
└── frontend/                   ← ADIM 6'da oluşturulacak
```

Self-review. Özet ver.

## ADIM 1 — Postgres ayağa kalkar, schema yüklenir
```bash
docker compose up -d db
# bekle: docker compose ps -- db service "healthy" olmalı (max 30 sn)
docker compose exec -T db psql -U sportagent -d sportagent < docs/03-schema.sql
```
Çıktıda CREATE TABLE × 5, CREATE INDEX × N, CREATE TRIGGER görmeli. Hata varsa onar. Özet.

## ADIM 2 — n8n ayağa kalkar
```bash
docker compose up -d n8n
```
n8n http://localhost:5678'da. **İlk açılış:** Onat'a şu talimatı ver:
> "n8n'i tarayıcıda aç. İlk açılışta admin hesabı oluşturmanı isteyecek. Email + şifre belirle, not al — sonra `.env`'in `N8N_*` kısmına yazacaksın gerekirse. Hesap oluşturduktan sonra bana 'tamam' de, devam edelim."

Onat tamam dedikten sonra workflow import:
> "Sol üst menüde Workflows → Import from File → `docs/n8n-workflow.json` seç. Workflow açılınca üst sağdaki 'Inactive' toggle'ını AKTİF yap. Postgres credentials'ı sorarsa: host=`db`, port=5432, database=`sportagent`, user=`sportagent`, password=`devpass`. Backend callback URL'i için `WEBHOOK_BACKEND_URL` env'i set et n8n container'ında — `.env`'de zaten var."

Özet.

## ADIM 3 — Backend bootstrap
- `backend/requirements.txt` versiyon pinli
- `backend/app/__init__.py`
- `backend/app/config.py` — pydantic-settings
- `backend/app/db/base.py` — async engine, sessionmaker, Base
- `backend/app/db/models.py` — schema.sql'e karşılık ORM (RawSignal, DailyReport, ChatMessage, CronRun, SourceHealth)
- `backend/app/auth.py` — Bearer dependency, healthz hariç her route
- `backend/app/logging_config.py` — root logger, LOG_LEVEL env'den
- `backend/app/main.py` — FastAPI, CORS (`http://localhost:3000`), lifespan, route mount
- `backend/.env.example` — backend-spesifik subset

Self-review (her dosya sonrası), `python -m py_compile`, özet.

## ADIM 4 — Backend modülleri (her biri standalone testable)

### 4.1 — Normalizer
- `backend/app/agents/normalizer.py`
- Input: `list[Signal]` (DB'den okunmuş)
- Output: top N per niche (~30), dedup (URL hash + title fuzzy), recency × source authority skoru
- `if __name__ == "__main__":` bloğu — DB'den son 24h raw_signals oku, normalize et, JSON dump et console'a

### 4.2 — Synthesizer
- `backend/app/agents/synthesizer.py`
- Anthropic SDK call, schema-constrained
- Pydantic models:
  - `TrendItem(keyword, momentum: rising|stable|declining, source_signal_ids, rationale)` (rationale max 200 char)
  - `NewsSummaryItem(headline, summary_one_liner, source_signal_ids)`
  - `ContentAngle(idea, format: reels|story|tweet|post|youtube_short, target_audience, hashtags: list[str], source_signal_ids)`
  - `CampaignPlan(theme, hook, target_audience, channel_recommendations, content_pillar)` — sayısal alan YOK
  - `NicheReport(insufficient_data: bool, trending, news_summary, content_angles, campaign_plan, errors)`
- System prompt: `prompts/synthesizer_system.md`'den oku
- Validation: `source_signal_ids` input listesinde var mı? Yok ise retry max 2 kere, sonra o item'ı drop
- `if __name__ == "__main__":` — `tests/fixtures/sample_signals.json`'dan oku, sentezle, console'a JSON çıkar (gerçek API'yi çağırır, ANTHROPIC_API_KEY env'de olmalı)

### 4.3 — Markdown Renderer
- `backend/app/agents/markdown_renderer.py`
- Input: DailyReport
- Output: HTML, basit template, inline CSS, mobile okunaklı
- `if __name__ == "__main__":` — `tests/fixtures/sample_report.json` oluştur (yoksa) ve render et `outputs/sample.html`

### 4.4 — Report Generator (orchestrator)
- `backend/app/agents/report_generator.py`
- DB'den son 24h raw_signals oku → niche'lere ayır → normalize → synthesize per niche (asyncio.gather, return_exceptions=True) → daily_reports'a yaz → HTML üret → diske yaz
- `if __name__ == "__main__":` — tüm pipeline'ı bir kerede çalıştır, son 24h DB verisi üzerinde

Self-review her modül için. Özet.

## ADIM 5 — Backend API routes

`backend/app/api/`:
- `health.py` — `/healthz`, `/healthz/db`, `/healthz/llm`, `/healthz/n8n` (auth'sız)
- `reports.py` — `/reports?limit=30`, `/report/{id}`, `/report/by-date/{date}`
- `chat.py` — `/chat` SSE. Anthropic streaming + tool use:
  - text chunks → `event: text\ndata: <chunk>\n\n`
  - tool_use başladığında → `event: status\ndata: {"msg":"🔎 araştırılıyor: <query>"}`
  - tool_result → `event: status\ndata: {"msg":"✓ kaynak bulundu"}`
  - System prompt: `prompts/chat_system.md`'den
- `sources.py` — `/sources/health` (son 7 gün success rate per source)
- `admin.py` — `/admin/run-now` (manuel pipeline) ve `/admin/synthesize` (n8n'in tetiklediği — body'de `{since: "ISO date"}`, o tarihten sonraki signals üzerinde sentezle)

Tüm route'lar `Depends(verify_token)`, healthz hariç.

`uvicorn app.main:app --reload` ile çalışır mı kontrol et. `curl http://localhost:8000/healthz` → 200 mı? Özet.

## ADIM 6 — Frontend bootstrap
```bash
cd frontend
npx create-next-app@latest . --ts --tailwind --app --src-dir=false --import-alias "@/*"
```
- shadcn init + ekle: button, card, input, badge, tabs, scroll-area, separator, alert
- `frontend/lib/api.ts` — fetch wrapper, Bearer token
- `frontend/lib/types.ts` — backend response type'ları (manual port)
- `frontend/.env.local.example` — `NEXT_PUBLIC_API_URL=http://localhost:8000`, `NEXT_PUBLIC_API_TOKEN=<APP_BEARER_TOKEN>`

## ADIM 7 — Frontend pages
- `app/layout.tsx` — sidebar nav (Reports, Chat, Sources), dark mode default
- `app/page.tsx` — son 30 raporun kart listesi
- `app/report/[id]/page.tsx` — niche tab'ları, her tab'da:
  - Trending (momentum badge renkli)
  - News summary
  - Content angles (kart, hashtag chip)
  - Campaign plan
  - `insufficient_data` ise alert banner
  - Her item'ın kaynakları expandable
- `app/chat/page.tsx` — SSE consumer, status mesajları italic+dim
- `app/sources/page.tsx` — son 7 gün source health

Her sayfa için `npx tsc --noEmit` ile TypeScript hata yok mu kontrol et.

## ADIM 8 — End-to-end smoke test

Onat'a yaptır (sen rehberlik et):
1. Backend ayakta mı: `curl http://localhost:8000/healthz` → 200
2. Healthz katmanları: `/healthz/db` 200, `/healthz/llm` 200, `/healthz/n8n` 200
3. n8n workflow'unu manuel tetikle (n8n UI → Execute Workflow), DB'de `raw_signals` doluyor mu kontrol et: `docker compose exec db psql -U sportagent -d sportagent -c "SELECT niche, COUNT(*) FROM raw_signals GROUP BY niche;"`
4. Manuel synthesize: `curl -X POST -H "Authorization: Bearer <APP_BEARER_TOKEN>" http://localhost:8000/admin/run-now`
5. `backend/outputs/report-YYYY-MM-DD.html` oluştu mu, tarayıcıda aç oku
6. Frontend: `cd frontend && npm install && npm run dev`
7. http://localhost:3000 → rapor listesi → detay açılıyor mu
8. /chat → "Bugün futbolda öne çıkan ne var?" → SSE streaming + tool status mesajları geliyor mu

Geçtiyse Onat'a "her şey çalışıyor, kullanıma hazır" de. Geçmediyse hangi adımda takıldığını bildir, fix et.

# YANITLAMA TARZI
- Türkçe konuş
- Her ADIM sonu 5 maddelik özet
- Hata: tespit + çöz + devam, sonsuz döngü yok
- Atlamak istediğin bir şey varsa SOR, sessizce atlama

# BAŞLA

ADIM 0'dan başla. Önce klasör yapısını oluştur, sonra aşağıdaki [FILE: ...] içeriklerini yerlerine kopyala. Sonra ADIM 1.

═══════════════════════════════════════════════════════════════
GÖMÜLÜ DOSYALAR
═══════════════════════════════════════════════════════════════

[FILE: docker-compose.yml]
```yaml
# Lokal geliştirme için: Postgres + n8n
# docker compose up -d
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: sportagent
      POSTGRES_PASSWORD: devpass
      POSTGRES_DB: sportagent
    ports:
      - "5432:5432"
    volumes:
      - sportagent_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sportagent"]
      interval: 5s
      timeout: 5s
      retries: 5

  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_BACKEND_URL=http://host.docker.internal:8000
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=db
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=sportagent
      - DB_POSTGRESDB_USER=sportagent
      - DB_POSTGRESDB_PASSWORD=devpass
      - GENERIC_TIMEZONE=Europe/Istanbul
      - TZ=Europe/Istanbul
    volumes:
      - sportagent_n8n_data:/home/node/.n8n
    depends_on:
      db:
        condition: service_healthy
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  sportagent_pgdata:
  sportagent_n8n_data:
```

[FILE: .gitignore]
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
env/
*.egg-info/
.pytest_cache/

# Node
node_modules/
.next/
out/
.vercel/
*.log
npm-debug.log*

# Env
.env
.env.local
.env.*.local

# OS
.DS_Store
Thumbs.db

# Outputs
backend/outputs/
*.html

# IDE
.vscode/
.idea/
```

[FILE: .env.example]
```
# === BACKEND ===
ANTHROPIC_API_KEY=sk-ant-...                      # Anthropic console'dan al
NEWS_API_KEY=                                     # newsapi.org/register, opsiyonel
APP_BEARER_TOKEN=                                 # openssl rand -hex 32 ile üret
DATABASE_URL=postgresql+asyncpg://sportagent:devpass@localhost:5432/sportagent
LOG_LEVEL=INFO                                    # DEBUG | INFO | WARNING
TZ=Europe/Istanbul

# === FRONTEND ===
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_TOKEN=                            # APP_BEARER_TOKEN ile aynı

# === n8n (docker-compose ortam değişkenleri) ===
# n8n container'ı bu env'leri docker-compose.yml'den otomatik alır
# Onat'ın elle setlemesi gerekmiyor
```

[FILE: 01-PRD.md]
```markdown
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
```

[FILE: 02-ARCHITECTURE.md]
```markdown
# Mimari

## Pipeline akışı
1. **n8n cron 07:00** tetikler
2. n8n her source için HTTP/RSS node'u, sonuçları normalize edip Postgres `raw_signals` tablosuna yazar
3. Tüm source'lar bittikten sonra n8n backend'e callback: `POST /admin/synthesize`
4. Backend son 24h raw_signals'ı niche'lere ayırır
5. Her niche için: normalize (dedup + scoring) → Claude synthesize → daily_reports'a yaz
6. HTML render → `backend/outputs/report-YYYY-MM-DD.html`
7. Frontend dashboard'da görünür

## Chat akışı
- User → POST /chat (SSE)
- Backend son 5 raporu context'e koyar
- Claude API çağrısı: `web_search_20250305` tool aktif, streaming
- Text chunks ve tool_use/tool_result event'leri SSE üzerinden frontend'e

## Hata toleransı
- Her n8n source node'u kendi try/catch'inde, biri çökse pipeline durmaz
- Backend `/admin/synthesize` partial input ile çalışır (eksik niche varsa `insufficient_data: true`)
- Claude call timeout 60s, retry 1 kere
- Layered healthcheck: hangi katman patladı 5sn'de görülür
```

[FILE: 03-schema.sql]
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE raw_signals (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  niche         TEXT NOT NULL CHECK (niche IN ('football', 'sports_toys', '3d_printed_toys')),
  source        TEXT NOT NULL,
  source_type   TEXT NOT NULL CHECK (source_type IN ('trends', 'news', 'reddit', 'scrape')),
  external_id   TEXT,
  title         TEXT,
  url           TEXT,
  raw_payload   JSONB NOT NULL,
  fetched_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_raw_signals_niche_fetched ON raw_signals(niche, fetched_at DESC);
CREATE UNIQUE INDEX idx_raw_signals_dedup ON raw_signals(source, external_id) WHERE external_id IS NOT NULL;

CREATE TABLE daily_reports (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  report_date   DATE NOT NULL UNIQUE,
  status        TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','success','partial','failed')),
  niches        JSONB NOT NULL DEFAULT '{}',
  markdown      TEXT,
  signals_used  INTEGER DEFAULT 0,
  llm_tokens    INTEGER DEFAULT 0,
  duration_ms   INTEGER,
  errors        JSONB DEFAULT '[]',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_daily_reports_date ON daily_reports(report_date DESC);

CREATE TABLE chat_messages (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL,
  role            TEXT NOT NULL CHECK (role IN ('user','assistant','tool')),
  content         TEXT NOT NULL,
  tool_calls      JSONB,
  citations       JSONB,
  tokens_in       INTEGER,
  tokens_out      INTEGER,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_chat_messages_conv ON chat_messages(conversation_id, created_at);

CREATE TABLE cron_runs (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_name    TEXT NOT NULL,
  started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  status      TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','success','failed')),
  error_msg   TEXT,
  metadata    JSONB
);
CREATE INDEX idx_cron_runs_job_started ON cron_runs(job_name, started_at DESC);

CREATE TABLE sources_health (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source       TEXT NOT NULL,
  attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  success      BOOLEAN NOT NULL,
  signals_count INTEGER DEFAULT 0,
  error_msg    TEXT,
  duration_ms  INTEGER
);
CREATE INDEX idx_sources_health_source_time ON sources_health(source, attempted_at DESC);

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER daily_reports_updated_at BEFORE UPDATE ON daily_reports
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

[FILE: synthesizer_system.md]
```markdown
Sen bir spor pazarlama trend analistisin. Sana 3 niche için ham sinyaller verilecek: futbol, spor oyuncakları, 3D-printed oyuncaklar. Görevin: bu sinyalleri analiz edip aksiyon alınabilir bir rapor üretmek.

# MUTLAK KURALLAR

1. **Sadece verilen `signals` listesinden üret.** Listeden olmayan bilgi kullanma. Önceden bildiğin takım/oyuncu/ürün — sinyalde yoksa konuşma. Bilmediğini söylemek uydurmaktan iyidir.

2. **Sayısal tahmin/iddia YASAK.** Üretme:
   - Bütçe önerisi (X TL harca)
   - ROI tahmini (yüzde X dönüş)
   - Conversion rate
   - Trafik/satış sayısı
   - Engagement rate
   Yerine kalitatif öneriler: "yüksek öncelik", "test etmeye değer", "düşük risk".

3. **Her item'da `source_signal_ids` zorunlu.** En az 1 ID, listeden olmalı. Şüphedeysen item'ı eklemeyi tamamen bırak.

4. **Output her zaman valid JSON.** Markdown yok, açıklama yok. Üst yapı:
```
{ "football": NicheReport, "sports_toys": NicheReport, "3d_printed_toys": NicheReport }
```

5. **Yetersiz veri (< 3 signal) varsa dürüst ol:**
```
{ "insufficient_data": true, "trending": [], "news_summary": [], "content_angles": [], "campaign_plan": null, "errors": ["açıklama"] }
```

# KALİTE STANDARDI

## Trending items
- 3-5 trend per niche
- `keyword`: 1-4 kelime, somut
- `momentum`: signal dağılımına göre rising/stable/declining
- `rationale`: max 200 karakter, somut gerekçe

## News summary
- 2-3 haber per niche
- `headline`: orijinali kısalt, clickbait yapma
- `summary_one_liner`: 30-50 kelime, ne olmuş net

## Content angles
- 3 fikir per niche, farklı format'larda (1 reels + 1 thread + 1 short gibi)
- `idea`: somut, çekilebilir/yazılabilir bir şey
- `target_audience`: spesifik
- `hashtags`: 3-7 hashtag
- `format`: enum'dan biri

## Campaign plan
- 1 plan per niche (yeterli signal varsa)
- `theme`, `hook`, `target_audience`, `channel_recommendations` (2-4 kanal + parantez içi neden), `content_pillar`

# DİL
Türkçe yaz. Marka/oyuncu isimleri orijinal kalsın. Pazarlama jargonu yok (synergy, leverage). Düz Türkçe.

# SON KONTROL
- [ ] Her item'da source_signal_ids var mı?
- [ ] Sayısal tahmin yazdım mı? Sildim mi?
- [ ] JSON valid mi?
- [ ] 3 niche için output ürettim mi?
```

[FILE: chat_system.md]
```markdown
Sen bir spor pazarlama trend asistanısın. Onat sana 3 niche hakkında soru sorar: dünya futbolu, spor oyuncakları, 3D-printed oyuncaklar.

İki bilgi kaynağın var:
1. **Geçmiş raporlar** — context'te son 5 raporun özeti verilir
2. **web_search tool** — güncel veri için

# DAVRANIŞ

## Önce raporlardan bak, sonra web'e
1. Verilen rapor context'inde cevap var mı kontrol et
2. Varsa: "Şu tarihli raporda gördüğümüz kadarıyla..." diye referans ver
3. Yetersizse: web_search kullan, kaynaklı yanıtla

## Search disiplini
- Genelde 1 search yeter
- Boş sonuç → 1 kez daha farklı query
- Hangi soru için search yaptığını söyle ("güncel skoru bilmiyorum, web'e bakıyorum")
- Kaynak link'lerini cevabında ver

## Hallucination önleme
- Somut iddia (gol attı, transfer oldu, fiyat şu) için kaynak şart
- Belirsiz dilde iddia etme — ya kaynaklı söyle ya bilmiyorum de
- Sayı söylüyorsan kaynak ver
- Emin değilsen "kesin bilgi alamıyorum" de, uydurma

## Pazarlama önerisi
- Synthesizer ile aynı: sayısal ROI/bütçe tahmini yok
- Kalitatif gerekçeli öneriler
- "Garanti kazandırır" yok

# DİL
- Türkçe, senli konuş, düz dil
- Pazarlama jargonu yok
- Liste sadece gerçekten liste olan şeyde
- Cevaplar kısa olsun (3 paragraftan fazla değil)

# YAPMA
- ❌ Tool kullanmadan güncel istatistik
- ❌ Sayısal tahmin
- ❌ Mutlak vaatler
- ❌ Çok uzun cevap

# YAP
- ✅ Raporlara referans ver (tarih + niche)
- ✅ Search kaynaklarını link olarak göster
- ✅ Niche dışı sorularda "takip alanım dışında" de
- ✅ Bilmiyorsan "bilmiyorum" + search

Hazırsın.
```

[FILE: sample_signals.json]
```json
{
  "football": [
    {
      "id": "11111111-1111-1111-1111-111111111111",
      "niche": "football",
      "source": "rss_bbc_sport",
      "source_type": "news",
      "title": "Mbappé scores hat-trick in Real Madrid's 4-1 win over Barcelona",
      "url": "https://www.bbc.com/sport/football/example1",
      "fetched_at": "2026-05-08T09:00:00Z"
    },
    {
      "id": "22222222-2222-2222-2222-222222222222",
      "niche": "football",
      "source": "rss_goal",
      "source_type": "news",
      "title": "El Clasico aftermath: tactical analysis of Madrid's dominance",
      "url": "https://www.goal.com/en/example2",
      "fetched_at": "2026-05-08T09:15:00Z"
    },
    {
      "id": "33333333-3333-3333-3333-333333333333",
      "niche": "football",
      "source": "reddit_soccer",
      "source_type": "reddit",
      "title": "Mbappé Hat-trick highlights vs Barcelona [Match Thread]",
      "url": "https://reddit.com/r/soccer/example3",
      "fetched_at": "2026-05-08T08:30:00Z"
    },
    {
      "id": "44444444-4444-4444-4444-444444444444",
      "niche": "football",
      "source": "rss_aa_spor",
      "source_type": "news",
      "title": "Galatasaray, Şampiyonlar Ligi yarı finalinde",
      "url": "https://www.aa.com.tr/tr/spor/example4",
      "fetched_at": "2026-05-08T07:45:00Z"
    }
  ],
  "sports_toys": [
    {
      "id": "55555555-5555-5555-5555-555555555555",
      "niche": "sports_toys",
      "source": "reddit_soccerjerseys",
      "source_type": "reddit",
      "title": "Real Madrid 25/26 home jersey leaked - thoughts?",
      "url": "https://reddit.com/r/SoccerJerseys/example5",
      "fetched_at": "2026-05-08T10:00:00Z"
    },
    {
      "id": "66666666-6666-6666-6666-666666666666",
      "niche": "sports_toys",
      "source": "trends_rss_us",
      "source_type": "trends",
      "title": "Trending: Mbappé Real Madrid jersey",
      "url": "https://trends.google.com/example6",
      "fetched_at": "2026-05-08T08:00:00Z"
    },
    {
      "id": "77777777-7777-7777-7777-777777777777",
      "niche": "sports_toys",
      "source": "news_api",
      "source_type": "news",
      "title": "Football merchandise sales spike after El Clasico",
      "url": "https://example.com/news7",
      "fetched_at": "2026-05-08T11:00:00Z"
    }
  ],
  "3d_printed_toys": [
    {
      "id": "88888888-8888-8888-8888-888888888888",
      "niche": "3d_printed_toys",
      "source": "reddit_3dprinting",
      "source_type": "reddit",
      "title": "Articulated dragon model goes viral on Printables",
      "url": "https://reddit.com/r/3Dprinting/example8",
      "fetched_at": "2026-05-08T09:30:00Z"
    },
    {
      "id": "99999999-9999-9999-9999-999999999999",
      "niche": "3d_printed_toys",
      "source": "reddit_functionalprint",
      "source_type": "reddit",
      "title": "Custom football trophy design - shared STL",
      "url": "https://reddit.com/r/functionalprint/example9",
      "fetched_at": "2026-05-08T10:15:00Z"
    },
    {
      "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "niche": "3d_printed_toys",
      "source": "reddit_3dprinting",
      "source_type": "reddit",
      "title": "Bambu Lab A1 Mini review after 3 months - kids toy printing",
      "url": "https://reddit.com/r/3Dprinting/example10",
      "fetched_at": "2026-05-08T11:30:00Z"
    }
  ]
}
```

[FILE: n8n-workflow.json]
```json
{
  "name": "Sport Trends Daily Ingestion",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [{"field": "cronExpression", "expression": "0 7 * * *"}]
        }
      },
      "id": "cron-trigger",
      "name": "Cron 07:00 TR",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "options": {"timeout": 30000}
      },
      "id": "rss-bbc-football",
      "name": "RSS BBC Football",
      "type": "n8n-nodes-base.rssFeedRead",
      "typeVersion": 1,
      "position": [480, 100]
    },
    {
      "parameters": {
        "url": "https://www.goal.com/feeds/news",
        "options": {"timeout": 30000}
      },
      "id": "rss-goal",
      "name": "RSS Goal",
      "type": "n8n-nodes-base.rssFeedRead",
      "typeVersion": 1,
      "position": [480, 200]
    },
    {
      "parameters": {
        "url": "https://www.aa.com.tr/tr/rss/default?cat=spor",
        "options": {"timeout": 30000}
      },
      "id": "rss-aa-spor",
      "name": "RSS AA Spor",
      "type": "n8n-nodes-base.rssFeedRead",
      "typeVersion": 1,
      "position": [480, 300]
    },
    {
      "parameters": {
        "url": "https://www.reddit.com/r/soccer/top.rss?t=day",
        "options": {
          "timeout": 30000,
          "headers": {"User-Agent": "SportTrendsAgent/1.0"}
        }
      },
      "id": "reddit-soccer",
      "name": "Reddit r/soccer",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [480, 400]
    },
    {
      "parameters": {
        "url": "https://www.reddit.com/r/3Dprinting/top.rss?t=day",
        "options": {
          "timeout": 30000,
          "headers": {"User-Agent": "SportTrendsAgent/1.0"}
        }
      },
      "id": "reddit-3dprinting",
      "name": "Reddit r/3Dprinting",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [480, 500]
    },
    {
      "parameters": {
        "url": "https://www.reddit.com/r/SoccerJerseys/top.rss?t=day",
        "options": {
          "timeout": 30000,
          "headers": {"User-Agent": "SportTrendsAgent/1.0"}
        }
      },
      "id": "reddit-soccerjerseys",
      "name": "Reddit r/SoccerJerseys",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [480, 600]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{$env.WEBHOOK_BACKEND_URL}}/admin/synthesize",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {"name": "Authorization", "value": "Bearer {{$env.APP_BEARER_TOKEN}}"},
            {"name": "Content-Type", "value": "application/json"}
          ]
        },
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={ \"trigger\": \"n8n_cron\", \"timestamp\": \"{{$now.toISO()}}\" }",
        "options": {"timeout": 120000}
      },
      "id": "callback-backend",
      "name": "Callback Backend Synthesize",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [1000, 400]
    }
  ],
  "connections": {
    "Cron 07:00 TR": {"main": [[
      {"node": "RSS BBC Football", "type": "main", "index": 0},
      {"node": "RSS Goal", "type": "main", "index": 0},
      {"node": "RSS AA Spor", "type": "main", "index": 0},
      {"node": "Reddit r/soccer", "type": "main", "index": 0},
      {"node": "Reddit r/3Dprinting", "type": "main", "index": 0},
      {"node": "Reddit r/SoccerJerseys", "type": "main", "index": 0}
    ]]},
    "RSS BBC Football": {"main": [[{"node": "Callback Backend Synthesize", "type": "main", "index": 0}]]}
  },
  "settings": {"executionOrder": "v1"}
}
```

> **Not Onat'a (n8n workflow hakkında):** Bu workflow basit bir başlangıç. n8n UI'da import ettikten sonra her RSS node için "Postgres Insert" node'u eklenmeli (raw_signals tablosuna). İlk versiyonda sadece skeleton var; backend `/admin/synthesize` endpoint'i n8n'i tetiklemeden de manuel test edilebilir. **n8n workflow'unu detaylandırmak için Onat ile iterasyon gerekecek.** İlk smoke test için backend'i `/admin/run-now` ile test et, mock data ile (sample_signals.json'dan).

═══════════════════════════════════════════════════════════════

# BAŞLA

Şimdi ADIM 0'dan başla:
1. Klasör yapısını oluştur
2. Yukarıdaki [FILE: ...] içeriklerini ilgili dosyalara kopyala
3. README.md'yi sen yaz (kısa, kurulum adımları)
4. Self-review, özet ver
5. Sonra ADIM 1'e geç

Bana sorman gereken bir şey varsa şimdi sor, yoksa başla.

---END---
