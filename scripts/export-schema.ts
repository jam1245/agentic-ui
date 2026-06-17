/**
 * Export the zod contract as JSON Schema so the SAME definition can be handed to the
 * Google ADK tool / LLM as its output schema. Run: `npm run export:schema`.
 *
 * This is the mechanism that keeps the agent and UI from drifting: one source
 * (contract/schema.ts) → TypeScript types for React AND JSON Schema for the agent.
 */
import { writeFileSync, mkdirSync } from "node:fs";
import { z } from "zod";
import { payloadSchema } from "../src/contract/schema";

// zod v4 ships `z.toJSONSchema`. (On zod v3 use the `zod-to-json-schema` package.)
const jsonSchema = z.toJSONSchema(payloadSchema, { target: "draft-2020-12" });

mkdirSync("dist", { recursive: true });
writeFileSync("dist/agent-ui-payload.schema.json", JSON.stringify(jsonSchema, null, 2));
console.log("Wrote dist/agent-ui-payload.schema.json");
