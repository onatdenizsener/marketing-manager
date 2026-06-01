"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getReport } from "@/lib/api";
import type { DailyReport, NicheReport, Momentum, ContentFormat } from "@/lib/types";

const MOMENTUM_COLORS: Record<Momentum, string> = {
  rising: "bg-green-600",
  stable: "bg-yellow-600",
  declining: "bg-red-600",
};

const FORMAT_COLORS: Record<ContentFormat, string> = {
  reels: "bg-purple-600",
  story: "bg-pink-600",
  tweet: "bg-sky-600",
  post: "bg-blue-600",
  youtube_short: "bg-red-700",
};

const NICHE_LABELS: Record<string, string> = {
  football: "Futbol",
  sports_toys: "Spor Oyuncakları",
  "3d_printed_toys": "3D Oyuncaklar",
};

function NicheTab({ report }: { report: NicheReport }) {
  if (report.insufficient_data) {
    return (
      <Alert variant="destructive" className="mt-4">
        <AlertDescription>
          Yetersiz veri: {report.errors.join(", ") || "Bilinmeyen hata"}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4 mt-4">
      {report.trending.length > 0 && (
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Trendler</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {report.trending.map((t, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <Badge className={`${MOMENTUM_COLORS[t.momentum]} text-white text-xs shrink-0 mt-0.5`}>{t.momentum}</Badge>
                  <div>
                    <span className="font-medium">{t.keyword}</span>
                    <span className="text-muted-foreground"> — {t.rationale}</span>
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {report.news_summary.length > 0 && (
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Gündem</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {report.news_summary.map((n, i) => (
                <li key={i} className="text-sm">
                  <p className="font-medium">{n.headline}</p>
                  <p className="text-muted-foreground">{n.summary_one_liner}</p>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {report.content_angles.length > 0 && (
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">İçerik Fikirleri</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {report.content_angles.map((c, i) => (
              <div key={i} className="border border-border rounded-md p-3 text-sm space-y-1">
                <div className="flex items-center gap-2">
                  <Badge className={`${FORMAT_COLORS[c.format] ?? "bg-zinc-600"} text-white text-xs`}>{c.format}</Badge>
                  <span className="font-medium">{c.idea}</span>
                </div>
                <p className="text-muted-foreground text-xs">Hedef: {c.target_audience}</p>
                <div className="flex flex-wrap gap-1">
                  {c.hashtags.map((h) => (
                    <span key={h} className="bg-muted text-xs px-1.5 py-0.5 rounded">{h}</span>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {report.campaign_plan && (
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Kampanya Planı</CardTitle></CardHeader>
          <CardContent className="text-sm space-y-2">
            <p><span className="text-muted-foreground">Tema:</span> {report.campaign_plan.theme}</p>
            <p><span className="text-muted-foreground">Hook:</span> {report.campaign_plan.hook}</p>
            <p><span className="text-muted-foreground">Hedef:</span> {report.campaign_plan.target_audience}</p>
            <p><span className="text-muted-foreground">Kanallar:</span> {report.campaign_plan.channel_recommendations.join(", ")}</p>
            <p><span className="text-muted-foreground">İçerik Pilonu:</span> {report.campaign_plan.content_pillar}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<DailyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getReport(id)
      .then(setReport)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-muted-foreground">Yükleniyor...</p>;
  if (error) return <p className="text-red-400">Hata: {error}</p>;
  if (!report) return null;

  const niches = Object.keys(NICHE_LABELS).filter((k) => report.niches[k]);

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-xl font-semibold">{report.report_date}</h1>
        <Badge variant="outline">{report.status}</Badge>
        <span className="text-sm text-muted-foreground">{report.signals_used} sinyal</span>
      </div>

      <Tabs defaultValue={niches[0] ?? "football"}>
        <TabsList>
          {niches.map((n) => (
            <TabsTrigger key={n} value={n}>{NICHE_LABELS[n] ?? n}</TabsTrigger>
          ))}
        </TabsList>
        {niches.map((n) => (
          <TabsContent key={n} value={n}>
            <NicheTab report={report.niches[n]} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
