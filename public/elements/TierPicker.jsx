import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";

const STYLE = {
  emerald: { border: "2px solid #34d399", background: "rgba(16,185,129,0.12)", color: "#6ee7b7" },
  blue: { border: "2px solid #60a5fa", background: "rgba(59,130,246,0.12)", color: "#93c5fd" },
  neutral: { border: "2px solid #64748b", background: "rgba(100,116,139,0.12)", color: "#cbd5e1" },
  amber: { border: "2px solid #fbbf24", background: "rgba(245,158,11,0.12)", color: "#fcd34d" },
  red: { border: "2px solid #f87171", background: "rgba(239,68,68,0.12)", color: "#fca5a5" },
};

export default function TierPicker() {
  const title = props.title || "Choose one option";
  const subtitle = props.subtitle || [props.employee, props.cycle].filter(Boolean).join(" - ");
  const requireComment = props.require_comment ?? props.require_justification !== false;
  const commentLabel = props.comment_label || "Comment";
  const commentPlaceholder = props.comment_placeholder || "Add supporting detail...";
  const submitLabel = props.submit_label || "Submit";
  const tiers = props.tiers || [];

  const [selected, setSelected] = useState(props.current_value || props.current_rating || null);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const tierStyle = (tier, on) => {
    if (!on) return { border: "1px solid #334155", background: "transparent", cursor: "pointer" };
    return STYLE[tier.style] || STYLE.blue;
  };

  const isValid = selected && (!requireComment || comment.trim().length > 0);

  const handleSubmit = () => {
    if (!isValid) return;
    setSubmitted(true);
    const tier = tiers.find((t) => t.value === selected);
    callAction({
      name: "tier_picker_submit",
      payload: {
        title,
        value: selected,
        tier_label: tier?.label,
        comment,
        subtitle,
      },
    });
  };

  if (submitted) {
    const tier = tiers.find((t) => t.value === selected);
    return (
      <Card className="mt-3 w-full max-w-lg">
        <CardContent className="pt-4 space-y-1">
          <div className="flex items-center gap-2 text-sm">
            <Check className="h-4 w-4 text-green-500" />
            <span>Selected:</span>
            <Badge variant="outline">{tier?.label}</Badge>
          </div>
          {comment && <p className="text-xs text-muted-foreground pl-6">{comment}</p>}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-3 w-full max-w-lg">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        {subtitle && <CardDescription>{subtitle}</CardDescription>}
      </CardHeader>
      <CardContent className="space-y-4 pb-2">
        <div className="grid grid-cols-1 gap-2">
          {tiers.map((tier) => {
            const on = selected === tier.value;
            return (
              <div
                key={tier.value}
                onClick={() => setSelected(tier.value)}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 12,
                  borderRadius: 8,
                  padding: 12,
                  ...tierStyle(tier, on),
                }}
              >
                <div
                  style={{
                    marginTop: 2,
                    width: 16,
                    height: 16,
                    borderRadius: "50%",
                    border: "2px solid currentColor",
                    flexShrink: 0,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  {on && <div style={{ width: 8, height: 8, borderRadius: "50%", background: "currentColor" }} />}
                </div>
                <div>
                  <div className="text-sm font-medium">{tier.label}</div>
                  {tier.description && <div className="text-xs opacity-80">{tier.description}</div>}
                </div>
              </div>
            );
          })}
        </div>
        {selected && (
          <div className="space-y-1.5">
            <Label className="text-sm">
              {commentLabel}
              {requireComment && <span className="text-destructive ml-1">*</span>}
            </Label>
            <Textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={commentPlaceholder}
              rows={3}
              className="text-sm"
            />
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button className="w-full" disabled={!isValid} onClick={handleSubmit}>
          {submitLabel}
        </Button>
      </CardFooter>
    </Card>
  );
}
