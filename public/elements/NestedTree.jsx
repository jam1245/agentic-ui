import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChevronRight, ChevronDown, Trophy, Users, Target, Circle, Folder, FileText } from "lucide-react";

const LEVEL_ICONS = {
  company: Trophy,
  team: Users,
  individual: Target,
  group: Users,
  folder: Folder,
  item: FileText,
};

const STATUS_DOT = {
  on_track: "#22c55e",
  at_risk: "#eab308",
  behind: "#ef4444",
  complete: "#3b82f6",
  draft: "#94a3b8",
  success: "#22c55e",
  warning: "#eab308",
  danger: "#ef4444",
};

export default function NestedTree() {
  const title = props.title || "Tree";
  const nodes = props.nodes || [];
  const showLegend = props.show_legend !== false;
  const [collapsed, setCollapsed] = useState(new Set());

  const toggle = (id) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const renderNodes = (nodeList, depth) =>
    nodeList.map((node) => {
      const Icon = LEVEL_ICONS[node.icon || node.level] || Circle;
      const hasChildren = node.children?.length > 0;
      const nodeId = node.id || node.title;
      const isCollapsed = collapsed.has(nodeId);

      return (
        <div key={nodeId}>
          <div
            className={`flex items-center gap-2 py-1.5 px-2 rounded-md ${hasChildren ? "cursor-pointer hover:bg-muted/50" : ""}`}
            style={{ paddingLeft: `${depth * 20 + 8}px` }}
            onClick={() => hasChildren && toggle(nodeId)}
          >
            {hasChildren ? (
              isCollapsed ? (
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
              )
            ) : (
              <span className="w-3.5 flex-shrink-0" />
            )}
            <Icon className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
            <span
              className={`text-sm flex-1 truncate ${depth === 0 ? "font-semibold" : depth === 1 ? "font-medium" : ""}`}
            >
              {node.title}
            </span>
            {node.status && (
              <span
                className="h-2 w-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: STATUS_DOT[node.status] || "#94a3b8" }}
              />
            )}
            {(node.badge || node.level_label) && (
              <Badge variant="outline" className="text-xs h-5 px-1.5 flex-shrink-0 capitalize">
                {node.badge || node.level_label}
              </Badge>
            )}
          </div>
          {hasChildren && !isCollapsed && <div>{renderNodes(node.children, depth + 1)}</div>}
        </div>
      );
    });

  return (
    <Card className="mt-3 w-full max-w-lg">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        {props.subtitle && <p className="text-xs text-muted-foreground">{props.subtitle}</p>}
        {showLegend && (
          <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1 flex-wrap">
            {Object.entries(STATUS_DOT).slice(0, 5).map(([key, color]) => (
              <span key={key} className="flex items-center gap-1 capitalize">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
                {key.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        )}
      </CardHeader>
      <CardContent className="pb-3">
        {nodes.length ? (
          <ScrollArea className="max-h-[400px] w-full pr-3">
            {renderNodes(nodes, 0)}
          </ScrollArea>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-4">No nodes.</p>
        )}
      </CardContent>
    </Card>
  );
}
