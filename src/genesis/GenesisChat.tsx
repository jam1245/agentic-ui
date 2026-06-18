/**
 * Genesis chat UI — talks to server/genesis_app.py (the internal LLM), renders any
 * returned payloads with the SAME <AgentUIRenderer>, and shows the artifact digests the
 * agent retains. This is the "real world example" path: your internal Genesis assistant
 * driving rich UI through the agent-to-UI contract.
 *
 * Deliberately dependency-light (plain fetch, no CopilotKit) so it runs against the
 * Genesis Assistants API without the AG-UI/CopilotKit chain. The contracts and renderers
 * are identical to every other tier.
 */
import { useState } from "react";
import { AgentUIRenderer } from "../components/AgentUIRenderer";
import type { AgentUIPayload, ArtifactDigest } from "../contract";
import "../styles.css";

interface Turn {
  role: "user" | "assistant";
  text: string;
  payloads?: AgentUIPayload[];
}

const SESSION_ID = `web-${Math.random().toString(36).slice(2)}`;
const SUGGESTIONS = [
  "Show CPI trend for the last six months.",
  "Why did March dip?",
  "Summarize program health.",
  "Show top risks by likelihood and impact.",
];

export default function GenesisChat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [artifacts, setArtifacts] = useState<ArtifactDigest[]>([]);

  async function send(message: string) {
    if (!message.trim() || busy) return;
    setTurns((t) => [...t, { role: "user", text: message }]);
    setInput("");
    setBusy(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: SESSION_ID }),
      });
      const data = await res.json();
      setTurns((t) => [...t, { role: "assistant", text: data.text, payloads: data.payloads }]);
      setArtifacts(data.artifacts ?? []);
    } catch (e) {
      setTurns((t) => [...t, { role: "assistant", text: `Error: ${String(e)}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ maxWidth: 880, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ fontSize: 20 }}>Program Analyst — powered by Genesis</h1>
      <p style={{ color: "#64748b", fontSize: 13 }}>
        Your internal LLM drives the charts. Same contracts, same renderers as every other tier.
      </p>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, margin: "12px 0" }}>
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => send(s)} disabled={busy}
            style={{ border: "1px solid #e2e8f0", background: "#fff", borderRadius: 8, padding: "4px 10px", fontSize: 12, cursor: "pointer" }}>
            {s}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {turns.map((turn, i) => (
          <div key={i}>
            <div style={{ fontSize: 12, color: "#64748b", marginBottom: 2 }}>
              {turn.role === "user" ? "You" : "Analyst"}
            </div>
            {turn.text && <div style={{ fontSize: 14 }}>{turn.text}</div>}
            {turn.payloads?.map((p, j) => (
              <AgentUIRenderer key={j} raw={p} />
            ))}
          </div>
        ))}
        {busy && <div style={{ color: "#64748b", fontSize: 13 }}>Analyst is thinking…</div>}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        style={{ display: "flex", gap: 8, marginTop: 16 }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about CPI, SPI, risks, program health…"
          style={{ flex: 1, padding: "8px 12px", border: "1px solid #e2e8f0", borderRadius: 8 }}
        />
        <button type="submit" disabled={busy} style={{ padding: "8px 16px", borderRadius: 8, border: "none", background: "#2563eb", color: "#fff", cursor: "pointer" }}>
          Send
        </button>
      </form>

      {artifacts.length > 0 && (
        <section style={{ marginTop: 16, border: "1px dashed #cbd5e1", borderRadius: 10, padding: 12, background: "#f8fafc" }}>
          <h3 style={{ margin: "0 0 8px", fontSize: 13 }}>🧠 Artifacts the agent remembers (for follow-ups)</h3>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "#475569" }}>
            {artifacts.map((a) => (
              <li key={a.artifactId}>
                <strong>{a.title}</strong> — {a.summary}
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
