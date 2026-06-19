/**
 * Landing page — the whole story on one screen:
 *   LEFT  : a LIVE chat powered by the internal Genesis LLM. Canned prompt chips really
 *           plot; follow-ups are answered from stored context.
 *   RIGHT : "Under the hood" — the artifact context the agent has ABSORBED (grows as you
 *           chat), the exact contract payload it emitted (the code), and a gallery of
 *           every component.
 *
 * Run `npm run dev:genesis` (chat works offline via the mock backend; add a Genesis key
 * to go live). `npm run dev` serves the page too, but the chat needs the backend.
 */
import { useEffect, useMemo, useState } from "react";
import { AgentUIRenderer } from "./components/AgentUIRenderer";
import { ALL_EXAMPLES } from "./examples/payloads";
import { useGenesisChat } from "./genesis/useGenesisChat";
import "./styles.css";

/**
 * Minimal, SAFE Markdown → HTML for assistant bubbles. HTML is escaped FIRST, so the only
 * tags in the output are the ones we add (strong/em/code/ul/ol/li/p) — no XSS from model
 * output. Handles what the agent emits: **bold**, *italic*, `code`, bullet/numbered lists,
 * and paragraphs. Intentionally ignores tables/headings/raw HTML.
 */
function renderMarkdown(src: string): string {
  const esc = (t: string) =>
    t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const inline = (t: string) =>
    esc(t)
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");

  const out: string[] = [];
  let list: { type: "ul" | "ol"; items: string[] } | null = null;
  const flush = () => {
    if (list) {
      out.push(`<${list.type}>${list.items.map((i) => `<li>${i}</li>`).join("")}</${list.type}>`);
      list = null;
    }
  };
  for (const raw of src.split("\n")) {
    const line = raw.trim();
    if (!line) { flush(); continue; }
    const bullet = line.match(/^[-*]\s+(.*)/);
    const ordered = line.match(/^\d+[.)]\s+(.*)/);
    if (bullet) {
      if (!list || list.type !== "ul") { flush(); list = { type: "ul", items: [] }; }
      list.items.push(inline(bullet[1]));
    } else if (ordered) {
      if (!list || list.type !== "ol") { flush(); list = { type: "ol", items: [] }; }
      list.items.push(inline(ordered[1]));
    } else {
      flush();
      out.push(`<p>${inline(line)}</p>`);
    }
  }
  flush();
  return out.join("");
}

interface Health { mode?: string; why?: string | null; adk_error?: string | null }

function ModeBadge() {
  const [h, setH] = useState<Health | null>(null);
  useEffect(() => {
    fetch("/api/health").then((r) => r.json()).then(setH).catch(() => setH({ mode: "?" }));
  }, []);
  if (!h) return null;
  const adk = h.mode === "adk";
  return (
    <span
      title={adk ? "Google ADK + Genesis LLM" : `Deterministic engine — ${h.why || "no LLM"}${h.adk_error ? `\n${h.adk_error}` : ""}`}
      style={{
        fontSize: 12, fontWeight: 600, padding: "2px 10px", borderRadius: 999,
        background: adk ? "#dcfce7" : "#fef9c3", color: adk ? "#166534" : "#854d0e",
        border: `1px solid ${adk ? "#86efac" : "#fde047"}`,
      }}
    >
      {adk ? "● ADK + Genesis (LLM)" : "● Deterministic engine (no LLM)"}
    </span>
  );
}

const SUGGESTIONS = [
  "Show CPI trend for the last six months.",
  "Why did March dip?",
  "Summarize program health.",
  "Show top risks by likelihood and impact.",
  "Compare SPI across control accounts.",
  "Show CAM variance for June.",
];

export default function App() {
  const { turns, artifacts, latestPayload, busy, send } = useGenesisChat();
  const [input, setInput] = useState("");
  const [tab, setTab] = useState<"context" | "payload" | "gallery">("context");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    send(input);
    setInput("");
  }

  return (
    <main className="landing">
      <header className="landing-head">
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <h1 style={{ margin: 0 }}>Agent-driven UI — program analyst</h1>
          <ModeBadge />
        </div>
        <p>
          Your internal <strong>Genesis</strong> LLM turns questions into charts, and remembers the data behind them
          so follow-ups just work. Try a chip, then ask <em>"why did March dip?"</em>
        </p>
      </header>

      <div className="landing-grid">
        {/* ---------------- LEFT: live chat ---------------- */}
        <section className="chat-pane">
          <div className="chat-chips">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="chip" onClick={() => send(s)} disabled={busy}>
                {s}
              </button>
            ))}
          </div>

          <div className="chat-log">
            {turns.length === 0 && (
              <div className="chat-empty">Pick a prompt above to start — charts render right here in the chat.</div>
            )}
            {turns.map((turn, i) => (
              <div key={i} className={`bubble bubble--${turn.role}`}>
                <div className="bubble-role">{turn.role === "user" ? "You" : "Analyst"}</div>
                {turn.contextUsed && turn.contextUsed.length > 0 && (
                  <div className="ctx-badge" title="Answered using data already in the conversation">
                    🧠 used context: {turn.contextUsed.map((c) => c.title).join(", ")}
                  </div>
                )}
                {turn.text &&
                  (turn.role === "assistant" ? (
                    <div className="bubble-text" dangerouslySetInnerHTML={{ __html: renderMarkdown(turn.text) }} />
                  ) : (
                    <div className="bubble-text">{turn.text}</div>
                  ))}
                {turn.payloads?.map((p, j) => (
                  <AgentUIRenderer key={j} raw={p} />
                ))}
              </div>
            ))}
            {busy && <div className="chat-thinking">Analyst is thinking…</div>}
          </div>

          <form className="chat-input" onSubmit={submit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about CPI, SPI, risks, program health…"
            />
            <button type="submit" disabled={busy}>
              Send
            </button>
          </form>
        </section>

        {/* ---------------- RIGHT: under the hood ---------------- */}
        <section className="hood-pane">
          <div className="hood-tabs">
            <button className={tab === "context" ? "on" : ""} onClick={() => setTab("context")}>
              Context ({artifacts.length})
            </button>
            <button className={tab === "payload" ? "on" : ""} onClick={() => setTab("payload")}>
              Payload
            </button>
            <button className={tab === "gallery" ? "on" : ""} onClick={() => setTab("gallery")}>
              Gallery
            </button>
          </div>

          {tab === "context" && <ContextPanel artifacts={artifacts} />}
          {tab === "payload" && <PayloadPanel payload={latestPayload} />}
          {tab === "gallery" && <Gallery />}
        </section>
      </div>
    </main>
  );
}

function ContextPanel({ artifacts }: { artifacts: ReturnType<typeof useGenesisChat>["artifacts"] }) {
  return (
    <div className="hood-body">
      <p className="hood-hint">
        Every chart the agent renders is also stored here as a compact <strong>digest</strong> (summary + schema +
        sample) — this is what gets fed into future prompts so the chat stays data-aware. The full rows stay out of the
        prompt and are rehydrated only when a follow-up needs them.
      </p>
      {artifacts.length === 0 && <div className="chat-empty">No data absorbed yet — ask for a chart.</div>}
      {artifacts.map((a) => (
        <div key={a.artifactId} className="ctx-card">
          <div className="ctx-title">{a.title}</div>
          <div className="ctx-summary">{a.summary}</div>
          <div className="ctx-meta">
            {a.artifactType} · {a.rowCount} rows · fields: {Object.entries(a.fields).map(([k, v]) => `${k}=${v}`).join(", ") || "—"}
          </div>
        </div>
      ))}
    </div>
  );
}

function PayloadPanel({ payload }: { payload: ReturnType<typeof useGenesisChat>["latestPayload"] }) {
  return (
    <div className="hood-body">
      <p className="hood-hint">
        The exact <strong>AgentUIPayload</strong> the agent emitted for the last chart — validated, then rendered by the
        generic <code>&lt;AgentUIRenderer&gt;</code>. This is the agent-to-UI contract.
      </p>
      {payload ? (
        <pre className="hood-code">{JSON.stringify(payload, null, 2)}</pre>
      ) : (
        <div className="chat-empty">Render a chart to see its payload.</div>
      )}
    </div>
  );
}

function Gallery() {
  const [active, setActive] = useState(0);
  const example = useMemo(() => ALL_EXAMPLES[active], [active]);
  return (
    <div className="hood-body">
      <p className="hood-hint">Every component the agent can choose from, rendered from a static example payload.</p>
      <div className="gallery-tabs">
        {ALL_EXAMPLES.map((ex, i) => (
          <button key={ex.key} className={i === active ? "on" : ""} onClick={() => setActive(i)}>
            {ex.key}
          </button>
        ))}
      </div>
      <AgentUIRenderer raw={example.payload} />
    </div>
  );
}
