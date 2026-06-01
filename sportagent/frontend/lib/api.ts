const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN ?? "";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_TOKEN}`,
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function getReports(limit = 30) {
  return apiFetch<import("./types").ReportListItem[]>(`/reports?limit=${limit}`);
}

export async function getReport(id: string) {
  return apiFetch<import("./types").DailyReport>(`/reports/${id}`);
}

export async function getReportByDate(date: string) {
  return apiFetch<import("./types").DailyReport>(`/reports/by-date/${date}`);
}

export async function getSourcesHealth() {
  return apiFetch<import("./types").SourceHealthRow[]>("/sources/health");
}

export function chatStream(
  message: string,
  conversationId: string | null,
  onText: (chunk: string) => void,
  onStatus: (msg: string) => void,
  onDone: (convId: string) => void,
  onError: (err: string) => void,
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${API_TOKEN}`,
        },
        body: JSON.stringify({ message, conversation_id: conversationId }),
        signal: controller.signal,
      });

      if (!res.ok) {
        onError(`HTTP ${res.status}`);
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          const lines = part.split("\n");
          let event = "text";
          let data = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) event = line.slice(7).trim();
            if (line.startsWith("data: ")) data = line.slice(6).trim();
          }
          if (!data) continue;
          try {
            const parsed = JSON.parse(data);
            if (event === "text" && parsed.chunk) onText(parsed.chunk);
            else if (event === "status" && parsed.msg) onStatus(parsed.msg);
            else if (event === "done" && parsed.conversation_id) onDone(parsed.conversation_id);
            else if (event === "error") onError(parsed.detail ?? "Unknown error");
          } catch {}
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") onError(err.message);
    }
  })();

  return () => controller.abort();
}
