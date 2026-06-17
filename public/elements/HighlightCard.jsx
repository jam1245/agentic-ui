import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Trophy, Star, Award, Zap, Heart, Medal, Check, Sparkles } from "lucide-react";

const ICONS = { trophy: Trophy, star: Star, award: Award, zap: Zap, heart: Heart, medal: Medal, sparkles: Sparkles };

export default function HighlightCard() {
  const headline = props.headline || props.award_name || "Highlight";
  const subtitle = props.subtitle || (props.recipient ? `Awarded to ${props.recipient}` : "");
  const body = props.body || props.citation || "";
  const Icon = ICONS[props.icon || props.badge_icon] || Trophy;
  const accent = props.accent_color || "#f59e0b";
  const cta = props.cta;
  const showCta = props.show_cta ?? props.show_nominate ?? !!cta;

  const [open, setOpen] = useState(false);
  const [values, setValues] = useState({});
  const [submitted, setSubmitted] = useState(false);

  const meta = props.meta || [];
  if (props.giver) meta.push({ label: "From", value: props.giver });
  if (props.date) meta.push({ label: "Date", value: props.date });

  const fields = cta?.fields || [
    { id: "name", label: "Name", type: "text" },
    { id: "reason", label: "Reason", type: "textarea" },
  ];

  const handleSubmit = () => {
    const name = values.name || values.nominee || "";
    if (cta?.require_name !== false && !name.trim()) return;
    setSubmitted(true);
    setOpen(false);
    callAction({
      name: "highlight_card_submit",
      payload: {
        headline,
        cta_label: cta?.label,
        ...values,
        nominee_name: name,
        award_name: headline,
        reason: values.reason || "",
      },
    });
  };

  return (
    <Card className="mt-3 w-full max-w-sm">
      <CardHeader className="pb-0 pt-5">
        <div className="flex flex-col items-center text-center gap-3">
          <div
            className="h-16 w-16 rounded-full flex items-center justify-center border-2"
            style={{ backgroundColor: `${accent}22`, borderColor: accent }}
          >
            <Icon className="h-8 w-8" style={{ color: accent }} />
          </div>
          <div>
            <div className="text-lg font-bold">{headline}</div>
            {subtitle && <div className="text-sm text-muted-foreground">{subtitle}</div>}
          </div>
        </div>
      </CardHeader>
      <CardContent className="text-center space-y-3 pt-3 pb-2">
        {body && (
          <blockquote
            className="text-sm text-muted-foreground italic border-l-2 text-left mx-1"
            style={{ borderColor: accent, paddingLeft: 16, marginLeft: 4 }}
          >
            {body}
          </blockquote>
        )}
        {meta.length > 0 && (
          <div className="flex items-center justify-center gap-3 text-xs text-muted-foreground flex-wrap">
            {meta.map((m, i) => (
              <span key={i}>
                {m.label ? `${m.label}: ${m.value}` : m.value}
              </span>
            ))}
          </div>
        )}
        {submitted && (
          <div className="flex items-center justify-center gap-2 text-sm text-green-600">
            <Check className="h-4 w-4" />
            {props.success_message || "Submitted."}
          </div>
        )}
        {open && !submitted && (
          <>
            <Separator />
            <div className="space-y-2 text-left">
              <div className="text-sm font-medium">{cta?.label || "Submit"}</div>
              {fields.map((f) => (
                <div key={f.id} className="space-y-1">
                  <Label className="text-xs">{f.label}</Label>
                  {f.type === "textarea" ? (
                    <Textarea
                      value={values[f.id] || ""}
                      onChange={(e) => setValues((v) => ({ ...v, [f.id]: e.target.value }))}
                      rows={2}
                      className="text-sm"
                    />
                  ) : (
                    <Input
                      value={values[f.id] || ""}
                      onChange={(e) => setValues((v) => ({ ...v, [f.id]: e.target.value }))}
                      className="h-8 text-sm"
                    />
                  )}
                </div>
              ))}
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setOpen(false)}>Cancel</Button>
                <Button size="sm" onClick={handleSubmit}>{cta?.submit_label || "Submit"}</Button>
              </div>
            </div>
          </>
        )}
      </CardContent>
      {showCta && !submitted && !open && (
        <CardFooter>
          <Button variant="outline" size="sm" className="w-full" onClick={() => setOpen(true)}>
            {cta?.label || "Nominate someone"}
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}
