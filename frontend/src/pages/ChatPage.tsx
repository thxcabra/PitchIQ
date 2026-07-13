import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { ChatResponse } from "../types";
import ResponseRenderer from "../components/renderers/ResponseRenderer";
import Icon from "../components/Icon";

interface Msg {
  id: number;
  role: "user" | "assistant";
  text?: string;
  resp?: ChatResponse;
  error?: string;
}

const EXAMPLES = [
  "Top 5 scorers in the Champions League",
  "Best young wingers in Serie A by goals per 90",
  "Most assists in the Portuguese league",
  "Compare Haaland and Mbappé",
  "Show me the best player",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const idSeq = useRef(0);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  async function ask(q: string) {
    const text = q.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((m) => [...m, { id: ++idSeq.current, role: "user", text }]);
    setLoading(true);
    try {
      const resp = await api.chat(text);
      setMessages((m) => [...m, { id: ++idSeq.current, role: "assistant", resp }]);
    } catch (e) {
      setMessages((m) => [...m, { id: ++idSeq.current, role: "assistant", error: (e as Error).message }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto flex flex-col" style={{ minHeight: "calc(100vh - 8rem)" }}>
      <div className="flex-1 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-10 animate-fade-up">
            <span className="grid place-items-center w-12 h-12 mx-auto rounded-xl bg-pitch-accent/15
                             text-pitch-accent ring-1 ring-pitch-accent/25 mb-3">
              <Icon name="sparkle" size={24} />
            </span>
            <h1 className="text-2xl font-bold text-white tracking-tight">Ask PitchIQ</h1>
            <p className="text-pitch-sub mt-2">Rankings, player profiles, or comparisons — in English or Portuguese.</p>
            <div className="flex flex-col items-center gap-2 mt-5">
              {EXAMPLES.map((e) => (
                <button key={e} className="btn max-w-full text-left hover:border-pitch-accent/50" onClick={() => ask(e)}>
                  <Icon name="bolt" size={14} className="text-pitch-accent shrink-0" /> {e}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="flex justify-end animate-fade-up">
              <div className="bg-pitch-accent/15 text-white rounded-2xl rounded-br-md px-4 py-2.5 max-w-[80%]
                              ring-1 ring-pitch-accent/20">
                {m.text}
              </div>
            </div>
          ) : (
            <div key={m.id} className="flex justify-start animate-fade-up">
              <div className="w-full">
                {m.error ? (
                  <div className="card p-4 text-rose-300 flex items-center gap-2">
                    <Icon name="alert" size={18} /> {m.error}
                  </div>
                ) : (
                  <ResponseRenderer resp={m.resp!} onAsk={ask} />
                )}
              </div>
            </div>
          ),
        )}

        {loading && (
          <div className="flex justify-start">
            <div className="card px-4 py-3 text-pitch-sub text-sm flex items-center gap-2">
              <span className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-pitch-accent animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 rounded-full bg-pitch-accent animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 rounded-full bg-pitch-accent animate-bounce" style={{ animationDelay: "300ms" }} />
              </span>
              PitchIQ is thinking…
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form
        className="sticky bottom-0 bg-pitch-bg/90 backdrop-blur py-3 flex gap-2"
        onSubmit={(e) => { e.preventDefault(); ask(input); }}
      >
        <input
          className="input"
          placeholder="Ask a question…  (e.g. artilheiros da Champions League)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" aria-label="Send"
                className="btn btn-accent px-4 disabled:opacity-40 disabled:cursor-not-allowed"
                disabled={loading || !input.trim()}>
          <Icon name="send" size={16} /> <span className="hidden sm:inline">Send</span>
        </button>
      </form>
    </div>
  );
}
