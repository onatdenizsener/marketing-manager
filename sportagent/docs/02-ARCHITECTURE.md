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
