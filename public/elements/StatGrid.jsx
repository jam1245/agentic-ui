import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  TrendingUp, TrendingDown, Minus, Target, Users, Star, Zap, Trophy, BarChart2,
} from "lucide-react";

const ICONS = {
  target: Target, users: Users, star: Star, zap: Zap, trophy: Trophy, chart: BarChart2,
};

const TREND = {
  up: { Icon: TrendingUp, color: "#16a34a", bg: "rgba(22,163,74,0.1)" },
  down: { Icon: TrendingDown, color: "#dc2626", bg: "rgba(220,38,38,0.1)" },
  neutral: { Icon: Minus, color: "#64748b", bg: "rgba(100,116,139,0.1)" },
};

export default function StatGrid() {
  const title = props.title || "";
  const stats = props.stats || props.metrics || [];
  const columns = Math.min(4, Math.max(1, Number(props.columns) || (stats.length <= 2 ? stats.length || 2 : 3)));
  const clickable = props.clickable === true;

  const handleClick = (stat) => {
    if (!clickable) return;
    callAction({
      name: "stat_grid_select",
      payload: { id: stat.id, label: stat.label, value: stat.value },
    });
  };

  return (
    <Card className="mt-3 w-full max-w-xl">
      {title && (
        <CardHeader className="pb-2">
          <CardTitle className="text-base">{title}</CardTitle>
          {props.subtitle && <p className="text-xs text-muted-foreground mt-1">{props.subtitle}</p>}
        </CardHeader>
      )}
      <CardContent className={title ? "pt-0" : "pt-4"}>
        <div
          className="grid gap-3"
          style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
        >
          {stats.map((stat, i) => {
            const trendKey = (stat.trend || "neutral").toLowerCase();
            const t = TREND[trendKey] || TREND.neutral;
            const TrendIcon = t.Icon;
            const StatIcon = ICONS[(stat.icon || "").toLowerCase()];
            const delta = stat.delta ?? stat.change;
            const Wrapper = clickable ? "button" : "div";

            return (
              <Wrapper
                key={stat.id || i}
                type={clickable ? "button" : undefined}
                onClick={clickable ? () => handleClick(stat) : undefined}
                className={`rounded-lg border p-3 text-left min-w-0 ${
                  clickable ? "cursor-pointer hover:border-primary/40 hover:bg-muted/30 transition-colors" : "bg-card"
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="text-xs font-medium text-muted-foreground truncate">{stat.label}</span>
                  {StatIcon && <StatIcon className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />}
                </div>
                <div className="text-xl font-semibold tracking-tight tabular-nums">
                  {stat.value}
                  {stat.suffix && <span className="text-sm font-normal text-muted-foreground ml-0.5">{stat.suffix}</span>}
                </div>
                {(delta != null && delta !== "") && (
                  <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                    <span
                      className="inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-xs font-medium"
                      style={{ color: t.color, backgroundColor: t.bg }}
                    >
                      <TrendIcon className="h-3 w-3" />
                      {delta}
                    </span>
                    {stat.delta_label && (
                      <span className="text-xs text-muted-foreground">{stat.delta_label}</span>
                    )}
                  </div>
                )}
                {stat.hint && <p className="text-xs text-muted-foreground mt-1.5">{stat.hint}</p>}
              </Wrapper>
            );
          })}
        </div>
        {stats.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4">No metrics.</p>
        )}
      </CardContent>
    </Card>
  );
}
