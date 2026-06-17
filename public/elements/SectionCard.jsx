import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const SECTION_COLORS = {
  green: "bg-green-500/10 border-green-200 text-green-800",
  amber: "bg-amber-500/10 border-amber-200 text-amber-800",
  blue: "bg-blue-500/10 border-blue-200 text-blue-800",
  purple: "bg-purple-500/10 border-purple-200 text-purple-800",
  red: "bg-red-500/10 border-red-200 text-red-800",
  default: "bg-muted/30 border-border text-foreground",
};

const BADGE_STYLES = {
  success: "bg-green-500/15 text-green-700 border-green-300",
  warning: "bg-amber-500/15 text-amber-700 border-amber-300",
  danger: "bg-red-500/15 text-red-700 border-red-300",
  info: "bg-blue-500/15 text-blue-700 border-blue-300",
  default: "",
};

export default function SectionCard() {
  const title = props.title || "";
  const subtitle = props.subtitle;
  const headerBadges = props.header_badges || [];
  const headerFields = props.header_fields || [];
  const sections = props.sections || [];

  return (
    <Card className="mt-3 w-full max-w-lg">
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            {title && <div className="text-base font-semibold">{title}</div>}
            {subtitle && <div className="mt-0.5 text-xs text-muted-foreground">{subtitle}</div>}
          </div>
          {headerBadges.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {headerBadges.map((b, i) => (
                <Badge key={i} variant="outline" className={`text-xs ${BADGE_STYLES[b.style] || ""}`}>
                  {b.label}
                </Badge>
              ))}
            </div>
          )}
        </div>
        {headerFields.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-3">
            {headerFields.map((f, i) => (
              <div key={i} className="flex items-center gap-1 text-xs text-muted-foreground">
                <span className="font-medium">{f.label}:</span>
                <span>{f.value}</span>
              </div>
            ))}
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-2 pb-4">
        {sections.map((sec, i) => (
          <div
            key={i}
            className={`rounded-md border p-3 ${SECTION_COLORS[sec.color] || SECTION_COLORS.default}`}
          >
            {sec.title && <div className="mb-1 text-xs font-semibold">{sec.title}</div>}
            <p className="text-sm leading-relaxed">{sec.content}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
