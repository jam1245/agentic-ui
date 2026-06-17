import { useState, useEffect, useCallback, useRef } from "react";
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

const COLS = 10;
const ROWS = 20;
const CELL = 22;

const SHAPES = [
  { m: [[1, 1, 1, 1]], c: "#22d3ee" },
  { m: [[1, 1], [1, 1]], c: "#eab308" },
  { m: [[0, 1, 0], [1, 1, 1]], c: "#a855f7" },
  { m: [[1, 1, 0], [0, 1, 1]], c: "#22c55e" },
  { m: [[0, 1, 1], [1, 1, 0]], c: "#ef4444" },
  { m: [[1, 0, 0], [1, 1, 1]], c: "#3b82f6" },
  { m: [[0, 0, 1], [1, 1, 1]], c: "#f97316" },
];

function emptyBoard() {
  return Array.from({ length: ROWS }, () => Array(COLS).fill(null));
}

function rotate(matrix) {
  const rows = matrix.length;
  const cols = matrix[0].length;
  const out = Array.from({ length: cols }, () => Array(rows).fill(0));
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) out[c][rows - 1 - r] = matrix[r][c];
  }
  return out;
}

function collides(board, matrix, px, py) {
  for (let r = 0; r < matrix.length; r++) {
    for (let c = 0; c < matrix[r].length; c++) {
      if (!matrix[r][c]) continue;
      const y = py + r;
      const x = px + c;
      if (x < 0 || x >= COLS || y >= ROWS) return true;
      if (y >= 0 && board[y][x]) return true;
    }
  }
  return false;
}

function merge(board, matrix, px, py, color) {
  const next = board.map((row) => [...row]);
  for (let r = 0; r < matrix.length; r++) {
    for (let c = 0; c < matrix[r].length; c++) {
      if (!matrix[r][c]) continue;
      const y = py + r;
      const x = px + c;
      if (y >= 0 && y < ROWS && x >= 0 && x < COLS) next[y][x] = color;
    }
  }
  return next;
}

function clearLines(board) {
  const kept = board.filter((row) => row.some((cell) => !cell));
  const cleared = ROWS - kept.length;
  while (kept.length < ROWS) kept.unshift(Array(COLS).fill(null));
  return { board: kept, cleared };
}

function randomPiece() {
  const s = SHAPES[Math.floor(Math.random() * SHAPES.length)];
  return { matrix: s.m.map((r) => [...r]), color: s.c };
}

export default function TetrisGame() {
  const title = props.title || "Tetris";
  const [board, setBoard] = useState(emptyBoard);
  const [piece, setPiece] = useState(() => randomPiece());
  const [pos, setPos] = useState({ x: 3, y: 0 });
  const [score, setScore] = useState(0);
  const [over, setOver] = useState(false);
  const [paused, setPaused] = useState(false);
  const stateRef = useRef({ board, piece, pos, over, paused });

  useEffect(() => {
    stateRef.current = { board, piece, pos, over, paused };
  }, [board, piece, pos, over, paused]);

  const spawn = useCallback((b) => {
    const p = randomPiece();
    const start = { x: Math.floor((COLS - p.matrix[0].length) / 2), y: 0 };
    if (collides(b, p.matrix, start.x, start.y)) {
      setOver(true);
      return null;
    }
    setPiece(p);
    setPos(start);
    return p;
  }, []);

  const lockPiece = useCallback(() => {
    const { board: b, piece: p, pos: ps } = stateRef.current;
    let next = merge(b, p.matrix, ps.x, ps.y, p.color);
    const { board: cleared, cleared: lines } = clearLines(next);
    if (lines) setScore((s) => s + lines * 100);
    setBoard(cleared);
    spawn(cleared);
  }, [spawn]);

  const tryMove = useCallback((dx, dy, nextMatrix) => {
    const { board: b, piece: p, pos: ps, over: o, paused: pa } = stateRef.current;
    if (o || pa) return false;
    const matrix = nextMatrix || p.matrix;
    if (!collides(b, matrix, ps.x + dx, ps.y + dy)) {
      setPos({ x: ps.x + dx, y: ps.y + dy });
      if (nextMatrix) setPiece({ ...p, matrix: nextMatrix });
      return true;
    }
    return false;
  }, []);

  const softDrop = useCallback(() => {
    if (!tryMove(0, 1)) lockPiece();
  }, [tryMove, lockPiece]);

  const hardDrop = useCallback(() => {
    const { board: b, piece: p, pos: ps, over: o, paused: pa } = stateRef.current;
    if (o || pa) return;
    let y = ps.y;
    while (!collides(b, p.matrix, ps.x, y + 1)) y += 1;
    setPos({ x: ps.x, y });
    setTimeout(lockPiece, 0);
  }, [lockPiece]);

  const { bind: focusBind } = useFocusedKeys({
    onDeactivate: () => setPaused(true),
    onActivate: () => {
      if (!stateRef.current.over) setPaused(false);
    },
    onKeyDown: (e) => {
      if (stateRef.current.over) return;
      const k = e.key;
      if (k === "ArrowLeft") tryMove(-1, 0);
      else if (k === "ArrowRight") tryMove(1, 0);
      else if (k === "ArrowDown") softDrop();
      else if (k === "ArrowUp") {
        const rotated = rotate(stateRef.current.piece.matrix);
        tryMove(0, 0, rotated);
      } else if (k === " ") hardDrop();
      else if (k === "p" || k === "P") setPaused((p) => !p);
    },
  });

  useEffect(() => {
    const id = setInterval(() => softDrop(), 650);
    return () => clearInterval(id);
  }, [softDrop]);

  const reset = () => {
    setBoard(emptyBoard());
    setScore(0);
    setOver(false);
    setPaused(false);
    const p = randomPiece();
    setPiece(p);
    setPos({ x: 3, y: 0 });
  };

  const display = board.map((row) => [...row]);
  if (!over && !paused) {
    for (let r = 0; r < piece.matrix.length; r++) {
      for (let c = 0; c < piece.matrix[r].length; c++) {
        if (!piece.matrix[r][c]) continue;
        const y = pos.y + r;
        const x = pos.x + c;
        if (y >= 0 && y < ROWS && x >= 0 && x < COLS) display[y][x] = piece.color;
      }
    }
  }

  return (
    <Card className="mt-3 w-full max-w-xs" {...focusBind}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-base">{title}</CardTitle>
          <span className="text-sm font-medium tabular-nums">Score: {score}</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Arrows move/rotate · Down soft drop · Space hard drop · P pause
        </p>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-3 pb-4">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: `repeat(${COLS}, ${CELL}px)`,
            gap: 1,
            padding: 4,
            backgroundColor: "#0f172a",
            borderRadius: 8,
            border: "2px solid #334155",
          }}
        >
          {display.map((row, ri) =>
            row.map((cell, ci) => (
              <div
                key={`${ri}-${ci}`}
                style={{
                  width: CELL,
                  height: CELL,
                  borderRadius: 3,
                  backgroundColor: cell || "#1e293b",
                  boxShadow: cell ? "inset 0 -2px 0 rgba(0,0,0,0.25)" : "none",
                }}
              />
            ))
          )}
        </div>
        {over && <p className="text-sm font-medium text-destructive">Game over</p>}
        {paused && !over && <p className="text-sm text-muted-foreground">Paused</p>}
        <Button size="sm" variant="outline" onClick={reset}>
          {over ? "Play again" : "Reset"}
        </Button>
      </CardContent>
    </Card>
  );
}
