// Client-side CSV export - builds a CSV string from an array of flat
// objects and triggers a browser download via a Blob object URL. No
// server round-trip needed since the data's already in the client (either
// just-fetched JSON, or admin table rows already on screen).

function csvEscape(value: unknown): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  // Quote any field containing a comma, quote, or newline; double up embedded quotes.
  return /[",\n]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str;
}

export function toCsv<T extends Record<string, unknown>>(rows: T[], columns?: (keyof T)[]): string {
  if (rows.length === 0) return "";
  const keys = columns ?? (Object.keys(rows[0]) as (keyof T)[]);
  const header = keys.map((k) => csvEscape(String(k))).join(",");
  const body = rows.map((row) => keys.map((k) => csvEscape(row[k])).join(",")).join("\n");
  return `${header}\n${body}`;
}

export function downloadCsv(filename: string, csvContent: string) {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
