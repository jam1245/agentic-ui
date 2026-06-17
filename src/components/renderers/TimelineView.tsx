import type { TimelinePayload } from "../../contract";

export function TimelineView({ payload }: { payload: TimelinePayload }) {
  return (
    <ol className="agent-ui-timeline">
      {payload.data.map((event, i) => (
        <li key={i} className="agent-ui-timeline-item" data-status={String(event.status ?? "")}>
          <div className="agent-ui-timeline-date">{event.date}</div>
          <div className="agent-ui-timeline-body">
            <div className="agent-ui-timeline-title">{event.title}</div>
            {event.description != null && (
              <div className="agent-ui-timeline-desc">{String(event.description)}</div>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
