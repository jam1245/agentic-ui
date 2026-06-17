import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const GAME_KEYS = new Set(["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", " ", "a", "A", "d", "D", "w", "W"]);

function isChatInput(el) {
  if (!el) return false;
  const tag = (el.tagName || "").toLowerCase();
  return tag === "input" || tag === "textarea" || el.isContentEditable;
}

function useFocusedKeys(handlers = {}) {
  const rootRef = useRef(null);
  const activeRef = useRef(false);
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  const deactivate = useCallback(() => {
    activeRef.current = false;
    handlersRef.current.onDeactivate?.();
  }, []);

  const activate = useCallback(() => {
    activeRef.current = true;
    handlersRef.current.onActivate?.();
  }, []);

  useEffect(() => {
    const onKeyDown = (e) => {
      if (isChatInput(e.target) && !rootRef.current?.contains(e.target)) {
        deactivate();
        return;
      }
      if (!activeRef.current || !rootRef.current) return;
      if (!document.body.contains(rootRef.current)) {
        deactivate();
        return;
      }
      if (GAME_KEYS.has(e.key)) e.preventDefault();
      handlersRef.current.onKeyDown?.(e);
    };
    const onKeyUp = (e) => {
      if (!activeRef.current) return;
      handlersRef.current.onKeyUp?.(e);
    };
    window.addEventListener("keydown", onKeyDown, true);
    window.addEventListener("keyup", onKeyUp, true);
    return () => {
      window.removeEventListener("keydown", onKeyDown, true);
      window.removeEventListener("keyup", onKeyUp, true);
      activeRef.current = false;
    };
  }, [deactivate]);

  const bind = {
    ref: rootRef,
    tabIndex: 0,
    onFocus: activate,
    onBlur: deactivate,
    onMouseDown: (e) => {
      activate();
      e.currentTarget.focus();
    },
    style: { outline: "none" },
  };

  return { bind };
}

const DEFAULT_PLATFORMS = [
  { x: 0, y: 248, w: 420, h: 12 },
  { x: 40, y: 190, w: 90, h: 10 },
  { x: 180, y: 150, w: 100, h: 10 },
  { x: 300, y: 110, w: 80, h: 10 },
  { x: 120, y: 70, w: 70, h: 10 },
];

export default function PlatformGame() {
  const title = props.title || "Platform runner";
  const W = props.width || 420;
  const H = props.height || 260;
  const PW = props.player_size || 28;
  const platforms = props.platforms || DEFAULT_PLATFORMS;
  const accent = props.color || "#ef4444";

  const [pos, setPos] = useState({ x: 48, y: 200 });
  const [won, setWon] = useState(false);
  const vel = useRef({ x: 0, y: 0 });
  const keys = useRef({});
  const posRef = useRef(pos);

  useEffect(() => { posRef.current = pos; }, [pos]);

  const { bind: focusBind } = useFocusedKeys({
    onDeactivate: () => { keys.current = {}; },
    onKeyDown: (e) => { keys.current[e.key] = true; },
    onKeyUp: (e) => { keys.current[e.key] = false; },
  });

  useEffect(() => {
    let frame;
    const speed = props.move_speed || 4;
    const jump = props.jump_force || 11;
    const gravity = props.gravity || 0.55;

    const tick = () => {
      let { x, y } = posRef.current;
      let vx = 0;
      if (keys.current.ArrowLeft || keys.current.a) vx = -speed;
      if (keys.current.ArrowRight || keys.current.d) vx = speed;

      let onGround = false;
      for (const p of platforms) {
        if (
          x + PW > p.x && x < p.x + p.w &&
          y + PW >= p.y && y + PW <= p.y + 14 &&
          vel.current.y >= 0
        ) {
          y = p.y - PW;
          vel.current.y = 0;
          onGround = true;
        }
      }

      if ((keys.current.ArrowUp || keys.current.w || keys.current[" "]) && onGround) {
        vel.current.y = -jump;
      }

      vel.current.y += gravity;
      vel.current.x = vx;
      x += vel.current.x;
      y += vel.current.y;

      if (x < 0) x = 0;
      if (x + PW > W) x = W - PW;
      if (y > H) {
        y = 40;
        vel.current.y = 0;
      }

      if (y < 30) setWon(true);

      setPos({ x, y });
      frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [platforms, W, H, PW]);

  const reset = () => {
    setPos({ x: 48, y: 200 });
    vel.current = { x: 0, y: 0 };
    setWon(false);
  };

  return (
    <Card className="mt-3" style={{ maxWidth: W + 32 }} {...focusBind}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        <p className="text-xs text-muted-foreground">
          Arrows or WASD move · Up/Space jump · Reach the top platform
        </p>
      </CardHeader>
      <CardContent className="pb-4">
        <div
          style={{
            position: "relative",
            width: W,
            height: H,
            borderRadius: 10,
            border: "2px solid #334155",
            background: "linear-gradient(180deg, #0ea5e9 0%, #bae6fd 55%, #86efac 100%)",
            overflow: "hidden",
          }}
        >
          {platforms.map((p, i) => (
            <div
              key={i}
              style={{
                position: "absolute",
                left: p.x,
                top: p.y,
                width: p.w,
                height: p.h,
                borderRadius: 4,
                backgroundColor: "#78350f",
                boxShadow: "inset 0 2px 0 #a16207",
              }}
            />
          ))}
          <div
            style={{
              position: "absolute",
              left: pos.x,
              top: pos.y,
              width: PW,
              height: PW,
              borderRadius: 6,
              backgroundColor: accent,
              border: "2px solid #991b1b",
              boxShadow: "0 2px 4px rgba(0,0,0,0.3)",
            }}
          />
          {won && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "rgba(15,23,42,0.5)",
                color: "#fff",
                fontWeight: 600,
                fontSize: 18,
              }}
            >
              You reached the top
            </div>
          )}
        </div>
        <Button size="sm" variant="outline" className="mt-3" onClick={reset}>
          Reset
        </Button>
      </CardContent>
    </Card>
  );
}
