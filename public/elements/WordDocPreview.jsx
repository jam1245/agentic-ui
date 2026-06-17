import { useState } from "react";
import { Button } from "@/components/ui/button";
import { FileText, Download } from "lucide-react";

export default function WordDocPreview() {
  const title = props.title || "Document";
  const filename = props.filename || "document.docx";
  const sections = props.sections || [];
  const sessionKey = props.session_key;
  const [downloading, setDownloading] = useState(false);

  const handleDownload = () => {
    setDownloading(true);
    callAction({
      name: "word_doc_download",
      payload: { session_key: sessionKey, filename },
    });
    setTimeout(() => setDownloading(false), 3000);
  };

  return (
    <div className="mt-3 w-full max-w-2xl">
      <div className="mb-2 flex items-center justify-between rounded-md border bg-muted/30 px-3 py-2">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <FileText className="h-4 w-4" />
          <span className="font-medium">{filename}</span>
        </div>
        <Button
          size="sm"
          variant="outline"
          className="gap-1.5 text-xs"
          onClick={handleDownload}
          disabled={downloading}
        >
          <Download className="h-3.5 w-3.5" />
          {downloading ? "Preparing..." : "Download .docx"}
        </Button>
      </div>

      {/* Paper preview */}
      <div className="rounded-md border bg-white shadow-sm dark:bg-zinc-950">
        <div className="px-10 py-8">
          <h1 className="mb-5 border-b border-border pb-4 text-xl font-bold tracking-tight">
            {title}
          </h1>
          <div className="space-y-5">
            {sections.map((section, si) => (
              <div key={si}>
                {section.heading && (
                  <h2 className="mb-2 text-sm font-semibold text-foreground">{section.heading}</h2>
                )}
                <div className="space-y-2">
                  {(section.content || []).map((block, bi) => {
                    if (block.type === "paragraph") {
                      return (
                        <p key={bi} className="text-sm leading-relaxed text-foreground/85">
                          {block.text}
                        </p>
                      );
                    }
                    if (block.type === "bullets") {
                      return (
                        <ul key={bi} className="ml-3 space-y-1 text-sm text-foreground/85">
                          {(block.items || []).map((item, ii) => (
                            <li key={ii} className="flex gap-2">
                              <span className="mt-2 h-1 w-1 flex-shrink-0 rounded-full bg-foreground/50" />
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      );
                    }
                    if (block.type === "table") {
                      return (
                        <div key={bi} className="overflow-x-auto">
                          <table className="w-full border-collapse text-xs">
                            {block.headers?.length > 0 && (
                              <thead>
                                <tr>
                                  {block.headers.map((h, hi) => (
                                    <th
                                      key={hi}
                                      className="border border-border bg-muted/50 px-3 py-1.5 text-left font-semibold"
                                    >
                                      {h}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                            )}
                            <tbody>
                              {(block.rows || []).map((row, ri) => (
                                <tr key={ri} className={ri % 2 === 1 ? "bg-muted/20" : ""}>
                                  {row.map((cell, ci) => (
                                    <td key={ci} className="border border-border px-3 py-1.5">
                                      {cell}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
