// Minimal RFC4180 CSV parser - handles quoted fields, commas/newlines inside
// quotes, and "" as an escaped quote. No library is installed for this (see
// package.json), and the admin CSV-upload flow needs the *entire* file
// parsed client-side (the backend's /csv-preview endpoint only returns a
// handful of sample rows for mapping purposes - see
// backend/app/routes/admin_ingestion.py), so a small hand-rolled parser is
// worth it here rather than pulling in a dependency for one feature.

export interface ParsedCsv {
  headers: string[];
  rows: Record<string, string>[];
}

export function parseCsv(text: string): ParsedCsv {
  const rows: string[][] = [];
  let field = "";
  let row: string[] = [];
  let inQuotes = false;

  const normalized = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");

  for (let i = 0; i < normalized.length; i++) {
    const char = normalized[i];

    if (inQuotes) {
      if (char === '"') {
        if (normalized[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += char;
      }
      continue;
    }

    if (char === '"') {
      inQuotes = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field);
      field = "";
      rows.push(row);
      row = [];
    } else {
      field += char;
    }
  }
  // Last field/row (files don't always end with a trailing newline).
  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }

  const nonEmptyRows = rows.filter((r) => !(r.length === 1 && r[0] === ""));
  if (nonEmptyRows.length === 0) return { headers: [], rows: [] };

  const headers = nonEmptyRows[0];
  const dataRows = nonEmptyRows.slice(1).map((cells) => {
    const record: Record<string, string> = {};
    headers.forEach((header, index) => {
      record[header] = cells[index] ?? "";
    });
    return record;
  });

  return { headers, rows: dataRows };
}
