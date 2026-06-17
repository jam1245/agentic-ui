import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Copy, Download, Check, ChevronDown, ChevronUp } from "lucide-react";

const EXT = {
  python: "py", javascript: "js", typescript: "ts", tsx: "tsx", jsx: "jsx",
  json: "json", bash: "sh", shell: "sh", sh: "sh", sql: "sql", html: "html",
  css: "css", yaml: "yml", yml: "yml", markdown: "md", md: "md", r: "r",
  go: "go", rust: "rs", java: "java", kotlin: "kt", swift: "swift",
};

function extFor(lang, filename) {
  if (filename && filename.includes(".")) return filename;
  const key = (lang || "").toLowerCase().trim();
  const ext = EXT[key] || "txt";
  return filename ? filename : `snippet.${ext}`;
}

export default function CodeBlock() {
  const code = props.code ?? props.content ?? "";
  const language = (props.language || props.lang || "").trim();
  const title = props.title || props.filename || (language ? language : "Code");
  const filename = extFor(language, props.filename);
  const maxLines = Math.max(4, props.max_lines ?? props.maxLines ?? 12);

  const lines = useMemo(() => (code ? String(code).split("\n") : [""]), [code]);
  const collapsible = lines.length > maxLines;
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const visible = expanded || !collapsible ? lines : lines.slice(0, maxLines);
  const hiddenCount = lines.length - maxLines;

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  };

  const onDownload = () => {
    const blob = new Blob([code], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="mt-3 w-full max-w-2xl overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 py-3 px-4 border-b bg-muted/30">
        <div className="flex items-center gap-2 min-w-0">
          <CardTitle className="text-sm font-medium truncate">{title}</CardTitle>
          {language ? (
            <Badge variant="secondary" className="text-[10px] font-normal shrink-0">
              {language}
            </Badge>
          ) : null}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button type="button" variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={onCopy}>
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? "Copied" : "Copy"}
          </Button>
          <Button type="button" variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={onDownload}>
            <Download className="h-3.5 w-3.5" />
            Download
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="relative">
          {expanded && collapsible ? (
            <ScrollArea className="max-h-[min(70vh,520px)]">
              <pre
                className="m-0 px-4 py-3 text-[13px] leading-[1.55] font-mono text-foreground bg-muted/20 overflow-x-auto"
                style={{ tabSize: 2 }}
              >
                <code>{code}</code>
              </pre>
            </ScrollArea>
          ) : (
            <pre
              className="m-0 px-4 py-3 text-[13px] leading-[1.55] font-mono text-foreground bg-muted/20 overflow-x-auto"
              style={{ tabSize: 2 }}
            >
              <code>
                {visible.map((line, i) => {
                  const isFade = collapsible && !expanded && i === visible.length - 1;
                  return (
                    <span
                      key={i}
                      className="block whitespace-pre"
                      style={isFade ? { opacity: 0.35 } : undefined}
                    >
                      {line || " "}
                    </span>
                  );
                })}
              </code>
            </pre>
          )}
          {collapsible && !expanded ? (
            <div
              className="absolute inset-x-0 bottom-0 flex flex-col items-center justify-end pt-10 pb-2 pointer-events-none"
              style={{
                background: "linear-gradient(to bottom, transparent 0%, hsl(var(--card)) 55%, hsl(var(--card)) 100%)",
              }}
            >
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="h-8 gap-1 text-xs pointer-events-auto shadow-sm"
                onClick={() => setExpanded(true)}
              >
                <ChevronDown className="h-4 w-4" />
                Show all {lines.length} lines
                {hiddenCount > 0 ? ` (+${hiddenCount} more)` : ""}
              </Button>
            </div>
          ) : null}
        </div>
        {collapsible && expanded ? (
          <div className="flex justify-center border-t bg-muted/20 py-1.5">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 gap-1 text-xs"
              onClick={() => setExpanded(false)}
            >
              <ChevronUp className="h-4 w-4" />
              Collapse
            </Button>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
