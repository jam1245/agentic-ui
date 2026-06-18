/**
 * Chat state for the live Genesis panel on the landing page.
 *
 * Talks to server/genesis_app.py (`POST /api/chat`). Tracks the conversation, the
 * artifacts the agent has absorbed into context, and — per turn — which prior artifacts a
 * follow-up drew on. That last bit is what visibly proves "the data is in the chat
 * context" to a developer watching the page.
 */
import { useCallback, useState } from "react";
import type { AgentUIPayload, ArtifactDigest } from "../contract";

export interface ChatTurn {
  role: "user" | "assistant";
  text: string;
  payloads?: AgentUIPayload[];
  /** Prior artifacts this turn pulled from context (assistant turns only). */
  contextUsed?: { artifactId: string; title: string }[];
}

interface ChatResponse {
  text: string;
  payloads?: AgentUIPayload[];
  artifacts?: ArtifactDigest[];
  context_used?: { artifactId: string; title: string }[];
}

const SESSION_ID = `web-${Math.random().toString(36).slice(2)}`;

export function useGenesisChat() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactDigest[]>([]);
  const [latestPayload, setLatestPayload] = useState<AgentUIPayload | null>(null);
  const [busy, setBusy] = useState(false);
  const [backendDown, setBackendDown] = useState(false);

  const send = useCallback(async (message: string) => {
    if (!message.trim() || busy) return;
    setTurns((t) => [...t, { role: "user", text: message }]);
    setBusy(true);
    setBackendDown(false);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: SESSION_ID }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: ChatResponse = await res.json();
      setTurns((t) => [
        ...t,
        { role: "assistant", text: data.text, payloads: data.payloads, contextUsed: data.context_used },
      ]);
      if (data.artifacts) setArtifacts(data.artifacts);
      const last = data.payloads?.[data.payloads.length - 1];
      if (last) setLatestPayload(last);
    } catch {
      setBackendDown(true);
      setTurns((t) => [
        ...t,
        {
          role: "assistant",
          text: "⚠ Couldn't reach the Genesis backend. Start it with `npm run dev:genesis` (runs offline in mock mode — no key needed).",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }, [busy]);

  return { turns, artifacts, latestPayload, busy, backendDown, send };
}
