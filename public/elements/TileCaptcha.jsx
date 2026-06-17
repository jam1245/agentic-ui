import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Star, Flame, Ghost, Moon, Heart, Zap, Droplets, Leaf, Globe, Trophy,
} from "lucide-react";

const ICONS = {
  star: Star, flame: Flame, ghost: Ghost, moon: Moon, heart: Heart,
  zap: Zap, droplets: Droplets, leaf: Leaf, globe: Globe, trophy: Trophy,
};

function buildDefaultTiles(size, targetKey) {
  const n = size * size;
  const targetCount = Math.max(2, Math.min(n - 2, Math.round(n * 0.4)));
  const indices = Array.from({ length: n }, (_, i) => i);
  for (let i = indices.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [indices[i], indices[j]] = [indices[j], indices[i]];
  }
  const targets = new Set(indices.slice(0, targetCount));
  return Array.from({ length: n }, (_, id) => ({
    id,
    iconKey: targets.has(id) ? targetKey : null,
  }));
}

export default function TileCaptcha() {
  const title = props.title || "Verify you're human";
  const instruction = props.instruction || "Select all tiles with stars.";
  const targetKey = (props.target_icon || "star").toLowerCase();
  const size = Math.min(4, Math.max(3, Number(props.grid_size) || 3));
  const TargetIcon = ICONS[targetKey] || Star;

  const tiles = useMemo(() => {
    if (Array.isArray(props.tiles) && props.tiles.length > 0) {
      return props.tiles.map((t, i) => ({
        id: t.id ?? i,
        iconKey: t.iconKey ?? (t.hasTarget ? targetKey : null),
      }));
    }
    return buildDefaultTiles(size, targetKey);
  }, []);

  const [selected, setSelected] = useState([]);
  const [done, setDone] = useState(false);

  const toggle = (id) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const targetIds = tiles.filter((t) => t.iconKey === targetKey).map((t) => t.id);
  const valid =
    selected.length === targetIds.length &&
    targetIds.every((id) => selected.includes(id));

  const onVerify = () => {
    setDone(true);
    callAction({
      name: "tile_captcha_submit",
      payload: { done: true, valid, selected_ids: selected, target_icon: targetKey },
    });
  };

  if (done) {
    return (
      <Card style={{ marginTop: 12, width: "100%", maxWidth: 360 }}>
        <CardContent style={{ padding: 16, fontSize: 13, color: "#64748b" }}>
          {valid ? "Verification passed." : "Verification failed. Try again in a new message."}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card style={{ marginTop: 12, width: "100%", maxWidth: 360, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
      <CardHeader style={{ paddingBottom: 8 }}>
        <CardTitle style={{ fontSize: 16, fontWeight: 600 }}>{title}</CardTitle>
        <p style={{ margin: "6px 0 0", fontSize: 13, color: "#64748b" }}>{instruction}</p>
      </CardHeader>
      <CardContent style={{ paddingTop: 0 }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: `repeat(${size}, 1fr)`,
            gap: 10,
            width: "100%",
          }}
        >
          {tiles.map((tile) => {
            const isOn = selected.includes(tile.id);
            const Icon = tile.iconKey ? (ICONS[tile.iconKey] || TargetIcon) : null;
            return (
              <button
                key={tile.id}
                type="button"
                onClick={() => toggle(tile.id)}
                style={{
                  width: "100%",
                  aspectRatio: "1",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  border: isOn ? "2px solid #2563eb" : "1px solid #e2e8f0",
                  borderRadius: 8,
                  backgroundColor: isOn ? "#eff6ff" : "#f8fafc",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                {Icon && (
                  <Icon
                    style={{
                      width: 28,
                      height: 28,
                      color: "#eab308",
                      fill: "#fef08a",
                      strokeWidth: 1.5,
                    }}
                  />
                )}
              </button>
            );
          })}
        </div>
      </CardContent>
      <CardFooter style={{ paddingTop: 12 }}>
        <Button size="sm" onClick={onVerify} disabled={selected.length === 0}>
          Done
        </Button>
      </CardFooter>
    </Card>
  );
}
