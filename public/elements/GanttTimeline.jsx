import { useMemo, useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Check, GripVertical } from "lucide-react";

const ROW_H   = 64;   // px per row
const BAR_T   = 14;   // bar top offset within row (px)
const BAR_H   = 28;   // bar height (px)

const STATUS_COLOR = {
  on_track: { bar: "#22c55e", badge: { bg: "rgba(34,197,94,0.15)",  color: "#16a34a" } },
  at_risk:  { bar: "#f59e0b", badge: { bg: "rgba(245,158,11,0.15)", color: "#d97706" } },
  behind:   { bar: "#ef4444", badge: { bg: "rgba(239,68,68,0.15)",  color: "#dc2626" } },
  complete: { bar: "#3b82f6", badge: { bg: "rgba(59,130,246,0.15)", color: "#2563eb" } },
  draft:    { bar: "#94a3b8", badge: { bg: "rgba(148,163,184,0.15)",color: "#64748b" } },
};
const FALLBACK_BARS = ["#8b5cf6","#0ea5e9","#14b8a6","#f97316","#ec4899","#6366f1","#10b981","#f43f5e"];

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function parseISO(str) {
  if (!str) return null;
  const d = new Date(str + "T00:00:00");
  return isNaN(d.getTime()) ? null : d;
}
function fmtShort(d) {
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
function toISO(d) {
  return d.toISOString().slice(0, 10);
}

export default function GanttTimeline() {
  const title    = props.title || "";
  const rawItems = props.items || [];
  const year     = props.year || new Date().getFullYear();

  const [overrides, setOverrides] = useState({});
  const [dragging,  setDragging]  = useState(null);
  const barAreaRef = useRef(null);

  // ── Derived range + markers ───────────────────────────────────────────
  const { rangeStart, totalMs, monthMarkers, todayPct } = useMemo(() => {
    const rangeStart = new Date(year, 0, 1);
    let maxEnd = new Date(year, 11, 31);
    rawItems.forEach(it => { const d = parseISO(it.end_date); if (d && d > maxEnd) maxEnd = d; });
    Object.values(overrides).forEach(iso => { const d = parseISO(iso); if (d && d > maxEnd) maxEnd = d; });

    const totalMs = maxEnd.getTime() - rangeStart.getTime();
    const toPct = d => Math.max(0, Math.min(100, (d - rangeStart) / totalMs * 100));

    const markers = [];
    const cur = new Date(year, 0, 1);
    const multi = maxEnd.getFullYear() > year;
    while (cur <= maxEnd) {
      markers.push({
        label: multi
          ? `${MONTHS[cur.getMonth()]} '${String(cur.getFullYear()).slice(2)}`
          : MONTHS[cur.getMonth()],
        pct: toPct(new Date(cur)),
        even: cur.getMonth() % 2 === 0,
      });
      cur.setMonth(cur.getMonth() + 1);
    }

    const today   = new Date();
    const todayPct = today >= rangeStart && today <= maxEnd ? toPct(today) : null;
    return { rangeStart, totalMs, monthMarkers: markers, todayPct };
  }, [rawItems, year, overrides]);

  // ── Resolved items ────────────────────────────────────────────────────
  const items = useMemo(() => {
    const toPct = d => Math.max(0, Math.min(100, (d - rangeStart) / totalMs * 100));
    return rawItems.map((item, idx) => {
      const start  = parseISO(item.start_date) || new Date(year, 0, 1);
      const endIso = overrides[idx] ?? item.end_date;
      const end    = parseISO(endIso) || new Date(year, 11, 31);
      const left   = toPct(start);
      const width  = Math.max(1, toPct(end) - left);
      const s      = STATUS_COLOR[item.status];
      return {
        ...item, start, end, endIso, left, width, idx,
        barColor:  s ? s.bar          : FALLBACK_BARS[idx % FALLBACK_BARS.length],
        badgeBg:   s ? s.badge.bg     : "rgba(148,163,184,0.15)",
        badgeText: s ? s.badge.color  : "#64748b",
      };
    });
  }, [rawItems, year, overrides, rangeStart, totalMs]);

  const hasChanges = Object.keys(overrides).length > 0;

  // ── Drag ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!dragging) return;
    const onMove = e => {
      const pct  = Math.max(0.01, Math.min(1, (e.clientX - dragging.rect.left) / dragging.rect.width));
      const newD = new Date(dragging.rangeStartMs + pct * dragging.totalMs);
      newD.setHours(0, 0, 0, 0);
      const start = parseISO(rawItems[dragging.idx]?.start_date) || new Date(year, 0, 1);
      if (newD <= start) return;
      setOverrides(p => ({ ...p, [dragging.idx]: toISO(newD) }));
    };
    const onUp = () => setDragging(null);
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => { window.removeEventListener("mousemove", onMove); window.removeEventListener("mouseup", onUp); };
  }, [dragging, rawItems, year]);

  const startDrag = (e, idx) => {
    e.preventDefault();
    if (!barAreaRef.current) return;
    setDragging({ idx, rect: barAreaRef.current.getBoundingClientRect(), rangeStartMs: rangeStart.getTime(), totalMs });
  };

  const handleConfirm = () => {
    const updated = items.map(({ title, endIso, start_date, status, owner }) => ({
      title, end_date: endIso,
      ...(start_date && { start_date }),
      ...(status     && { status }),
      ...(owner      && { owner }),
    }));
    const changes = Object.entries(overrides).map(([idx, d]) => ({
      title: rawItems[idx]?.title,
      original_end_date: rawItems[idx]?.end_date,
      new_end_date: d,
    }));
    callAction({ name: "gantt_update", payload: { items: updated, changes } });
    setOverrides({});
  };

  const LABEL_W = 176; // px, label column width

  return (
    <div style={{ marginTop: 12, width: "100%", maxWidth: 760, fontFamily: "inherit" }}>

      {/* Header row */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 10 }}>
        <div>
          {title && <div style={{ fontSize: 14, fontWeight: 600 }}>{title}</div>}
          <div style={{ fontSize: 11, color: "var(--muted-foreground, #94a3b8)", marginTop: 2 }}>
            Drag the right edge of any bar to adjust its end date
          </div>
        </div>
        {hasChanges && (
          <Button size="sm" style={{ height: 28, fontSize: 12, gap: 4 }} onClick={handleConfirm}>
            <Check style={{ width: 12, height: 12 }} />
            Confirm changes
          </Button>
        )}
      </div>

      {/* Chart */}
      <div style={{ border: "1px solid var(--border, #334155)", borderRadius: 12, overflow: "hidden" }}>

        {/* Month header */}
        <div style={{ display: "flex", borderBottom: "1px solid var(--border, #334155)", background: "var(--muted, rgba(255,255,255,0.04))" }}>
          {/* Corner */}
          <div style={{ width: LABEL_W, flexShrink: 0, borderRight: "1px solid var(--border, #334155)", padding: "8px 12px" }}>
            <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--muted-foreground, #94a3b8)" }}>
              Item
            </span>
          </div>
          {/* Month labels */}
          <div ref={barAreaRef} style={{ position: "relative", flex: 1, height: 36 }}>
            {/* Alternating stripe (header) */}
            {monthMarkers.map((m, i) => m.even && (
              <div key={i} style={{
                position: "absolute", top: 0, bottom: 0,
                left: `${m.pct}%`,
                width: i < monthMarkers.length - 1 ? `${monthMarkers[i+1].pct - m.pct}%` : `${100 - m.pct}%`,
                background: "rgba(255,255,255,0.03)",
              }} />
            ))}
            {monthMarkers.map((m, i) => (
              <div key={i} style={{ position: "absolute", top: 0, height: "100%", left: `${m.pct}%` }}>
                {i > 0 && <div style={{ position: "absolute", inset: "0 auto 0 0", width: 1, background: "var(--border, rgba(255,255,255,0.1))" }} />}
                <span style={{ position: "absolute", top: 10, left: 6, fontSize: 10, fontWeight: 500, whiteSpace: "nowrap", color: "var(--muted-foreground, #94a3b8)" }}>
                  {m.label}
                </span>
              </div>
            ))}
            {/* Today pin */}
            {todayPct !== null && <>
              <div style={{ position: "absolute", top: 0, bottom: 0, width: 1, background: "#f87171", zIndex: 10, left: `${todayPct}%` }} />
              <div style={{
                position: "absolute", top: 0, left: `${todayPct}%`,
                transform: "translateX(-50%)",
                background: "#f87171", color: "#fff",
                fontSize: 8, fontWeight: 700, padding: "1px 4px", borderRadius: "0 0 3px 3px",
                zIndex: 10, whiteSpace: "nowrap",
              }}>
                today
              </div>
            </>}
          </div>
        </div>

        {/* Item rows */}
        {items.map((item, i) => (
          <div key={i} style={{
            display: "flex",
            borderBottom: i < items.length - 1 ? "1px solid var(--border, rgba(255,255,255,0.08))" : "none",
            height: ROW_H,
          }}>
            {/* Label */}
            <div style={{ width: LABEL_W, flexShrink: 0, borderRight: "1px solid var(--border, rgba(255,255,255,0.08))", padding: "10px 12px", display: "flex", flexDirection: "column", justifyContent: "center", gap: 3, minWidth: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", flexShrink: 0, backgroundColor: item.barColor }} />
                <span style={{ fontSize: 11, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={item.title}>
                  {item.title}
                </span>
              </div>
              {item.owner && (
                <div style={{ fontSize: 10, color: "var(--muted-foreground, #94a3b8)", paddingLeft: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {item.owner}
                </div>
              )}
              {item.status && (
                <div style={{
                  display: "inline-block", marginLeft: 14, padding: "1px 6px", borderRadius: 4,
                  fontSize: 9, fontWeight: 600, textTransform: "capitalize",
                  backgroundColor: item.badgeBg, color: item.badgeText,
                  alignSelf: "flex-start",
                }}>
                  {item.status.replace(/_/g, " ")}
                </div>
              )}
            </div>

            {/* Bar area */}
            <div style={{ position: "relative", flex: 1, height: ROW_H, overflow: "hidden" }}>
              {/* Column stripes */}
              {monthMarkers.map((m, mi) => m.even && (
                <div key={mi} style={{
                  position: "absolute", top: 0, bottom: 0,
                  left: `${m.pct}%`,
                  width: mi < monthMarkers.length - 1 ? `${monthMarkers[mi+1].pct - m.pct}%` : `${100 - m.pct}%`,
                  background: "rgba(255,255,255,0.025)",
                }} />
              ))}
              {/* Month grid lines */}
              {monthMarkers.map((m, mi) => (
                <div key={mi} style={{ position: "absolute", top: 0, bottom: 0, width: 1, left: `${m.pct}%`, background: "rgba(255,255,255,0.07)" }} />
              ))}
              {/* Today line */}
              {todayPct !== null && (
                <div style={{ position: "absolute", top: 0, bottom: 0, width: 1, left: `${todayPct}%`, background: "rgba(248,113,113,0.5)", zIndex: 5 }} />
              )}

              {/* Bar */}
              <div
                title={`${item.title}: ${fmtShort(item.start)} → ${fmtShort(item.end)}`}
                style={{
                  position: "absolute",
                  top: BAR_T,
                  height: BAR_H,
                  left: `${item.left}%`,
                  width: `${item.width}%`,
                  backgroundColor: item.barColor,
                  borderRadius: 999,
                  opacity: overrides[item.idx] ? 1 : 0.82,
                  boxShadow: overrides[item.idx] ? `0 0 0 2px rgba(255,255,255,0.25)` : "0 1px 3px rgba(0,0,0,0.3)",
                  transition: "opacity 0.15s, box-shadow 0.15s",
                  zIndex: 2,
                  cursor: "default",
                  display: "flex",
                  alignItems: "center",
                  overflow: "hidden",
                }}
              >
                {/* Label inside bar */}
                {item.width > 10 && (
                  <span style={{ paddingLeft: 10, paddingRight: 28, fontSize: 10, fontWeight: 500, color: "rgba(255,255,255,0.9)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {item.title}
                  </span>
                )}
                {/* Drag handle */}
                <div
                  onMouseDown={e => startDrag(e, item.idx)}
                  style={{
                    position: "absolute", right: 0, top: 0, bottom: 0, width: 20,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    cursor: "ew-resize",
                    background: "rgba(0,0,0,0.15)",
                    borderRadius: "0 999px 999px 0",
                  }}
                >
                  <GripVertical style={{ width: 11, height: 11, color: "rgba(255,255,255,0.7)" }} />
                </div>
              </div>

              {/* End-date label */}
              <div style={{
                position: "absolute",
                top: "50%",
                transform: "translateY(-50%)",
                left: `calc(${item.left + item.width}% + 5px)`,
                fontSize: 9,
                whiteSpace: "nowrap",
                color: overrides[item.idx] ? "var(--foreground, #f1f5f9)" : "var(--muted-foreground, #94a3b8)",
                fontWeight: overrides[item.idx] ? 600 : 400,
                zIndex: 3,
              }}>
                {fmtShort(item.end)}
              </div>
            </div>
          </div>
        ))}

        {/* Footer legend */}
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 8, borderTop: "1px solid var(--border, rgba(255,255,255,0.08))", background: "var(--muted, rgba(255,255,255,0.03))", padding: "8px 12px" }}>
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12 }}>
            {todayPct !== null && (
              <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10, color: "var(--muted-foreground, #94a3b8)" }}>
                <div style={{ width: 2, height: 12, borderRadius: 1, backgroundColor: "#f87171" }} />
                Today
              </div>
            )}
            {Object.entries(STATUS_COLOR).map(([key, val]) => (
              <div key={key} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10, color: "var(--muted-foreground, #94a3b8)" }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: val.bar }} />
                <span style={{ textTransform: "capitalize" }}>{key.replace(/_/g, " ")}</span>
              </div>
            ))}
          </div>
          {hasChanges && (
            <Button size="sm" style={{ height: 28, fontSize: 12, gap: 4 }} onClick={handleConfirm}>
              <Check style={{ width: 12, height: 12 }} />
              Confirm changes
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
