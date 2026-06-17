import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";

export default function DropdownSelect() {
  const title = props.title || "Select an option";
  const placeholder = props.placeholder || "Choose...";
  const rawOptions = props.options || [];
  const options = rawOptions.map((o) =>
    typeof o === "string" ? { value: o, label: o } : o
  );

  const [value, setValue] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const selectedLabel = options.find((o) => o.value === value)?.label || value;

  const handleSubmit = () => {
    if (!value) return;
    setSubmitted(true);
    callAction({ name: "dropdown_select", payload: { selected: value, label: selectedLabel } });
  };

  if (submitted) {
    return (
      <Card className="mt-3 w-full max-w-sm">
        <CardContent className="pt-4 flex items-center gap-2 text-sm">
          <Check className="h-4 w-4 text-green-500" />
          Selected: <Badge variant="secondary">{selectedLabel}</Badge>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-3 w-full max-w-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="pb-2">
        <Select value={value} onValueChange={setValue}>
          <SelectTrigger>
            <SelectValue placeholder={placeholder} />
          </SelectTrigger>
          <SelectContent>
            {options.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardContent>
      <CardFooter>
        <Button className="w-full" disabled={!value} onClick={handleSubmit}>
          Confirm
        </Button>
      </CardFooter>
    </Card>
  );
}
