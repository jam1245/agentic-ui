import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";

export default function CheckboxGroup() {
  const title = props.title || "Select options";
  const multiple = props.multiple !== false;
  const minSelected = props.min_selected || (multiple ? 0 : 1);
  const maxSelected = props.max_selected || (multiple ? Infinity : 1);
  const options = (props.options || []).map((o) =>
    typeof o === "string" ? { value: o, label: o } : o
  );

  const [selected, setSelected] = useState([]);
  const [submitted, setSubmitted] = useState(false);

  const toggle = (value) => {
    setSelected((prev) => {
      if (!multiple) return prev.includes(value) ? [] : [value];
      if (prev.includes(value)) return prev.filter((v) => v !== value);
      if (prev.length >= maxSelected) return prev;
      return [...prev, value];
    });
  };

  const isValid = selected.length >= minSelected && selected.length <= maxSelected;

  const handleSubmit = () => {
    if (!isValid) return;
    setSubmitted(true);
    callAction({ name: "checkbox_submit", payload: { selected } });
  };

  if (submitted) {
    return (
      <Card className="mt-3 w-full max-w-sm">
        <CardContent className="pt-4 flex flex-wrap items-center gap-2 text-sm">
          <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
          <span>Selected:</span>
          {selected.map((v) => <Badge key={v} variant="secondary">{v}</Badge>)}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-3 w-full max-w-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        {multiple && maxSelected < Infinity && (
          <CardDescription>Select up to {maxSelected}</CardDescription>
        )}
        {!multiple && (
          <CardDescription>Select one</CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-2 pb-2">
        {options.map((o) => (
          <div key={o.value} className="flex items-center gap-3">
            <Checkbox
              id={`cb-${o.value}`}
              checked={selected.includes(o.value)}
              onCheckedChange={() => toggle(o.value)}
            />
            <Label htmlFor={`cb-${o.value}`} className="cursor-pointer text-sm font-normal">
              {o.label}
            </Label>
          </div>
        ))}
      </CardContent>
      <CardFooter className="justify-end">
        <Button size="sm" className="w-auto min-w-[8rem]" disabled={!isValid} onClick={handleSubmit}>
          {multiple ? `Confirm (${selected.length} selected)` : "Confirm"}
        </Button>
      </CardFooter>
    </Card>
  );
}
