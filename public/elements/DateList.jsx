import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock, AlertCircle, CheckCircle, Circle } from "lucide-react";

function daysUntil(dateStr) {
  if (!dateStr) return null;
  const due = new Date(dateStr);
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  due.setHours(0, 0, 0, 0);
  return Math.round((due - now) / (1000 * 60 * 60 * 24));
}

function urgency(days) {
  if (days === null) return "unknown";
  if (days < 0) return "overdue";
  if (days === 0) return "today";
  if (days <= 7) return "soon";
  if (days <= 14) return "upcoming";
  return "ok";
}

const URGENCY = {
  overdue: { border: "#f87171", bg: "rgba(239,68,68,0.1)", Icon: AlertCircle },
  today: { border: "#f87171", bg: "rgba(239,68,68,0.1)", Icon: AlertCircle },
  soon: { border: "#fbbf24", bg: "rgba(245,158,11,0.1)", Icon: Clock },
  upcoming: { border: "#facc15", bg: "rgba(234,179,8,0.1)", Icon: Clock },
  ok: { border: "#34d399", bg: "rgba(16,185,129,0.1)", Icon: CheckCircle },
  unknown: { border: "#334155", bg: "rgba(100,116,139,0.1)", Icon: Circle },
};

function daysLabel(days) {
  if (days === null) return "-";
  if (days < 0) return `${Math.abs(days)}d overdue`;
  if (days === 0) return "Due today";
  return `${days}d left`;
}

export default function DateList() {
  const title = props.title || "Upcoming dates";
  const items = props.items || props.deadlines || [];

  return (
    <Card className="mt-3 w-full max-w-lg">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        {props.subtitle && <p className="text-xs text-muted-foreground">{props.subtitle}</p>}
      </CardHeader>
      <CardContent className="pb-3">
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {items.map((item, i) => {
            const days = daysUntil(item.due_date);
            const u = urgency(days);
            const { border, bg, Icon } = URGENCY[u];
            return (
              <div
                key={i}
                style={{ border: `2px solid ${border}`, background: bg, borderRadius: 8, padding: 12 }}
              >
                <div className="flex items-start justify-between gap-1">
                  <span className="text-sm font-medium leading-tight">{item.title}</span>
                  {item.badge && <Badge variant="outline" className="text-xs h-5 px-1.5">{item.badge}</Badge>}
                  {!item.badge && item.type && <Badge variant="outline" className="text-xs h-5 px-1.5">{item.type}</Badge>}
                </div>
                <div className="flex items-center gap-1.5 mt-2 text-sm font-semibold">
                  <Icon className="h-3.5 w-3.5 flex-shrink-0" />
                  <span>{daysLabel(days)}</span>
                  {item.due_date && <span className="text-xs font-normal opacity-70">· {item.due_date}</span>}
                </div>
                {item.status && <span className="text-xs text-muted-foreground capitalize mt-1 block">{item.status}</span>}
              </div>
            );
          })}
        </div>
        {items.length === 0 && <p className="text-sm text-muted-foreground text-center py-4">No items.</p>}
      </CardContent>
    </Card>
  );
}
