import type { KpiCardPayload, StatusLevel } from "../../contract";

const COLORS: Record<StatusLevel, string> = {
  good: "#16a34a",
  warning: "#d97706",
  critical: "#dc2626",
  neutral: "#475569",
};

export function KpiCardGrid({ payload }: { payload: KpiCardPayload }) {
  return (
    <div className="agent-ui-kpi-grid">
      {payload.data.map((kpi, i) => {
        const status = (kpi.status ?? "neutral") as StatusLevel;
        return (
          <div key={i} className="agent-ui-kpi-card" style={{ borderTop: `3px solid ${COLORS[status]}` }}>
            <div className="agent-ui-kpi-label">{kpi.label}</div>
            <div className="agent-ui-kpi-value" style={{ color: COLORS[status] }}>
              {String(kpi.value)}
              {kpi.unit ? <span className="agent-ui-kpi-unit"> {String(kpi.unit)}</span> : null}
            </div>
            {kpi.delta != null && <div className="agent-ui-kpi-delta">{String(kpi.delta)}</div>}
          </div>
        );
      })}
    </div>
  );
}
