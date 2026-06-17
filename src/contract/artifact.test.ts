import { describe, expect, it } from "vitest";
import { toArtifactContext, toDigest } from "./artifact";
import { artifactRegistry } from "../store/artifactRegistry";
import { cpiTrend, riskMatrix } from "../examples/payloads";

describe("artifact-to-agent context contract", () => {
  it("normalizes a rendering payload into an artifact, sharing the same artifactId", () => {
    const payload = { ...cpiTrend, artifactId: "artifact_cpi_001" };
    const a = toArtifactContext(payload, {
      originalUserQuestion: "Show CPI trend for the last six months.",
      sourceTool: "evms_mcp.get_cpi_history",
      summaryForFutureTurns: "CPI improved from 0.92 to 1.01 with a dip in March.",
    });
    expect(a.artifactId).toBe("artifact_cpi_001");
    expect(a.artifactType).toBe("line_chart");
    expect(a.fields).toEqual({ x: "month", y: "cpi" });
    expect(a.fullData).toHaveLength(cpiTrend.data.length);
  });

  it("keeps the prompt-safe digest free of the full dataset", () => {
    const bigMatrix = {
      ...riskMatrix,
      data: Array.from({ length: 500 }, (_, i) => ({ risk: `R${i}`, likelihood: 3, impact: 3 })),
    } as typeof riskMatrix;
    const a = toArtifactContext(bigMatrix, {
      originalUserQuestion: "top risks",
      sourceTool: "risk_register_mcp.list",
      summaryForFutureTurns: "Two highs.",
    });
    const digest = toDigest(a);
    expect(digest.rowCount).toBe(500);
    expect(digest.dataSample!.length).toBeLessThanOrEqual(5); // sample only
    expect("fullData" in digest).toBe(false); // full data never in the digest
    expect(digest.summary).toBe("Two highs.");
  });

  it("registry stores full data and exposes it for on-demand rehydration", () => {
    artifactRegistry.clear();
    const a = toArtifactContext(
      { ...cpiTrend, artifactId: "artifact_cpi_002" },
      { originalUserQuestion: "cpi", sourceTool: "evms_mcp.get_cpi_history", summaryForFutureTurns: "dip in March" },
    );
    artifactRegistry.upsert(a);

    expect(artifactRegistry.digests()).toHaveLength(1);
    const full = artifactRegistry.getFullData("artifact_cpi_002");
    expect(full).toHaveLength(cpiTrend.data.length);
    // the March row is recoverable for "why did March dip?"
    expect(full!.some((r) => r.month === "Mar")).toBe(true);
  });
});
