import type { VarianceTablePayload } from "../../contract";

/** Plan-vs-actual table. Columns flagged `kind: "variance"` are colored and arrowed
 *  (▲ favorable / ▼ unfavorable). Used for CAM variance, budget vs actual, etc. */
export function VarianceTable({ payload }: { payload: VarianceTablePayload }) {
  const { data, columns } = payload;

  const renderVariance = (v: unknown) => {
    const n = Number(v);
    if (Number.isNaN(n)) return String(v ?? "");
    const arrow = n > 0 ? "▲" : n < 0 ? "▼" : "—";
    const color = n > 0 ? "#16a34a" : n < 0 ? "#dc2626" : "#475569";
    return (
      <span style={{ color }}>
        {arrow} {n.toLocaleString()}
      </span>
    );
  };

  return (
    <table className="agent-ui-table agent-ui-variance">
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c.key} style={{ textAlign: c.kind === "text" ? "left" : "right" }}>
              {c.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((rowData, i) => (
          <tr key={i}>
            {columns.map((c) => (
              <td key={c.key} style={{ textAlign: c.kind === "text" ? "left" : "right" }}>
                {c.kind === "variance" ? renderVariance(rowData[c.key]) : String(rowData[c.key] ?? "")}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
