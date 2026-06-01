"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getSourcesHealth } from "@/lib/api";
import type { SourceHealthRow } from "@/lib/types";

function rateColor(rate: number | null) {
  if (rate === null) return "bg-zinc-600";
  if (rate >= 0.8) return "bg-green-600";
  if (rate >= 0.5) return "bg-yellow-600";
  return "bg-red-600";
}

export default function SourcesPage() {
  const [rows, setRows] = useState<SourceHealthRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSourcesHealth()
      .then(setRows)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-muted-foreground">Yükleniyor...</p>;
  if (error) return <p className="text-red-400">Hata: {error}</p>;

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Sources Health (Son 7 Gün)</h1>
      {rows.length === 0 ? (
        <p className="text-muted-foreground">Henüz source health verisi yok.</p>
      ) : (
        <div className="grid gap-3">
          {rows.map((r) => (
            <Card key={r.source}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-mono">{r.source}</CardTitle>
                  <Badge className={`${rateColor(r.success_rate_7d)} text-white text-xs`}>
                    {r.success_rate_7d != null ? `${(r.success_rate_7d * 100).toFixed(0)}%` : "—"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground flex gap-4">
                <span>{r.success_7d}/{r.total_7d} başarılı</span>
                <span>{r.signals_7d ?? 0} sinyal</span>
                {r.last_attempt && <span>Son: {new Date(r.last_attempt).toLocaleDateString("tr-TR")}</span>}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
