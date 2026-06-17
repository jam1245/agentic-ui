import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GripVertical, Check } from "lucide-react";

export default function DraggableCategories() {
  const title = props.title || "Categorize these items";
  const instruction = props.instruction || "Drag pills between columns to categorize them.";

  const [cols, setCols] = useState(
    (props.columns || []).map((c) => ({ name: c.name, items: c.items || [] }))
  );
  const [dragged, setDragged] = useState(null); // {colIdx, itemIdx, item}
  const [dragOverCol, setDragOverCol] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const startDrag = (e, colIdx, itemIdx) => {
    const item = cols[colIdx].items[itemIdx];
    setDragged({ colIdx, itemIdx, item });
    e.dataTransfer.effectAllowed = "move";
  };

  const moveItem = (targetColIdx, insertBefore) => {
    if (!dragged) return;
    setCols((prev) => {
      const next = prev.map((c) => ({ ...c, items: [...c.items] }));
      next[dragged.colIdx].items.splice(dragged.itemIdx, 1);
      if (insertBefore !== undefined) {
        // Adjust index if moving within the same column after the source
        const adj =
          targetColIdx === dragged.colIdx && insertBefore > dragged.itemIdx
            ? insertBefore - 1
            : insertBefore;
        next[targetColIdx].items.splice(adj, 0, dragged.item);
      } else {
        next[targetColIdx].items.push(dragged.item);
      }
      return next;
    });
    setDragged(null);
    setDragOverCol(null);
  };

  const handleItemDragOver = (e) => { e.preventDefault(); e.stopPropagation(); };
  const handleItemDrop = (e, colIdx, itemIdx) => {
    e.preventDefault();
    e.stopPropagation();
    moveItem(colIdx, itemIdx);
  };

  const handleColDragOver = (e, colIdx) => {
    e.preventDefault();
    setDragOverCol(colIdx);
  };
  const handleColDrop = (e, colIdx) => {
    e.preventDefault();
    moveItem(colIdx);
  };

  const handleSubmit = () => {
    setSubmitted(true);
    callAction({
      name: "categories_submit",
      payload: { columns: cols.map((c) => ({ name: c.name, items: c.items })) },
    });
  };

  const gridCols = cols.length === 2 ? "grid-cols-2" : "grid-cols-3";

  if (submitted) {
    return (
      <Card className="mt-3 w-full">
        <CardContent className="pt-4">
          <div className="flex items-center gap-2 text-sm mb-3">
            <Check className="h-4 w-4 text-green-500" />
            <span>Categorization submitted:</span>
          </div>
          <div className={`grid ${gridCols} gap-3`}>
            {cols.map((col, ci) => (
              <div key={ci}>
                <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1">
                  {col.name}
                </div>
                <div className="flex flex-col gap-1">
                  {col.items.map((item, ii) => (
                    <Badge key={ii} variant="secondary" className="justify-start">{item}</Badge>
                  ))}
                  {col.items.length === 0 && (
                    <span className="text-xs text-muted-foreground italic">empty</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-3 w-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{instruction}</CardDescription>
      </CardHeader>
      <CardContent className="pb-2">
        <div className={`grid ${gridCols} gap-3`}>
          {cols.map((col, colIdx) => (
            <div
              key={colIdx}
              onDragOver={(e) => handleColDragOver(e, colIdx)}
              onDrop={(e) => handleColDrop(e, colIdx)}
              className={`min-h-24 rounded-lg border-2 border-dashed p-2 transition-colors ${
                dragOverCol === colIdx ? "border-primary bg-primary/5" : "border-border"
              }`}
            >
              <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 px-1">
                {col.name}
                <Badge variant="outline" className="ml-2 text-xs">{col.items.length}</Badge>
              </div>
              <div className="flex flex-col gap-1.5">
                {col.items.map((item, itemIdx) => (
                  <div
                    key={`${colIdx}-${itemIdx}-${item}`}
                    draggable
                    onDragStart={(e) => startDrag(e, colIdx, itemIdx)}
                    onDragOver={handleItemDragOver}
                    onDrop={(e) => handleItemDrop(e, colIdx, itemIdx)}
                    onDragEnd={() => { setDragged(null); setDragOverCol(null); }}
                    className={`flex items-center gap-2 px-2 py-1.5 rounded-md border bg-card text-sm cursor-grab active:cursor-grabbing select-none transition-opacity ${
                      dragged?.colIdx === colIdx && dragged?.itemIdx === itemIdx
                        ? "opacity-30"
                        : "opacity-100"
                    }`}
                  >
                    <GripVertical className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                    <span className="flex-1 truncate">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
      <CardFooter>
        <Button className="w-full" onClick={handleSubmit}>
          Submit Categorization
        </Button>
      </CardFooter>
    </Card>
  );
}
