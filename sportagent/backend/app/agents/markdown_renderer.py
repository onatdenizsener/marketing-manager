import logging
import os
from datetime import date
from app.agents.synthesizer import NicheReport

logger = logging.getLogger(__name__)

MOMENTUM_COLORS = {
    "rising": "#22c55e",
    "stable": "#f59e0b",
    "declining": "#ef4444",
}

NICHE_LABELS = {
    "football": "Futbol",
    "sports_toys": "Spor Oyuncakları",
    "3d_printed_toys": "3D Oyuncaklar",
}


def _niche_section(niche: str, report: NicheReport) -> str:
    label = NICHE_LABELS.get(niche, niche)
    parts = [f'<section class="niche"><h2>{label}</h2>']

    if report.insufficient_data:
        errors = "; ".join(report.errors) if report.errors else "Yeterli veri yok"
        parts.append(f'<div class="alert">⚠️ Yetersiz veri: {errors}</div>')
        parts.append("</section>")
        return "\n".join(parts)

    if report.trending:
        parts.append('<div class="card"><h3>Trendler</h3><ul>')
        for t in report.trending:
            color = MOMENTUM_COLORS.get(t.momentum, "#6b7280")
            parts.append(
                f'<li><span class="badge" style="background:{color}">{t.momentum}</span>'
                f' <strong>{t.keyword}</strong> — {t.rationale}</li>'
            )
        parts.append("</ul></div>")

    if report.news_summary:
        parts.append('<div class="card"><h3>Gündem</h3><ul>')
        for n in report.news_summary:
            parts.append(f'<li><strong>{n.headline}</strong><br>{n.summary_one_liner}</li>')
        parts.append("</ul></div>")

    if report.content_angles:
        parts.append('<div class="card"><h3>İçerik Fikirleri</h3>')
        for c in report.content_angles:
            tags = " ".join(f'<span class="tag">{h}</span>' for h in c.hashtags)
            parts.append(
                f'<div class="angle"><span class="format-badge">{c.format}</span>'
                f' <strong>{c.idea}</strong>'
                f'<br><em>Hedef: {c.target_audience}</em>'
                f'<br>{tags}</div>'
            )
        parts.append("</div>")

    if report.campaign_plan:
        cp = report.campaign_plan
        channels = ", ".join(cp.channel_recommendations)
        parts.append(
            f'<div class="card"><h3>Kampanya Planı</h3>'
            f'<p><strong>Tema:</strong> {cp.theme}</p>'
            f'<p><strong>Hook:</strong> {cp.hook}</p>'
            f'<p><strong>Hedef Kitle:</strong> {cp.target_audience}</p>'
            f'<p><strong>Kanallar:</strong> {channels}</p>'
            f'<p><strong>İçerik Pilonu:</strong> {cp.content_pillar}</p>'
            f'</div>'
        )

    parts.append("</section>")
    return "\n".join(parts)


def render_html(report_date: date, niches: dict[str, NicheReport]) -> str:
    sections = "\n".join(_niche_section(k, v) for k, v in niches.items())
    date_str = report_date.strftime("%d %B %Y")

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sport Trends — {date_str}</title>
<style>
  :root {{ --bg:#0f172a;--surface:#1e293b;--border:#334155;--text:#e2e8f0;--muted:#94a3b8 }}
  body {{ background:var(--bg);color:var(--text);font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:1.5rem }}
  h1 {{ font-size:1.5rem;margin-bottom:2rem }}
  h2 {{ font-size:1.2rem;border-bottom:1px solid var(--border);padding-bottom:.5rem }}
  h3 {{ font-size:1rem;color:var(--muted);margin-bottom:.5rem }}
  .card {{ background:var(--surface);border:1px solid var(--border);border-radius:.5rem;padding:1rem;margin-bottom:1rem }}
  .badge,.format-badge {{ display:inline-block;padding:.1rem .5rem;border-radius:999px;font-size:.75rem;color:#fff;margin-right:.5rem }}
  .format-badge {{ background:#6366f1 }}
  .tag {{ display:inline-block;background:var(--border);padding:.1rem .4rem;border-radius:.25rem;font-size:.7rem;margin:.1rem }}
  .alert {{ background:#7f1d1d;border:1px solid #dc2626;padding:.75rem;border-radius:.5rem;margin-bottom:1rem }}
  ul {{ padding-left:1.25rem }}
  li {{ margin-bottom:.5rem }}
  .angle {{ background:var(--surface);border:1px solid var(--border);border-radius:.5rem;padding:.75rem;margin-bottom:.75rem }}
  .niche {{ margin-bottom:2rem }}
</style>
</head>
<body>
<h1>Sport Trends — {date_str}</h1>
{sections}
</body>
</html>"""


if __name__ == "__main__":
    import json
    import sys
    import os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    from app.logging_config import setup_logging
    setup_logging()

    fixture_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "tests", "fixtures", "sample_report.json"
    )

    if not os.path.exists(fixture_path):
        sample = {
            "football": {
                "insufficient_data": False,
                "trending": [{"keyword": "Mbappé hat-trick", "momentum": "rising", "source_signal_ids": ["11111111-1111-1111-1111-111111111111"], "rationale": "El Clasico'da 3 gol atarak viral oldu"}],
                "news_summary": [{"headline": "Madrid 4-1 Barcelona", "summary_one_liner": "Mbappé üç golle Real Madrid'in galibiyetine öncülük etti.", "source_signal_ids": ["11111111-1111-1111-1111-111111111111"]}],
                "content_angles": [{"idea": "Mbappé'nin gollerini Türk yorumuyla reels formatında hazırla", "format": "reels", "target_audience": "Türk futbol taraftarları", "hashtags": ["#Mbappe", "#ElClasico", "#RealMadrid"], "source_signal_ids": ["11111111-1111-1111-1111-111111111111"]}],
                "campaign_plan": {"theme": "El Clasico etkisi", "hook": "Madrid'in şov gecesi", "target_audience": "18-35 yaş futbol takipçileri", "channel_recommendations": ["Instagram (görsel içerik)", "TikTok (kısa video)"], "content_pillar": "Futbol anlık reaksiyon"},
                "errors": []
            },
            "sports_toys": {"insufficient_data": True, "trending": [], "news_summary": [], "content_angles": [], "campaign_plan": None, "errors": ["Test verisi"]},
            "3d_printed_toys": {"insufficient_data": True, "trending": [], "news_summary": [], "content_angles": [], "campaign_plan": None, "errors": ["Test verisi"]}
        }
        os.makedirs(os.path.dirname(fixture_path), exist_ok=True)
        with open(fixture_path, "w", encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False, indent=2)
        print(f"Created fixture: {fixture_path}")

    with open(fixture_path, encoding="utf-8") as f:
        raw = json.load(f)

    niches = {k: NicheReport.model_validate(v) for k, v in raw.items()}
    html = render_html(date.today(), niches)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sample.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Rendered: {out_path}")
