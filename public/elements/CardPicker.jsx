import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Check } from "lucide-react";

const AVATAR_COLORS = [
  "#3b82f6", "#a855f7", "#22c55e",
  "#f59e0b", "#ef4444", "#14b8a6",
  "#ec4899", "#6366f1",
];

function initials(name) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
}

export default function CardPicker() {
  const title = props.title || "Select items";
  const items = props.items || [];
  const maxSelections = props.max_selections || Infinity;
  const submitLabel = props.submit_label || "Confirm";
  const [selected, setSelected] = useState([]);

  const toggle = (id) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= maxSelections) return [...prev.slice(1), id];
      return [...prev, id];
    });
  };

  const handleSubmit = () => {
    const chosen = items.filter((item) => selected.includes(item.id));
    callAction({
      name: "card_picker_submit",
      payload: { selected_ids: selected, selected_items: chosen },
    });
  };

  return (
    <Card className="mt-3 w-full max-w-xl">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-base">{title}</CardTitle>
          {maxSelections !== Infinity && (
            <span style={{ fontSize: 12, color: "#94a3b8", whiteSpace: "nowrap" }}>
              {selected.length}/{maxSelections} selected
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            gap: 10,
          }}
        >
          {items.map((item, idx) => {
            const isSelected = selected.includes(item.id);
            const avatarColor = AVATAR_COLORS[idx % AVATAR_COLORS.length];
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => toggle(item.id)}
                style={{
                  position: "relative",
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  width: "100%",
                  minHeight: 76,
                  padding: "12px 14px",
                  paddingRight: isSelected ? 32 : 14,
                  textAlign: "left",
                  borderRadius: 10,
                  border: isSelected ? "2px solid #6366f1" : "1px solid #334155",
                  background: isSelected ? "rgba(99, 102, 241, 0.1)" : "transparent",
                  cursor: "pointer",
                  transition: "border-color 0.15s, background 0.15s",
                }}
              >
                {isSelected && (
                  <span
                    style={{
                      position: "absolute",
                      top: 8,
                      right: 8,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: 18,
                      height: 18,
                      borderRadius: "50%",
                      backgroundColor: "#6366f1",
                      color: "#fff",
                    }}
                  >
                    <Check style={{ width: 11, height: 11 }} strokeWidth={3} />
                  </span>
                )}
                <Avatar className="h-10 w-10 flex-shrink-0">
                  {(item.avatar_url || item.image_url) && (
                    <AvatarImage src={item.avatar_url || item.image_url} alt={item.name || ""} />
                  )}
                  <AvatarFallback
                    className="text-xs font-semibold text-white"
                    style={{ backgroundColor: avatarColor }}
                  >
                    {item.initials || initials(item.name)}
                  </AvatarFallback>
                </Avatar>
                <div style={{ minWidth: 0, flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
                  <div
                    style={{
                      fontSize: 14,
                      fontWeight: 600,
                      lineHeight: 1.25,
                      color: "var(--foreground, #f1f5f9)",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {item.name}
                  </div>
                  {item.subtitle && (
                    <div
                      style={{
                        fontSize: 12,
                        lineHeight: 1.3,
                        color: "#94a3b8",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {item.subtitle}
                    </div>
                  )}
                  {item.detail && (
                    <div
                      style={{
                        fontSize: 11,
                        lineHeight: 1.3,
                        color: "#64748b",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {item.detail}
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </CardContent>

      {items.length > 0 && (
        <CardFooter className="flex items-center justify-between gap-3 pt-0">
          {selected.length > 0 ? (
            <div className="flex flex-wrap gap-1 min-w-0 flex-1">
              {selected.map((id) => {
                const item = items.find((x) => x.id === id);
                return item ? (
                  <Badge key={id} variant="secondary" className="text-xs">
                    {item.name}
                  </Badge>
                ) : null;
              })}
            </div>
          ) : (
            <span style={{ fontSize: 12, color: "#94a3b8" }}>None selected</span>
          )}
          <Button size="sm" disabled={selected.length === 0} onClick={handleSubmit} className="flex-shrink-0">
            {submitLabel}
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}
