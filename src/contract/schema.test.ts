import { describe, expect, it } from "vitest";
import { validatePayload } from "./schema";
import { ALL_EXAMPLES } from "../examples/payloads";

describe("agent-to-UI contract", () => {
  it("accepts every documented example payload", () => {
    for (const { key, payload } of ALL_EXAMPLES) {
      const result = validatePayload(payload);
      expect(result.ok, `${key} should validate`).toBe(true);
      expect(result.payload.component).toBe(payload.component);
    }
  });

  it("falls back to a table when the component is unknown", () => {
    const result = validatePayload({ component: "pie_3d", title: "Bad", data: [{ a: 1 }], metadata: { source: "x" } });
    expect(result.ok).toBe(false);
    expect(result.payload.component).toBe("table");
    expect(result.payload.data).toEqual([{ a: 1 }]);
  });

  it("falls back when a line_chart is missing required field mapping", () => {
    const result = validatePayload({
      component: "line_chart",
      title: "CPI",
      data: [{ month: "Jan", cpi: 0.9 }],
      fields: {}, // missing x and y
      metadata: { source: "EVMS MCP" },
    });
    expect(result.ok).toBe(false);
    expect(result.payload.component).toBe("table");
  });

  it("preserves data through the fallback so the user still sees numbers", () => {
    const result = validatePayload({ component: "garbage", title: "T", data: [{ x: 1 }, { x: 2 }], metadata: {} });
    expect(result.payload.data).toHaveLength(2);
  });
});
