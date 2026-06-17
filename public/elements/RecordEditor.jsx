import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Target, Calendar, Edit, Save, X, Plus, Trash2, FileText, Briefcase, Flag, Layers,
} from "lucide-react";

const ICONS = { target: Target, file: FileText, briefcase: Briefcase, flag: Flag, layers: Layers };

const DEFAULT_STATUS = {
  draft: "Draft",
  on_track: "On Track",
  at_risk: "At Risk",
  behind: "Behind",
  complete: "Complete",
  planned: "Planned",
  blocked: "Blocked",
};

const STATUS_CLASS = {
  draft: "bg-muted text-muted-foreground",
  on_track: "bg-green-500/15 text-green-700 border-green-300",
  at_risk: "bg-yellow-500/15 text-yellow-700 border-yellow-300",
  behind: "bg-red-500/15 text-red-700 border-red-300",
  complete: "bg-blue-500/15 text-blue-700 border-blue-300",
  planned: "bg-slate-500/15 text-slate-700 border-slate-300",
  blocked: "bg-red-500/15 text-red-700 border-red-300",
};

function initItems(raw) {
  return (raw || []).map((row, i) => {
    if (typeof row === "string") return { id: i, text: row, complete: false };
    return {
      id: row.id ?? i,
      text: row.text || row.title || row.label || "",
      complete: !!row.complete,
      status: row.status,
    };
  });
}

export default function RecordEditor() {
  const [editing, setEditing] = useState(props.edit_mode === true);
  const [title, setTitle] = useState(props.title || "");
  const [description, setDescription] = useState(props.description || props.body || "");
  const [dueDate, setDueDate] = useState(props.due_date || "");
  const [status, setStatus] = useState(props.status || "on_track");
  const [fieldValues, setFieldValues] = useState(() => {
    const v = {};
    (props.fields || []).forEach((f) => { v[f.id] = f.value ?? ""; });
    return v;
  });

  const itemsLabel = props.items_label || props.sub_items_label || "Items";
  const showItems = props.show_items !== false;
  const [items, setItems] = useState(() => initItems(props.items || props.key_results));

  const statusOptions = useMemo(() => {
    if (props.status_options?.length) {
      return props.status_options.map((o) =>
        typeof o === "string" ? { value: o, label: o.replace(/_/g, " ") } : { value: o.value, label: o.label || o.value }
      );
    }
    const labels = props.status_labels || DEFAULT_STATUS;
    return Object.entries(labels).map(([value, label]) => ({ value, label }));
  }, [props.status_options, props.status_labels]);

  const extraFields = props.fields || [];
  const HeaderIcon = ICONS[(props.icon || "target").toLowerCase()] || Target;
  const saveLabel = props.save_label || "Save";
  const statusOnChangeLive = props.status_live_update !== false;

  const toggleItem = (id) =>
    setItems((prev) => prev.map((r) => (r.id === id ? { ...r, complete: !r.complete } : r)));

  const addItem = () => setItems((prev) => [...prev, { id: Date.now(), text: "", complete: false }]);
  const updateItemText = (id, text) =>
    setItems((prev) => prev.map((r) => (r.id === id ? { ...r, text } : r)));
  const removeItem = (id) => setItems((prev) => prev.filter((r) => r.id !== id));

  const buildPayload = () => ({
    title,
    description,
    due_date: dueDate,
    status,
    owner: props.owner,
    fields: extraFields.map((f) => ({ id: f.id, label: f.label, value: fieldValues[f.id] || "" })),
    items: items.map(({ id, text, complete, status: st }) => ({ text, complete, status: st })),
    key_results: items.map(({ text, complete }) => ({ text, complete })),
  });

  const handleSave = () => {
    setEditing(false);
    callAction({ name: "record_editor_save", payload: buildPayload() });
  };

  const handleStatusChange = (val) => {
    setStatus(val);
    if (!editing && statusOnChangeLive) {
      callAction({ name: "record_editor_status", payload: { status: val, title } });
    }
  };

  const statusLabel = (v) => {
    const o = statusOptions.find((x) => x.value === v);
    return o?.label || DEFAULT_STATUS[v] || v;
  };

  return (
    <Card className="mt-3 w-full max-w-lg">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <HeaderIcon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            {editing ? (
              <Input value={title} onChange={(e) => setTitle(e.target.value)} className="text-base font-semibold" placeholder="Title" />
            ) : (
              <CardTitle className="text-base leading-snug">{title || "Untitled"}</CardTitle>
            )}
          </div>
          {props.editable !== false && (
            <Button variant="ghost" size="icon" className="flex-shrink-0" onClick={() => setEditing(!editing)}>
              {editing ? <X className="h-4 w-4" /> : <Edit className="h-4 w-4" />}
            </Button>
          )}
        </div>
        {(props.subtitle || props.owner) && !editing && (
          <p className="text-xs text-muted-foreground mt-1">{props.subtitle}{props.owner ? ` · ${props.owner}` : ""}</p>
        )}
        <div className="flex items-center gap-2 mt-2 flex-wrap">
          {props.show_status !== false && (
            <Select value={status} onValueChange={handleStatusChange}>
              <SelectTrigger className="w-auto h-7 text-xs border-0 p-0 focus:ring-0">
                <Badge variant="outline" className={`${STATUS_CLASS[status] || ""} cursor-pointer capitalize`}>
                  {statusLabel(status)}
                </Badge>
              </SelectTrigger>
              <SelectContent>
                {statusOptions.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          {dueDate && (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              Due {dueDate}
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pb-2">
        {editing ? (
          <>
            <div className="space-y-1">
              <Label className="text-xs">Description</Label>
              <Textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} placeholder="Description..." />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Due date</Label>
              <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </div>
            {extraFields.map((f) => (
              <div key={f.id} className="space-y-1">
                <Label className="text-xs">{f.label}</Label>
                {f.type === "textarea" ? (
                  <Textarea
                    value={fieldValues[f.id] || ""}
                    onChange={(e) => setFieldValues((v) => ({ ...v, [f.id]: e.target.value }))}
                    rows={f.rows || 2}
                    className="text-sm"
                  />
                ) : f.type === "select" ? (
                  <Select value={fieldValues[f.id] || ""} onValueChange={(x) => setFieldValues((v) => ({ ...v, [f.id]: x }))}>
                    <SelectTrigger className="h-8 text-sm"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {(f.options || []).map((o) => {
                        const val = typeof o === "string" ? o : o.value;
                        const lab = typeof o === "string" ? o : o.label;
                        return <SelectItem key={val} value={val}>{lab}</SelectItem>;
                      })}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    type={f.type === "date" ? "date" : "text"}
                    value={fieldValues[f.id] || ""}
                    onChange={(e) => setFieldValues((v) => ({ ...v, [f.id]: e.target.value }))}
                    className="h-8 text-sm"
                  />
                )}
              </div>
            ))}
          </>
        ) : (
          <>
            {description && <p className="text-sm text-muted-foreground">{description}</p>}
            {extraFields.map((f) => fieldValues[f.id] && (
              <div key={f.id} className="text-sm">
                <span className="text-muted-foreground">{f.label}: </span>
                <span>{fieldValues[f.id]}</span>
              </div>
            ))}
          </>
        )}

        {showItems && items.length > 0 && (
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">{itemsLabel}</Label>
            {items.map((row) => (
              <div key={row.id} className="flex items-center gap-2">
                <Checkbox checked={row.complete} onCheckedChange={() => toggleItem(row.id)} disabled={editing && false} />
                {editing ? (
                  <>
                    <Input value={row.text} onChange={(e) => updateItemText(row.id, e.target.value)} className="h-7 text-sm flex-1" />
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => removeItem(row.id)}>
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </>
                ) : (
                  <span className={`text-sm flex-1 ${row.complete ? "line-through text-muted-foreground" : ""}`}>{row.text}</span>
                )}
              </div>
            ))}
          </div>
        )}
        {editing && showItems && props.allow_add_items !== false && (
          <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={addItem}>
            <Plus className="h-3 w-3 mr-1" />Add {itemsLabel.toLowerCase()}
          </Button>
        )}
      </CardContent>

      {editing && (
        <CardFooter className="gap-2 justify-end">
          <Button variant="outline" size="sm" onClick={() => setEditing(false)}>Cancel</Button>
          <Button size="sm" onClick={handleSave}>
            <Save className="h-3.5 w-3.5 mr-1" />{saveLabel}
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}
