import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LineChartPayload } from "../../contract";

/** Generic line chart driven entirely by `fields.x` / `fields.y` / `fields.groupBy`. */
export function LineChartView({ payload }: { payload: LineChartPayload }) {
  const { data, fields, referenceLine } = payload;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={fields.x} />
        <YAxis />
        <Tooltip />
        {referenceLine && (
          <ReferenceLine y={referenceLine.value} label={referenceLine.label} stroke="#94a3b8" strokeDasharray="4 4" />
        )}
        <Line type="monotone" dataKey={fields.y} stroke="#2563eb" strokeWidth={2} dot />
      </LineChart>
    </ResponsiveContainer>
  );
}
