import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GripVertical, Check } from "lucide-react";

function normalizeItems(raw) {
  return (raw || []).map((entry, i) => {
    if (entry && typeof entry === "object") {
      const label = entry.label || entry.title || entry.name || "";
      return { id: entry.id ?? `rank-${i}`, label: String(label || entry) };
    }
    const label = String(entry);
    return { id: `rank-${i}-${label.slice(0, 32)}`, label };
  });
}

export default function DraggableRank() {
  const title = props.title || "Rank these items";
  const instruction = props.instruction || "Drag to reorder. Top = highest priority.";

  const [items, setItems] = useState(() => normalizeItems(props.items));
  const [draggedIndex, setDraggedIndex] = useState(null);
  const [overIndex, setOverIndex] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const dragFrom = useRef(null);
  const dragTo = useRef(null);

  const reorder = (from, to) => {
    if (from === null || to === null || from === to) return;
    setItems((prev) => {
      const next = [...prev];
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });
  };

  const handleDragStart = (e, i) => {
    dragFrom.current = i;
    dragTo.current = i;
    setDraggedIndex(i);
    setOverIndex(i);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", String(i));
  };

  const handleDragOver = (e, i) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    dragTo.current = i;
    if (draggedIndex !== null) setOverIndex(i);
  };

  const handleDrop = (e, i) => {
    e.preventDefault();
    dragTo.current = i;
    setOverIndex(i);
  };

  const handleDragEnd = () => {
    const from = dragFrom.current;
    const to = dragTo.current;
    if (from !== null && to !== null) reorder(from, to);
    dragFrom.current = null;
    dragTo.current = null;
    setDraggedIndex(null);
    setOverIndex(null);
  };

  const handleSubmit = () => {
    setSubmitted(true);
    const ranked = items.map((x) => x.label);
    callAction({ name: "rank_submit", payload: { ranked } });
  };

  if (submitted) {
    return (
      <Card className="mt-3 w-full max-w-md">
        <CardContent className="pt-4">
          <div className="flex items-center gap-2 text-sm mb-2">
            <Check className="h-4 w-4 text-green-500" />
            <span>Ranking submitted:</span>
          </div>
          <ol className="space-y-1">
            {items.map((item, i) => (
              <li key={item.id} className="flex items-center gap-2 text-sm">
                <Badge variant="outline" className="w-6 h-6 flex items-center justify-center p-0 text-xs">{i + 1}</Badge>
                <span>{item.label}</span>
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-3 w-full max-w-md">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{instruction}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 pb-2">
        {items.map((item, i) => (
          <div
            key={item.id}
            draggable
            onDragStart={(e) => handleDragStart(e, i)}
            onDragOver={(e) => handleDragOver(e, i)}
            onDrop={(e) => handleDrop(e, i)}
            onDragEnd={handleDragEnd}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg border bg-card text-sm cursor-grab active:cursor-grabbing select-none transition-all ${
              draggedIndex === i ? "opacity-50 border-primary/50" : ""
            } ${overIndex === i && draggedIndex !== null && draggedIndex !== i ? "border-primary bg-muted/40" : ""}`}
          >
            <GripVertical className="h-4 w-4 text-muted-foreground flex-shrink-0 pointer-events-none" />
            <Badge variant="outline" className="w-6 h-6 flex items-center justify-center p-0 text-xs flex-shrink-0">
              {i + 1}
            </Badge>
            <span className="flex-1">{item.label}</span>
          </div>
        ))}
      </CardContent>
      <CardFooter>
        <Button className="w-full" onClick={handleSubmit}>
          Submit Ranking
        </Button>
      </CardFooter>
    </Card>
  );
}
