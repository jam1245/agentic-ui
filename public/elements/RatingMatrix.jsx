import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Star, Check } from "lucide-react";

const SCROLL_THRESHOLD = 5;

export default function RatingMatrix() {
  const title = props.title || "Rate items";
  const description = props.description || props.rating_hint || "Rate each row 1 (low) to 5 (high)";
  const includeComments = props.include_comments !== false;
  const maxRating = props.max_rating ?? 5;
  const submitLabel = props.submit_label || "Submit ratings";

  const items = useMemo(() => {
    if (props.items?.length) return props.items;
    return (props.competencies || []).map((c) => ({
      id: c.id,
      label: c.name || c.label,
      description: c.description,
    }));
  }, [props.items, props.competencies]);

  const [ratings, setRatings] = useState({});
  const [hovered, setHovered] = useState({});
  const [comments, setComments] = useState({});
  const [submitted, setSubmitted] = useState(false);

  const stars = Array.from({ length: maxRating }, (_, i) => i + 1);
  const allRated = items.length > 0 && items.every((c) => ratings[c.id]);

  const handleSubmit = () => {
    setSubmitted(true);
    callAction({
      name: "rating_matrix_submit",
      payload: {
        title,
        ratings: items.map((c) => ({
          id: c.id,
          label: c.label,
          rating: ratings[c.id] || 0,
          comment: comments[c.id] || "",
        })),
      },
    });
  };

  if (submitted) {
    return (
      <Card className="mt-3 w-full max-w-lg">
        <CardContent className="pt-4">
          <div className="flex items-center gap-2 text-sm mb-3">
            <Check className="h-4 w-4 text-green-500" />
            <span>Ratings submitted</span>
          </div>
          <div className="space-y-1">
            {items.map((c) => (
              <div key={c.id} className="flex items-center justify-between text-sm">
                <span>{c.label}</span>
                <div className="flex gap-0.5">
                  {stars.map((n) => (
                    <Star
                      key={n}
                      className={`h-3.5 w-3.5 ${n <= (ratings[c.id] || 0) ? "fill-yellow-400 text-yellow-400" : "text-muted-foreground"}`}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-3 w-full max-w-lg">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="pb-2">
        {(() => {
          const rows = items.map((item, i) => (
            <div key={item.id}>
              {i > 0 && <Separator className="mb-4" />}
              <div className="space-y-2">
                <div>
                  <div className="text-sm font-medium">{item.label}</div>
                  {item.description && <div className="text-xs text-muted-foreground">{item.description}</div>}
                </div>
                <div className="flex gap-1.5 flex-wrap items-center">
                  {stars.map((n) => {
                    const active = n <= ((hovered[item.id] ?? ratings[item.id]) || 0);
                    return (
                      <button
                        key={n}
                        type="button"
                        className="focus:outline-none"
                        onMouseEnter={() => setHovered((h) => ({ ...h, [item.id]: n }))}
                        onMouseLeave={() => setHovered((h) => ({ ...h, [item.id]: 0 }))}
                        onClick={() => setRatings((r) => ({ ...r, [item.id]: n }))}
                      >
                        <Star className={`h-6 w-6 transition-colors ${active ? "fill-yellow-400 text-yellow-400" : "text-muted-foreground"}`} />
                      </button>
                    );
                  })}
                </div>
                {includeComments && ratings[item.id] && (
                  <Textarea
                    value={comments[item.id] || ""}
                    onChange={(e) => setComments((c) => ({ ...c, [item.id]: e.target.value }))}
                    placeholder="Optional comment..."
                    rows={2}
                    className="text-sm"
                  />
                )}
              </div>
            </div>
          ));
          return items.length > SCROLL_THRESHOLD ? (
            <ScrollArea className="max-h-[400px] w-full pr-3">
              <div className="space-y-4">{rows}</div>
            </ScrollArea>
          ) : (
            <div className="space-y-4">{rows}</div>
          );
        })()}
      </CardContent>
      <CardFooter className="justify-center">
        <Button size="sm" className="w-auto min-w-[9rem]" disabled={!allRated} onClick={handleSubmit}>
          {submitLabel}
        </Button>
      </CardFooter>
    </Card>
  );
}
