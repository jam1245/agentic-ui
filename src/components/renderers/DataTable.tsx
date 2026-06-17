import type { TablePayload } from "../../contract";

/** The universal fallback. Any payload can degrade to this. */
export function DataTable({ payload }: { payload: TablePayload }) {
  const { data, columns } = payload;
  const cols =
    columns ??
    (data[0] ? Object.keys(data[0]).map((key) => ({ key, label: key, align: "left" as const })) : []);

  return (
    <table className="agent-ui-table">
      <thead>
        <tr>
          {cols.map((c) => (
            <th key={c.key} style={{ textAlign: c.align ?? "left" }}>
              {c.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i}>
            {cols.map((c) => (
              <td key={c.key} style={{ textAlign: c.align ?? "left" }}>
                {String(row[c.key] ?? "")}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
