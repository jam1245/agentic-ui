import type { GanttPayload } from "../../contract";

/** Minimal dependency-free Gantt: each task is a positioned bar across the overall
 *  date span. Good enough for milestone/schedule views without a charting lib. */
export function GanttView({ payload }: { payload: GanttPayload }) {
  const tasks = payload.data;
  if (tasks.length === 0) return null;

  const toTs = (d: string) => new Date(d).getTime();
  const min = Math.min(...tasks.map((t) => toTs(t.start)));
  const max = Math.max(...tasks.map((t) => toTs(t.end)));
  const span = Math.max(max - min, 1);
  const pct = (ts: number) => ((ts - min) / span) * 100;

  return (
    <div className="agent-ui-gantt">
      {tasks.map((t, i) => {
        const left = pct(toTs(t.start));
        const width = Math.max(pct(toTs(t.end)) - left, 1);
        return (
          <div key={i} className="agent-ui-gantt-row">
            <div className="agent-ui-gantt-label">{t.task}</div>
            <div className="agent-ui-gantt-track">
              <div
                className="agent-ui-gantt-bar"
                data-status={String(t.status ?? "")}
                style={{ left: `${left}%`, width: `${width}%` }}
                title={`${t.start} → ${t.end}`}
              >
                {t.percentComplete != null && (
                  <span className="agent-ui-gantt-fill" style={{ width: `${Number(t.percentComplete)}%` }} />
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
