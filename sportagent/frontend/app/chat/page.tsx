"use client";
import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { chatStream } from "@/lib/api";
import { Send } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  status?: string;
  streaming?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [convId, setConvId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const cancelRef = useRef<(() => void) | null>(null);
  const accTextRef = useRef<string>("");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);
    accTextRef.current = "";

    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "", streaming: true },
    ]);

    cancelRef.current = chatStream(
      text,
      convId,
      (chunk) => {
        accTextRef.current += chunk;
        const fullText = accTextRef.current;
        setMessages((prev) =>
          prev.map((m, i) =>
            i === prev.length - 1 && m.role === "assistant"
              ? { ...m, content: fullText }
              : m
          )
        );
      },
      (msg) => {
        setMessages((prev) =>
          prev.map((m, i) =>
            i === prev.length - 1 && m.role === "assistant"
              ? { ...m, status: msg }
              : m
          )
        );
      },
      (id) => {
        setConvId(id);
        setBusy(false);
        setMessages((prev) =>
          prev.map((m, i) =>
            i === prev.length - 1 && m.role === "assistant"
              ? { ...m, streaming: false, status: undefined }
              : m
          )
        );
      },
      (err) => {
        setBusy(false);
        setMessages((prev) =>
          prev.map((m, i) =>
            i === prev.length - 1 && m.role === "assistant"
              ? { ...m, content: `Hata: ${err}`, streaming: false }
              : m
          )
        );
      },
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      <h1 className="text-xl font-semibold mb-4">Chat</h1>
      <ScrollArea className="flex-1 border border-border rounded-lg p-4 mb-4">
        {messages.length === 0 && (
          <p className="text-muted-foreground text-sm">Bir şey sor — örn. &quot;Bugün futbolda ne var?&quot;</p>
        )}
        <div className="space-y-4">
          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                {m.status && (
                  <p className="text-xs text-muted-foreground italic mb-1">{m.status}</p>
                )}
                <p className="whitespace-pre-wrap">
                  {m.content}
                  {m.streaming && <span className="animate-pulse">▋</span>}
                </p>
              </div>
            </div>
          ))}
        </div>
        <div ref={bottomRef} />
      </ScrollArea>
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Mesajını yaz..."
          disabled={busy}
          className="flex-1"
        />
        <Button onClick={send} disabled={busy || !input.trim()} size="icon">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
