import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { BarChartPayload } from "../../contract";

export function BarChartView({ payload }: { payload: BarChartPayload }) {
  const { data, fields, orientation = "vertical" } = payload;
  const horizontal = orientation === "horizontal";
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={data}
        layout={horizontal ? "vertical" : "horizontal"}
        margin={{ top: 16, right: 24, bottom: 8, left: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        {horizontal ? (
          <>
            <XAxis type="number" />
            <YAxis type="category" dataKey={fields.x} width={120} />
          </>
        ) : (
          <>
            <XAxis dataKey={fields.x} />
            <YAxis />
          </>
        )}
        <Tooltip />
        <Bar dataKey={fields.y} fill="#2563eb" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
