import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Target, MessageSquare, CalendarCheck, Award, Circle, Star, Flag, FileText,
} from "lucide-react";

const ICONS = {
  goal: Target,
  feedback: MessageSquare,
  checkin: CalendarCheck,
  award: Award,
  milestone: Flag,
  document: FileText,
  star: Star,
  other: Circle,
};

const BADGE = {
  goal: "bg-blue-500/15 text-blue-700 border-blue-300",
  feedback: "bg-purple-500/15 text-purple-700 border-purple-300",
  checkin: "bg-green-500/15 text-green-700 border-green-300",
  award: "bg-amber-500/15 text-amber-700 border-amber-300",
  default: "",
};

const DOT = {
  goal: "#3b82f6",
  feedback: "#a855f7",
  checkin: "#22c55e",
  award: "#f59e0b",
  default: "#64748b",
};

export default function Timeline() {
  const title = props.title || "Timeline";
  const subtitle = props.subtitle || props.employee || "";
  const events = props.events || [];

  return (
    <Card className="mt-3 w-full max-w-lg">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
      </CardHeader>
      <CardContent className="pb-4">
        <div className="relative">
          <div className="absolute left-5 top-2 bottom-2 w-px bg-border" />
          <div className="space-y-4">
            {events.map((event, i) => {
              const kind = event.type || event.kind || "other";
              const Icon = ICONS[kind] || Circle;
              const dot = event.color || DOT[kind] || DOT.default;
              return (
                <div key={i} className="relative flex gap-4 pl-2">
                  <div
                    className="relative z-10 h-7 w-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                    style={{ backgroundColor: dot }}
                  >
                    <Icon className="h-3.5 w-3.5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-2 flex-wrap">
                      <span className="text-sm font-medium leading-tight">{event.title}</span>
                      {(event.badge || (kind && kind !== "other")) && (
                        <Badge variant="outline" className={`text-xs h-5 px-1.5 ${BADGE[kind] || BADGE.default}`}>
                          {event.badge || kind}
                        </Badge>
                      )}
                    </div>
                    {event.description && (
                      <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{event.description}</p>
                    )}
                    {event.date && <p className="text-xs text-muted-foreground/70 mt-0.5">{event.date}</p>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        {events.length === 0 && <p className="text-sm text-muted-foreground text-center py-4">No events.</p>}
      </CardContent>
    </Card>
  );
}
