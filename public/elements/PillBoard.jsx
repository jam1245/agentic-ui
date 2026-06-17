import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const COL_THEME = {
  green: { header: "#22c55e", bg: "rgba(34,197,94,0.12)", border: "rgba(34,197,94,0.35)", text: "#4ade80" },
  amber: { header: "#f59e0b", bg: "rgba(245,158,11,0.12)", border: "rgba(245,158,11,0.35)", text: "#fbbf24" },
  blue: { header: "#3b82f6", bg: "rgba(59,130,246,0.12)", border: "rgba(59,130,246,0.35)", text: "#93c5fd" },
  purple: { header: "#a855f7", bg: "rgba(168,85,247,0.12)", border: "rgba(168,85,247,0.35)", text: "#c4b5fd" },
  red: { header: "#ef4444", bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.35)", text: "#fca5a5" },
  default: { header: "#94a3b8", bg: "rgba(148,163,184,0.1)", border: "rgba(148,163,184,0.3)", text: "#cbd5e1" },
};

function theme(color) {
  return COL_THEME[color] || COL_THEME.default;
}

export default function PillBoard() {
  const title = props.title || "";
  const subtitle = props.subtitle || "";
  const columns = props.columns || [];
  const quotes = props.quotes || [];
  const stats = props.stats || [];
  const colCount = Math.min(Math.max(columns.length, 1), 4);

  return (
    <Card className="mt-3 w-full max-w-xl">
      <CardHeader style={{ paddingBottom: 12 }}>
        {title && (
          <CardTitle style={{ fontSize: 16, fontWeight: 600, lineHeight: 1.3 }}>
            {title}
          </CardTitle>
        )}
        {subtitle && (
          <p style={{ marginTop: 4, fontSize: 12, color: "#94a3b8", lineHeight: 1.4 }}>
            {subtitle}
          </p>
        )}
        {stats.length > 0 && (
          <div style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 8 }}>
            {stats.map((s, i) => (
              <div
                key={i}
                style={{
                  display: "inline-flex",
                  alignItems: "baseline",
                  gap: 6,
                  padding: "6px 12px",
                  borderRadius: 8,
                  border: "1px solid #334155",
                  background: "rgba(255,255,255,0.04)",
                }}
              >
                <span style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground, #f1f5f9)" }}>
                  {s.value}
                </span>
                <span style={{ fontSize: 11, color: "#94a3b8" }}>{s.label}</span>
              </div>
            ))}
          </div>
        )}
      </CardHeader>

      <CardContent style={{ paddingTop: 0, paddingBottom: 16 }}>
        {columns.length > 0 && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: `repeat(${colCount}, minmax(0, 1fr))`,
              gap: 16,
              alignItems: "start",
            }}
          >
            {columns.map((col, ci) => {
              const t = theme(col.color);
              return (
                <div key={ci}>
                  <div
                    style={{
                      marginBottom: 10,
                      fontSize: 12,
                      fontWeight: 600,
                      letterSpacing: "0.02em",
                      textTransform: "uppercase",
                      color: t.header,
                    }}
                  >
                    {col.name}
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {(col.items || []).map((item, ii) => (
                      <span
                        key={ii}
                        style={{
                          display: "inline-block",
                          fontSize: 12,
                          lineHeight: 1.3,
                          padding: "5px 10px",
                          borderRadius: 999,
                          border: `1px solid ${t.border}`,
                          backgroundColor: t.bg,
                          color: t.text,
                        }}
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {quotes.length > 0 && (
          <div
            style={{
              marginTop: columns.length > 0 ? 20 : 0,
              paddingTop: 16,
              borderTop: "1px solid #334155",
            }}
          >
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {quotes.map((q, i) => (
                <blockquote
                  key={i}
                  style={{
                    margin: 0,
                    paddingLeft: 12,
                    borderLeft: "3px solid #475569",
                    fontSize: 13,
                    fontStyle: "italic",
                    lineHeight: 1.5,
                    color: "#94a3b8",
                  }}
                >
                  {q}
                </blockquote>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
