import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Plus, Trash2, ChevronUp, ChevronDown, ChevronRight, Check, Calendar } from "lucide-react";

const SCROLL_THRESHOLD = 5;

const MINUTE_OPTIONS = [5, 10, 15, 20, 30];

function initRows() {
  const preset = props.preset || "custom";
  const raw = props.rows || props.topics || props.items || [];
  if (preset === "agenda") {
    return raw.map((t, i) => ({
      id: t.id ?? i,
      title: t.title || "",
      talking_points: t.talking_points || t.notes || "",
      minutes: t.minutes ?? 10,
      expanded: false,
    }));
  }
  if (preset === "tasks") {
    return raw.map((t, i) => ({
      id: t.id ?? i,
      text: t.text || t.title || "",
      complete: t.complete || false,
      notes: t.notes || "",
      due_date: t.due_date || "",
      expanded: false,
    }));
  }
  return raw.map((r, i) => ({ id: r.id ?? i, ...r, expanded: r.expanded || false }));
}

export default function EditableList() {
  const title = props.title || "List";
  const subtitle = props.subtitle || [props.employee, props.date, props.check_in_type, props.from_date].filter(Boolean).join(" - ");
  const preset = props.preset || (props.topics ? "agenda" : props.items ? "tasks" : "custom");
  const submitLabel = props.submit_label || "Submit";
  const addLabel = props.add_label || (preset === "agenda" ? "Add topic" : "Add item");
  const showReorder = props.show_reorder !== false && preset === "agenda";

  const [rows, setRows] = useState(initRows);
  const [submitted, setSubmitted] = useState(false);

  const update = (id, field, val) =>
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, [field]: val } : r)));

  const remove = (id) => setRows((prev) => prev.filter((r) => r.id !== id));

  const add = () => {
    const id = Date.now();
    if (preset === "agenda") {
      setRows((prev) => [...prev, { id, title: "", talking_points: "", minutes: 10, expanded: true }]);
    } else if (preset === "tasks") {
      setRows((prev) => [...prev, { id, text: "", complete: false, notes: "", due_date: "", expanded: false }]);
    } else {
      setRows((prev) => [...prev, { id, title: "", expanded: false }]);
    }
  };

  const move = (idx, dir) => {
    const next = [...rows];
    const target = idx + dir;
    if (target < 0 || target >= next.length) return;
    [next[idx], next[target]] = [next[target], next[idx]];
    setRows(next);
  };

  const totalMins = preset === "agenda" ? rows.reduce((s, r) => s + (r.minutes || 0), 0) : 0;
  const doneCount = preset === "tasks" ? rows.filter((r) => r.complete).length : 0;

  const handleSubmit = () => {
    setSubmitted(true);
    callAction({
      name: "editable_list_submit",
      payload: {
        title,
        preset,
        rows: rows.map(({ id, expanded, ...rest }) => rest),
        total_minutes: totalMins,
        completed: doneCount,
        total: rows.length,
      },
    });
  };

  if (submitted) {
    return (
      <Card className="mt-3 w-full max-w-lg">
        <CardContent className="pt-4 flex items-center gap-2 text-sm">
          <Check className="h-4 w-4 text-green-500" />
          {preset === "tasks"
            ? `${doneCount} of ${rows.length} items updated.`
            : `Submitted (${totalMins || rows.length} ${preset === "agenda" ? "min" : "rows"}).`}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-3 w-full max-w-lg">
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center justify-between gap-2">
          <span>{title}</span>
          {preset === "tasks" && (
            <Badge variant="outline" className="text-xs">{doneCount}/{rows.length} done</Badge>
          )}
        </CardTitle>
        {(subtitle || totalMins > 0) && (
          <CardDescription>
            {subtitle}
            {totalMins > 0 && <span className="ml-2">{totalMins} min total</span>}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-2 pb-2">
        {(() => {
          const rowList = rows.map((row, idx) => (
          <div
            key={row.id}
            className={`rounded-lg border p-3 space-y-2 ${preset === "tasks" && row.complete ? "opacity-60" : ""}`}
          >
            {preset === "agenda" && (
              <>
                <div className="flex items-center gap-2">
                  {showReorder && (
                    <div className="flex flex-col gap-0.5">
                      <button type="button" onClick={() => move(idx, -1)} disabled={idx === 0} className="text-muted-foreground disabled:opacity-30">
                        <ChevronUp className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" onClick={() => move(idx, 1)} disabled={idx === rows.length - 1} className="text-muted-foreground disabled:opacity-30">
                        <ChevronDown className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}
                  <Badge variant="outline" className="w-6 h-6 flex items-center justify-center p-0 text-xs">{idx + 1}</Badge>
                  <Input
                    value={row.title}
                    onChange={(e) => update(row.id, "title", e.target.value)}
                    placeholder="Title..."
                    className="h-7 text-sm flex-1"
                  />
                  <select
                    value={row.minutes}
                    onChange={(e) => update(row.id, "minutes", Number(e.target.value))}
                    className="h-7 text-xs rounded border bg-background px-1"
                  >
                    {MINUTE_OPTIONS.map((m) => (
                      <option key={m} value={m}>{m}m</option>
                    ))}
                  </select>
                  <button type="button" onClick={() => update(row.id, "expanded", !row.expanded)} className="text-muted-foreground">
                    <ChevronRight className={`h-3.5 w-3.5 transition-transform ${row.expanded ? "rotate-90" : ""}`} />
                  </button>
                  <button type="button" onClick={() => remove(row.id)} className="text-muted-foreground hover:text-destructive">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
                {row.expanded && (
                  <Textarea
                    value={row.talking_points}
                    onChange={(e) => update(row.id, "talking_points", e.target.value)}
                    placeholder="Notes, talking points..."
                    rows={3}
                    className="text-xs"
                  />
                )}
              </>
            )}
            {preset === "tasks" && (
              <>
                <div className="flex items-center gap-2">
                  <Checkbox checked={row.complete} onCheckedChange={() => update(row.id, "complete", !row.complete)} />
                  <Input
                    value={row.text}
                    onChange={(e) => update(row.id, "text", e.target.value)}
                    className={`h-7 text-sm flex-1 border-0 focus-visible:ring-0 p-0 bg-transparent ${row.complete ? "line-through text-muted-foreground" : ""}`}
                    placeholder="Item..."
                  />
                  {row.due_date && (
                    <span className="text-xs text-muted-foreground flex items-center gap-0.5">
                      <Calendar className="h-3 w-3" />{row.due_date}
                    </span>
                  )}
                  <button type="button" onClick={() => update(row.id, "expanded", !row.expanded)} className="text-muted-foreground">
                    <ChevronRight className={`h-3.5 w-3.5 transition-transform ${row.expanded ? "rotate-90" : ""}`} />
                  </button>
                  <button type="button" onClick={() => remove(row.id)} className="text-muted-foreground hover:text-destructive">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
                {row.expanded && (
                  <div className="pl-6 space-y-1.5">
                    <Textarea value={row.notes} onChange={(e) => update(row.id, "notes", e.target.value)} placeholder="Notes..." rows={2} className="text-xs" />
                    <Input type="date" value={row.due_date} onChange={(e) => update(row.id, "due_date", e.target.value)} className="h-7 text-xs" />
                  </div>
                )}
              </>
            )}
            {preset === "custom" && (
              <div className="flex items-center gap-2">
                <Input value={row.title || row.text || ""} onChange={(e) => update(row.id, "title", e.target.value)} className="flex-1 h-8 text-sm" />
                <button type="button" onClick={() => remove(row.id)}><Trash2 className="h-3.5 w-3.5" /></button>
              </div>
            )}
          </div>
        ));
          return (
            <>
              {rows.length > SCROLL_THRESHOLD ? (
                <ScrollArea className="max-h-[400px] w-full pr-3 mb-2">
                  <div className="space-y-2">{rowList}</div>
                </ScrollArea>
              ) : (
                <div className="space-y-2">{rowList}</div>
              )}
              <Button variant="ghost" size="sm" className="w-full h-8 text-xs border-dashed border" onClick={add}>
                <Plus className="h-3.5 w-3.5 mr-1" />{addLabel}
              </Button>
            </>
          );
        })()}
      </CardContent>
      <CardFooter>
        <Button className="w-full" disabled={rows.length === 0} onClick={handleSubmit}>
          {submitLabel}
        </Button>
      </CardFooter>
    </Card>
  );
}
