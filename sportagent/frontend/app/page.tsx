"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getReports } from "@/lib/api";
import type { ReportListItem } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  success: "bg-green-600",
  partial: "bg-yellow-600",
  failed: "bg-red-600",
  pending: "bg-zinc-600",
};

export default function HomePage() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getReports(30)
      .then(setReports)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-muted-foreground">Yükleniyor...</p>;
  if (error) return <p className="text-red-400">Hata: {error}</p>;

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Günlük Raporlar</h1>
      {reports.length === 0 ? (
        <p className="text-muted-foreground">
          Henüz rapor yok.{" "}
          <code className="bg-muted px-1 rounded text-xs">POST /admin/run-now</code> ile rapor üret.
        </p>
      ) : (
        <div className="grid gap-3">
          {reports.map((r) => (
            <Link key={r.id} href={`/report/${r.id}`}>
              <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{r.report_date}</CardTitle>
                    <Badge className={`${STATUS_COLORS[r.status] ?? "bg-zinc-600"} text-white text-xs`}>
                      {r.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground flex gap-4">
                  <span>{r.signals_used} sinyal</span>
                  {r.duration_ms != null && <span>{(r.duration_ms / 1000).toFixed(1)}s</span>}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
