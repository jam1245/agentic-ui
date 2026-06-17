import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Star } from "lucide-react";

export default function RatingWidget() {
  const title = props.title || "Rate your experience";
  const [hovered, setHovered] = useState(0);
  const [selected, setSelected] = useState(props.rating || 0);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    if (selected === 0) return;
    setSubmitted(true);
    callAction({ name: "rating_submit", payload: { rating: selected, title } });
  };

  if (submitted) {
    return (
      <Card className="mt-3 w-full max-w-sm">
        <CardContent className="pt-4 text-center text-sm text-muted-foreground">
          Thanks for your rating: {selected} / 5
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-3 w-full max-w-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex gap-1 justify-center pb-2">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            className="focus:outline-none"
            onMouseEnter={() => setHovered(n)}
            onMouseLeave={() => setHovered(0)}
            onClick={() => setSelected(n)}
          >
            <Star
              className={`h-8 w-8 transition-colors ${
                n <= (hovered || selected)
                  ? "fill-yellow-400 text-yellow-400"
                  : "text-muted-foreground"
              }`}
            />
          </button>
        ))}
      </CardContent>
      <CardFooter className="flex justify-between items-center pt-0">
        <span className="text-xs text-muted-foreground">
          {selected > 0 ? `${selected} star${selected > 1 ? "s" : ""} selected` : "Select a rating"}
        </span>
        <Button size="sm" disabled={selected === 0} onClick={handleSubmit}>
          Submit
        </Button>
      </CardFooter>
    </Card>
  );
}
