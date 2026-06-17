import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Download, Sheet } from "lucide-react";

export default function XlsxPreview() {
  const filename = props.filename || "spreadsheet.xlsx";
  const sheets = props.sheets || [];
  const sessionKey = props.session_key;
  const [activeSheet, setActiveSheet] = useState(0);
  const [downloading, setDownloading] = useState(false);

  const handleDownload = () => {
    setDownloading(true);
    callAction({ name: "xlsx_download", payload: { session_key: sessionKey, filename } });
    setTimeout(() => setDownloading(false), 3000);
  };

  const sheet = sheets[activeSheet] || {};
  const headers = sheet.headers || [];
  const allRows = sheet.rows || [];
  const previewRows = allRows.slice(0, 100);
  const colCount = Math.max(headers.length, ...previewRows.map((r) => r?.length || 0), 1);

  return (
    <div className="mt-3 w-full max-w-2xl">
      {/* Toolbar */}
      <div className="flex items-center justify-between rounded-t-md border border-b-0 bg-muted/30 px-3 py-2">
        <div className="flex items-center gap-2 text-sm">
          <Sheet className="h-4 w-4 text-green-600" />
          <span className="font-medium">{filename}</span>
          {sheets.length > 0 && (
            <span className="text-xs text-muted-foreground">
              {allRows.length} row{allRows.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
        <Button
          size="sm"
          variant="outline"
          className="gap-1.5 text-xs"
          onClick={handleDownload}
          disabled={downloading}
        >
          <Download className="h-3.5 w-3.5" />
          {downloading ? "Preparing..." : "Download .xlsx"}
        </Button>
      </div>

      {/* Sheet tabs */}
      {sheets.length > 1 && (
        <div className="flex gap-0 border border-b-0 border-t-0 bg-muted/20 px-2 pt-1">
          {sheets.map((s, i) => (
            <button
              key={i}
              onClick={() => setActiveSheet(i)}
              className={`rounded-t px-3 py-1 text-xs transition-colors focus:outline-none ${
                i === activeSheet
                  ? "border border-b-0 border-border bg-background font-medium text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {s.name || `Sheet${i + 1}`}
            </button>
          ))}
        </div>
      )}

      {/* Grid */}
      <div
        className={`overflow-auto border ${sheets.length > 1 ? "border-t-0 rounded-b-md" : "rounded-b-md"}`}
        style={{ maxHeight: "340px" }}
      >
        <table className="w-full border-collapse text-xs">
          {headers.length > 0 && (
            <thead className="sticky top-0 z-10">
              <tr>
                <th className="w-8 border-b border-r bg-muted/60 px-1 py-1.5 text-center text-[10px] text-muted-foreground">
                  #
                </th>
                {headers.map((h, ci) => (
                  <th
                    key={ci}
                    className="whitespace-nowrap border-b border-r bg-muted/60 px-2.5 py-1.5 text-left font-semibold text-foreground/90"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
          )}
          <tbody>
            {previewRows.length === 0 ? (
              <tr>
                <td
                  colSpan={colCount + 1}
                  className="px-3 py-4 text-center text-xs text-muted-foreground"
                >
                  No data
                </td>
              </tr>
            ) : (
              previewRows.map((row, ri) => (
                <tr key={ri} className={ri % 2 === 1 ? "bg-muted/10" : "bg-background"}>
                  <td className="border-b border-r bg-muted/25 px-1 py-1 text-center text-[10px] text-muted-foreground">
                    {ri + 1}
                  </td>
                  {Array.from({ length: colCount }).map((_, ci) => (
                    <td
                      key={ci}
                      className="whitespace-nowrap border-b border-r px-2.5 py-1 text-foreground/80"
                    >
                      {row?.[ci] ?? ""}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {allRows.length > 100 && (
        <div className="mt-1 text-right text-[10px] text-muted-foreground">
          Preview: 100 of {allRows.length} rows
        </div>
      )}
    </div>
  );
}
