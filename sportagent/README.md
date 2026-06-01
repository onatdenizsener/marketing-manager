# Sport Trends Marketing Agent

Futbol, spor oyuncakları ve 3D-printed oyuncak nişlerinde günlük trend raporu üreten, Claude destekli lokal AI agent.

## Ne yapar
- Her sabah 07:00'de n8n RSS/Reddit/NewsAPI'den veri çeker
- FastAPI backend Claude ile sentezler, HTML rapor üretir
- Next.js dashboard'da raporları ve chat arayüzünü sunar

## Gereksinimler
- Docker + Docker Compose
- Python 3.11
- Node.js 18+
- Anthropic API key

## Lokal kurulum

### 1. Env dosyasını hazırla
```bash
cp .env.example .env
# .env içinde ANTHROPIC_API_KEY ve APP_BEARER_TOKEN doldur
# APP_BEARER_TOKEN üretmek için: openssl rand -hex 32
```

### 2. Docker servisleri başlat
```bash
docker compose up -d
# db + n8n ayağa kalkar
```

### 3. Postgres schema yükle
```bash
docker compose exec -T db psql -U sportagent -d sportagent < docs/03-schema.sql
```

### 4. Backend başlat
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://localhost:8000
```

### 5. Frontend başlat
```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

### 6. n8n workflow import
- http://localhost:5678 aç
- Admin hesabı oluştur
- Workflows → Import from File → `docs/n8n-workflow.json`
- Workflow'u aktif et

## Hızlı test
```bash
# API ayakta mı?
curl http://localhost:8000/healthz

# Manuel pipeline tetikle
curl -X POST -H "Authorization: Bearer <APP_BEARER_TOKEN>" http://localhost:8000/admin/run-now
```

## Klasör yapısı
```
sportagent/
├── docker-compose.yml   # Postgres + n8n
├── docs/                # PRD, mimari, schema, n8n workflow
├── prompts/             # LLM system prompt'ları
├── tests/fixtures/      # Test verisi
├── backend/             # FastAPI uygulaması
└── frontend/            # Next.js uygulaması
```
