import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ChevronRight, List } from "lucide-react";

const STATUS_STYLES = {
  on_track: "bg-green-500/15 text-green-700 border-green-300",
  at_risk: "bg-yellow-500/15 text-yellow-700 border-yellow-300",
  behind: "bg-red-500/15 text-red-700 border-red-300",
  complete: "bg-blue-500/15 text-blue-700 border-blue-300",
  draft: "bg-muted text-muted-foreground",
  success: "bg-green-500/15 text-green-700 border-green-300",
  warning: "bg-yellow-500/15 text-yellow-700 border-yellow-300",
  danger: "bg-red-500/15 text-red-700 border-red-300",
  info: "bg-blue-500/15 text-blue-700 border-blue-300",
};

const PROGRESS_INDICATOR = {
  on_track: "[&>div]:bg-green-500",
  at_risk: "[&>div]:bg-yellow-500",
  behind: "[&>div]:bg-red-500",
  complete: "[&>div]:bg-blue-500",
  draft: "[&>div]:bg-slate-400",
  success: "[&>div]:bg-green-500",
  warning: "[&>div]:bg-yellow-500",
  danger: "[&>div]:bg-red-500",
  info: "[&>div]:bg-blue-500",
};

export default function ProgressList() {
  const title = props.title || "Progress";
  const clickable = props.clickable !== false;
  const items = props.items?.length
    ? props.items
    : (props.goals || []).map((g) => ({
        id: g.id,
        title: g.title,
        subtitle: g.subtitle || g.owner,
        progress: g.progress,
        status: g.status,
        badge: g.badge,
      }));

  const handleClick = (item) => {
    if (!clickable) return;
    callAction({
      name: "progress_list_select",
      payload: { id: item.id, title: item.title, item },
    });
  };

  return (
    <Card className="mt-3 w-full max-w-lg">
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <List className="h-4 w-4 text-muted-foreground" />
          {title}
        </CardTitle>
        {props.subtitle && <p className="text-xs text-muted-foreground">{props.subtitle}</p>}
      </CardHeader>
      <CardContent className="space-y-2 pb-3">
        {items.map((item, i) => {
          const pct = Math.min(100, Math.max(0, item.progress ?? 0));
          const badgeText = item.badge || (item.status ? String(item.status).replace(/_/g, " ") : null);
          const progressClass = PROGRESS_INDICATOR[item.status] || "[&>div]:bg-primary";
          return (
            <div
              key={item.id || i}
              className={`group flex flex-col gap-1 rounded-lg border p-3 transition-colors ${clickable ? "cursor-pointer hover:border-primary/50 hover:bg-muted/30" : ""}`}
              onClick={() => handleClick(item)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <span className="text-sm font-medium leading-snug block truncate">{item.title}</span>
                  {item.subtitle && <span className="text-xs text-muted-foreground">{item.subtitle}</span>}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {badgeText && (
                    <Badge variant="outline" className={`text-xs capitalize ${STATUS_STYLES[item.status] || ""}`}>
                      {badgeText}
                    </Badge>
                  )}
                  {clickable && (
                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground group-hover:text-foreground" />
                  )}
                </div>
              </div>
              {item.progress != null && (
                <div className="flex items-center gap-2 mt-0.5">
                  <Progress value={pct} className={`h-2 flex-1 ${progressClass}`} />
                  <span className="text-xs text-muted-foreground w-8 text-right tabular-nums">{pct}%</span>
                </div>
              )}
            </div>
          );
        })}
        {items.length === 0 && <p className="text-sm text-muted-foreground text-center py-4">No items.</p>}
      </CardContent>
    </Card>
  );
}
