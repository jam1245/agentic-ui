import { Badge } from "@/components/ui/badge";
import { useState } from "react";

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr",
  "May", "Jun", "Jul", "Aug",
  "Sep", "Oct", "Nov", "Dec",
];

function isoLastDay(year, monthIndex) {
  const day = new Date(year, monthIndex + 1, 0).getDate();
  return `${year}-${String(monthIndex + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export default function YearCalendar() {
  const year = props.year || new Date().getFullYear();
  const title = props.title || `${year}`;
  const [selected, setSelected] = useState(null);

  const handleClick = (monthIndex) => {
    const date = isoLastDay(year, monthIndex);
    setSelected(monthIndex);
    callAction({
      name: "calendar_month_select",
      payload: {
        date,
        month: ["January","February","March","April","May","June","July","August","September","October","November","December"][monthIndex],
        month_number: monthIndex + 1,
        year,
        last_day: new Date(year, monthIndex + 1, 0).getDate(),
      },
    });
  };

  return (
    <div className="mt-2 w-full max-w-xs">
      <div className="mb-1.5 flex items-center gap-2">
        <span className="text-sm font-medium">{title}</span>
        {selected !== null && (
          <Badge variant="secondary" className="text-xs">{MONTHS[selected]}</Badge>
        )}
      </div>
      <div className="grid grid-cols-4 gap-1 pb-3">
        {MONTHS.map((name, i) => (
          <button
            key={i}
            onClick={() => handleClick(i)}
            className={`rounded border px-1 py-1.5 text-xs font-medium transition-all hover:border-primary hover:bg-primary/10 focus:outline-none ${
              selected === i
                ? "border-primary bg-primary/10 text-primary"
                : "border-border text-muted-foreground"
            }`}
          >
            {name}
          </button>
        ))}
      </div>
      <p className="mt-1 text-xs text-muted-foreground">Click a month to select it.</p>
    </div>
  );
}
