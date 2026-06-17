/**
 * Standalone demo: renders example payloads through the SAME AgentUIRenderer the agent
 * drives in production, AND shows the artifact context the chat agent would retain for
 * follow-up questions. No CopilotKit/agent needed — this proves both contracts in
 * isolation. `npm run dev` to view.
 */
import { useMemo, useState } from "react";
import { AgentUIRenderer } from "./components/AgentUIRenderer";
import { ALL_EXAMPLES } from "./examples/payloads";
import { newArtifactId, toArtifactContext, toDigest } from "./contract";
import "./styles.css";

export default function App() {
  const [active, setActive] = useState(0);
  const example = ALL_EXAMPLES[active];

  // Build the ArtifactContext the way render_ui would, then project to the prompt-safe
  // digest the chat agent actually sees each turn.
  const digest = useMemo(() => {
    const payload = { ...example.payload, artifactId: newArtifactId(example.payload.component) };
    const ctx = toArtifactContext(payload, {
      originalUserQuestion: `(${example.key}) example question`,
      sourceTool: payload.metadata.source,
      summaryForFutureTurns: payload.metadata.explanation ?? "",
    });
    return toDigest(ctx);
  }, [example]);

  return (
    <main style={{ maxWidth: 920, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ fontSize: 20 }}>Agent-driven UI — two-contract demo</h1>
      <p style={{ color: "#64748b" }}>
        Each tab is a payload an agent would emit. The same <code>&lt;AgentUIRenderer&gt;</code> renders them all, and
        the panel below shows the <strong>artifact context</strong> the chat agent keeps for follow-ups.
      </p>
      <nav style={{ display: "flex", flexWrap: "wrap", gap: 6, margin: "16px 0" }}>
        {ALL_EXAMPLES.map((ex, i) => (
          <button
            key={ex.key}
            onClick={() => setActive(i)}
            style={{
              border: "1px solid #e2e8f0",
              background: i === active ? "#2563eb" : "#fff",
              color: i === active ? "#fff" : "#0f172a",
              borderRadius: 8,
              padding: "4px 12px",
              cursor: "pointer",
            }}
          >
            {ex.key}
          </button>
        ))}
      </nav>

      <AgentUIRenderer raw={example.payload} />

      <section style={{ marginTop: 8, border: "1px dashed #cbd5e1", borderRadius: 10, padding: 16, background: "#f8fafc" }}>
        <h3 style={{ margin: "0 0 8px", fontSize: 14 }}>
          🧠 What the chat agent remembers (compact digest — fed to the prompt each turn)
        </h3>
        <p style={{ margin: "0 0 8px", fontSize: 12, color: "#64748b" }}>
          The full dataset stays out of the prompt; only this digest + a data reference are injected. Follow-ups like
          "why did March dip?" use the summary, then rehydrate full rows on demand.
        </p>
        <pre style={{ margin: 0, fontSize: 12, overflowX: "auto" }}>{JSON.stringify(digest, null, 2)}</pre>
      </section>
    </main>
  );
}
