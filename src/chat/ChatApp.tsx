/**
 * Tier-4 chat UI. Connects to the self-hosted CopilotKit runtime (which proxies to the
 * ADK agent over AG-UI). Charts render inline in the conversation, and follow-ups
 * ("why did March dip?") work because the agent keeps artifact context in session state.
 *
 * Served at /chat.html via Vite (separate entry from the key-free demo at /).
 */
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { useAdkRenderUI } from "./useAdkRenderUI";
import "../styles.css";

function Conversation() {
  // Register the generative-UI binding so render_ui tool calls become charts.
  useAdkRenderUI();
  return (
    <CopilotChat
      className="agent-chat"
      labels={{
        title: "Program Analyst",
        initial:
          "Ask about CPI, SPI, risks, or program health. Try: \"Show CPI trend for the last six months\", then \"why did March dip?\"",
      }}
    />
  );
}

export default function ChatApp() {
  return (
    // agent="program_analyst" must match the key registered in server/copilotkit-runtime.ts
    <CopilotKit runtimeUrl="/api/copilotkit" agent="program_analyst">
      <div style={{ maxWidth: 820, margin: "0 auto", height: "100vh", padding: 16 }}>
        <Conversation />
      </div>
    </CopilotKit>
  );
}
