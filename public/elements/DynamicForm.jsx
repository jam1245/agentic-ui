import { useState, useMemo, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Calendar, Check, Save } from "lucide-react";

const DEFAULT_MAX = 2000;
const FIELD_TYPES = new Set([
  "text", "email", "number", "date", "textarea", "select", "radio",
  "checkbox", "switch", "multiselect", "heading", "divider",
]);

function normalizeOption(opt) {
  if (typeof opt === "string") return { value: opt, label: opt };
  const value = String(opt.value ?? opt.id ?? opt.label ?? "");
  return { value, label: opt.label ?? opt.name ?? value };
}

function normalizeField(raw) {
  const f = raw || {};
  const type = FIELD_TYPES.has(f.type) ? f.type : "text";
  let value = f.value;
  if (value === undefined || value === null) {
    if (type === "checkbox" || type === "switch") value = false;
    else if (type === "multiselect") value = [];
    else value = "";
  }
  if (type === "multiselect" && !Array.isArray(value)) value = [];
  return {
    id: f.id,
    label: f.label || f.title || f.id,
    type,
    placeholder: f.placeholder || "",
    required: f.required !== false && type !== "heading" && type !== "divider",
    value,
    options: (f.options || []).map(normalizeOption),
    col_span: f.col_span ?? (f.full_width ? 2 : 1),
    rows: f.rows,
    max_chars: f.max_chars,
    help: f.help || f.description || "",
    min: f.min,
    max: f.max,
  };
}

function fieldById(fields) {
  return Object.fromEntries(fields.map((f) => [f.id, f]));
}

function isFieldFilled(f, v) {
  if (f.type === "checkbox" || f.type === "switch") return !!v;
  if (f.type === "multiselect") return Array.isArray(v) && v.length > 0;
  if (f.type === "heading" || f.type === "divider") return true;
  return String(v ?? "").trim().length > 0;
}

export default function DynamicForm() {
  const title = props.title || "Form";
  const subtitle = props.subtitle || props.employee_name || "";
  const description = props.description || "";
  const dueDate = props.due_date || props.badge || "";
  const submitLabel = props.submit_label || "Submit";
  const askMode = props.ask_mode === true;
  const showCancel = props.show_cancel !== false && askMode;
  const showDraft = !askMode && props.show_draft !== false;
  const timeout = props.timeout;
  const defaultMax = props.max_chars ?? DEFAULT_MAX;
  const compact = props.compact === true || askMode;
  const columns = Math.min(3, Math.max(1, Number(props.columns) || 1));

  const fields = useMemo(() => {
    const list = [];
    const push = (raw) => {
      if (!raw?.id) return;
      list.push(normalizeField(raw));
    };
    (props.fields || []).forEach(push);
    (props.sections || []).forEach((s) =>
      push({
        id: s.id,
        label: s.title || s.label,
        placeholder: s.placeholder,
        type: s.type || "textarea",
        required: s.required,
        value: s.value,
        max_chars: s.max_chars,
        options: s.options,
        rows: s.rows,
      })
    );
    if (props.rows?.length) {
      props.rows.forEach((row) => {
        (row.fields || row.columns || []).forEach((ref) => {
          if (typeof ref === "string") return;
          push(ref);
        });
      });
    }
    return list;
  }, [props.fields, props.sections, props.rows]);

  const layoutRows = useMemo(() => {
    const map = fieldById(fields);
    if (props.rows?.length) {
      return props.rows.map((row, i) => ({
        key: `row-${i}`,
        cols: Math.min(3, Math.max(1, row.columns ?? row.cols ?? ((row.fields || row.columns || []).length || 2))),
        fields: (row.fields || row.columns || [])
          .map((ref) => (typeof ref === "string" ? map[ref] : normalizeField(ref)))
          .filter(Boolean),
      }));
    }
    return null;
  }, [props.rows, fields]);

  const [values, setValues] = useState(() => {
    const init = {};
    fields.forEach((f) => {
      init[f.id] = f.value;
    });
    return init;
  });
  const [submitted, setSubmitted] = useState(false);
  const [savedDraft, setSavedDraft] = useState(false);
  const [timeLeft, setTimeLeft] = useState(timeout || null);

  useEffect(() => {
    if (!timeout) return;
    const interval = setInterval(() => setTimeLeft((t) => (t > 0 ? t - 1 : 0)), 1000);
    return () => clearInterval(interval);
  }, [timeout]);

  const allRequiredFilled = fields
    .filter((f) => f.required)
    .every((f) => isFieldFilled(f, values[f.id]));

  const setValue = (id, val) => setValues((v) => ({ ...v, [id]: val }));

  const handleSubmit = () => {
    if (!allRequiredFilled) return;
    setSubmitted(true);
    const payload = { ...values, submitted: true };
    if (askMode && typeof submitElement === "function") {
      submitElement(payload);
      return;
    }
    callAction({
      name: "form_submit",
      payload: {
        title,
        fields: fields
          .filter((f) => f.type !== "heading" && f.type !== "divider")
          .map((f) => ({ id: f.id, label: f.label, type: f.type, value: values[f.id] })),
      },
    });
  };

  const handleCancel = () => {
    if (askMode && typeof cancelElement === "function") cancelElement();
    else if (typeof deleteElement === "function") deleteElement();
  };

  const handleSaveDraft = () => {
    setSavedDraft(true);
    setTimeout(() => setSavedDraft(false), 2000);
    updateElement({
      ...props,
      fields: fields.map((f) => ({ ...f, value: values[f.id] })),
    });
  };

  const renderFieldControl = (field) => {
    const max = field.max_chars ?? defaultMax;
    const val = values[field.id];
    const type = field.type;

    if (type === "heading") {
      return <div className="text-sm font-semibold pt-1">{field.label}</div>;
    }
    if (type === "divider") {
      return <Separator className="my-1" />;
    }
    if (type === "textarea") {
      return (
        <Textarea
          value={val || ""}
          onChange={(e) => setValue(field.id, e.target.value.slice(0, max))}
          placeholder={field.placeholder || field.label}
          rows={field.rows ?? (compact ? 3 : 5)}
          className="text-sm resize-y"
        />
      );
    }
    if (type === "select") {
      return (
        <Select value={val || ""} onValueChange={(x) => setValue(field.id, x)}>
          <SelectTrigger>
            <SelectValue placeholder={field.placeholder || `Select ${field.label}`} />
          </SelectTrigger>
          <SelectContent>
            {field.options.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    }
    if (type === "radio") {
      return (
        <div className="flex flex-wrap gap-2">
          {field.options.map((opt) => {
            const on = val === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => setValue(field.id, opt.value)}
                className={`rounded-md border px-3 py-1.5 text-sm transition-colors ${
                  on ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:bg-muted/50"
                }`}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      );
    }
    if (type === "multiselect") {
      const selected = Array.isArray(val) ? val : [];
      return (
        <div className="flex flex-col gap-2">
          {field.options.map((opt) => (
            <div key={opt.value} className="flex items-center gap-2">
              <Checkbox
                id={`${field.id}-${opt.value}`}
                checked={selected.includes(opt.value)}
                onCheckedChange={(checked) => {
                  setValue(
                    field.id,
                    checked ? [...selected, opt.value] : selected.filter((x) => x !== opt.value)
                  );
                }}
              />
              <Label htmlFor={`${field.id}-${opt.value}`} className="text-sm font-normal cursor-pointer">
                {opt.label}
              </Label>
            </div>
          ))}
        </div>
      );
    }
    if (type === "checkbox") {
      return (
        <div className="flex items-center gap-2">
          <Checkbox
            id={field.id}
            checked={!!val}
            onCheckedChange={(c) => setValue(field.id, !!c)}
          />
          <Label htmlFor={field.id} className="text-sm font-normal cursor-pointer">
            {field.placeholder || field.label}
          </Label>
        </div>
      );
    }
    if (type === "switch") {
      return (
        <div className="flex items-center justify-between gap-3 rounded-lg border px-3 py-2">
          <Label htmlFor={field.id} className="text-sm font-normal">{field.label}</Label>
          <Switch id={field.id} checked={!!val} onCheckedChange={(c) => setValue(field.id, !!c)} />
        </div>
      );
    }
    const inputType = type === "email" ? "email" : type === "number" ? "number" : type === "date" ? "date" : "text";
    return (
      <Input
        type={inputType}
        value={val ?? ""}
        min={field.min}
        max={field.max}
        onChange={(e) => {
          const next = type === "number" ? e.target.value : e.target.value.slice(0, max);
          setValue(field.id, next);
        }}
        placeholder={field.placeholder || field.label}
        className="text-sm"
      />
    );
  };

  const renderFieldBlock = (field) => {
    if (field.type === "divider") {
      return <div key={field.id}>{renderFieldControl(field)}</div>;
    }
    if (field.type === "heading") {
      return <div key={field.id} className="col-span-full">{renderFieldControl(field)}</div>;
    }
    const max = field.max_chars ?? defaultMax;
    const charCount = String(values[field.id] || "").length;
    const showCount = !askMode && field.type === "textarea";
    const hideLabel = field.type === "checkbox" && field.placeholder;

    return (
      <div key={field.id} className="space-y-1.5 min-w-0">
        {!hideLabel && field.type !== "switch" && (
          <div className="flex items-baseline justify-between gap-2">
            <Label className="text-sm font-medium">
              {field.label}
              {field.required && <span className="text-destructive ml-1">*</span>}
            </Label>
            {showCount && (
              <span className={`text-xs ${charCount > max * 0.9 ? "text-destructive" : "text-muted-foreground"}`}>
                {charCount}/{max}
              </span>
            )}
          </div>
        )}
        {field.help && field.type !== "switch" && (
          <p className="text-xs text-muted-foreground -mt-0.5">{field.help}</p>
        )}
        {renderFieldControl(field)}
      </div>
    );
  };

  const spanStyle = (field, colCount) => {
    const span = Math.min(field.col_span || 1, colCount);
    if (span >= colCount) return { gridColumn: "1 / -1" };
    return { gridColumn: `span ${span}` };
  };

  const renderBody = () => {
    if (layoutRows) {
      return (
        <div className="space-y-4">
          {layoutRows.map((row) => (
            <div
              key={row.key}
              className="grid gap-3"
              style={{ gridTemplateColumns: `repeat(${row.cols}, minmax(0, 1fr))` }}
            >
              {row.fields.map((field) => (
                <div key={field.id} style={spanStyle(field, row.cols)}>
                  {renderFieldBlock(field)}
                </div>
              ))}
            </div>
          ))}
        </div>
      );
    }
    return (
      <div
        className="grid gap-3"
        style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
      >
        {fields.map((field) => (
          <div key={field.id} style={spanStyle(field, columns)}>
            {renderFieldBlock(field)}
          </div>
        ))}
      </div>
    );
  };

  if (submitted && !askMode) {
    return (
      <Card className={`mt-3 w-full ${compact ? "max-w-lg" : "max-w-2xl"}`}>
        <CardContent className="pt-4 flex items-center gap-2 text-sm">
          <Check className="h-4 w-4 text-green-500" />
          {props.success_message || "Submitted successfully."}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`mt-3 w-full ${compact ? "max-w-lg" : "max-w-2xl"}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            {subtitle && <CardDescription>{subtitle}</CardDescription>}
            {description && <p className="text-xs text-muted-foreground mt-1.5">{description}</p>}
            {timeLeft !== null && <CardDescription className="mt-1">{timeLeft}s remaining</CardDescription>}
          </div>
          {dueDate && (
            <Badge variant="outline" className="text-xs flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {dueDate.startsWith("Due") ? dueDate : `Due ${dueDate}`}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="pb-2">{renderBody()}</CardContent>
      <CardFooter className={`gap-2 flex-wrap ${showCancel || showDraft ? "justify-between" : "justify-center"}`}>
        <div className="flex gap-2">
          {showDraft && (
            <Button variant="outline" size="sm" onClick={handleSaveDraft}>
              <Save className="h-3.5 w-3.5 mr-1" />
              {savedDraft ? "Saved" : "Save draft"}
            </Button>
          )}
          {showCancel && <Button variant="outline" size="sm" onClick={handleCancel}>Cancel</Button>}
        </div>
        <Button size="sm" className="min-w-[8rem]" disabled={!allRequiredFilled} onClick={handleSubmit}>
          {submitLabel}
        </Button>
      </CardFooter>
    </Card>
  );
}
