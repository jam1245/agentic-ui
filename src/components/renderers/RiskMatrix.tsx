import type { RiskMatrixPayload } from "../../contract";

/** 5x5 (configurable) likelihood × impact grid. Each cell lists the risks that land
 *  in it; cell color follows the product score (red = high). */
export function RiskMatrix({ payload }: { payload: RiskMatrixPayload }) {
  const { data, fields, scale } = payload;
  const lMax = scale?.likelihoodMax ?? 5;
  const iMax = scale?.impactMax ?? 5;

  const cellColor = (l: number, i: number) => {
    const score = (l / lMax) * (i / iMax);
    if (score >= 0.6) return "#fee2e2";
    if (score >= 0.3) return "#fef9c3";
    return "#dcfce7";
  };

  // impact descends down the rows, likelihood ascends across columns
  const rows = Array.from({ length: iMax }, (_, r) => iMax - r);
  const cols = Array.from({ length: lMax }, (_, c) => c + 1);

  const risksAt = (l: number, i: number) =>
    data.filter((d) => Number(d[fields.x]) === l && Number(d[fields.y]) === i);

  return (
    <table className="agent-ui-risk-matrix">
      <tbody>
        {rows.map((impact) => (
          <tr key={impact}>
            <th className="agent-ui-risk-axis">{impact}</th>
            {cols.map((likelihood) => {
              const here = risksAt(likelihood, impact);
              return (
                <td key={likelihood} style={{ background: cellColor(likelihood, impact) }}>
                  {here.map((r, idx) => (
                    <div key={idx} className="agent-ui-risk-chip">
                      {String(r[fields.label ?? "risk"] ?? "")}
                    </div>
                  ))}
                </td>
              );
            })}
          </tr>
        ))}
        <tr>
          <th />
          {cols.map((c) => (
            <th key={c} className="agent-ui-risk-axis">
              {c}
            </th>
          ))}
        </tr>
      </tbody>
    </table>
  );
}
