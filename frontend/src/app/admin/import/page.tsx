"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { Tabs } from "@/components/ui/Tabs";
import { Textarea } from "@/components/ui/Textarea";
import { useToast } from "@/components/ui/Toast";
import { RequirePermission } from "@/components/admin/RequirePermission";
import { useAdminAuth } from "@/hooks/useAdminAuth";
import { addCsvRows, addPasteRows, createImportBatch, csvTemplateUrl, previewCsv, processBatch } from "@/lib/adminApi";
import { CSV_CANONICAL_FIELDS } from "@/lib/adminTypes";
import { parseCsv, ParsedCsv } from "@/lib/csvParse";

type Mode = "paste_single" | "paste_multi" | "csv_upload";

const PLACEHOLDER = `2018 Honda Civic EX
82,000 km
Automatic
$19,500
Clean title
Hamilton

Well maintained, new brakes.`;

export default function NewImportPage() {
  const { accessToken } = useAdminAuth();
  const { showToast } = useToast();
  const router = useRouter();

  const [mode, setMode] = useState<Mode>("paste_single");
  const [texts, setTexts] = useState<string[]>([""]);
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvPreview, setCsvPreview] = useState<Awaited<ReturnType<typeof previewCsv>> | null>(null);
  const [parsedCsv, setParsedCsv] = useState<ParsedCsv | null>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [csvLoading, setCsvLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFileSelected(file: File) {
    if (!accessToken) return;
    setCsvFile(file);
    setCsvLoading(true);
    try {
      const [preview, text] = await Promise.all([previewCsv(accessToken, file), file.text()]);
      setCsvPreview(preview);
      setParsedCsv(parseCsv(text));
      const mapping: Record<string, string> = {};
      preview.headers.forEach((header) => {
        if (preview.suggested_mapping[header]) mapping[header] = preview.suggested_mapping[header] as string;
      });
      setColumnMapping(mapping);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Couldn't read that CSV", "error");
      setCsvFile(null);
    } finally {
      setCsvLoading(false);
    }
  }

  async function handleSubmitPaste() {
    if (!accessToken) return;
    const nonEmpty = texts.map((t) => t.trim()).filter(Boolean);
    if (nonEmpty.length === 0) {
      showToast("Paste at least one listing", "error");
      return;
    }
    setSubmitting(true);
    try {
      const batch = await createImportBatch(accessToken, { source_type: mode as "paste_single" | "paste_multi", notes: notes || undefined });
      await addPasteRows(accessToken, batch.id, nonEmpty);
      await processBatch(accessToken, batch.id);
      showToast(`Batch #${batch.id} created and processed`, "success");
      router.push(`/admin/batches/${batch.id}`);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Import failed", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmitCsv() {
    if (!accessToken || !csvFile || !parsedCsv) return;
    const mappedFieldCount = Object.values(columnMapping).filter(Boolean).length;
    if (mappedFieldCount === 0) {
      showToast("Map at least one column before importing", "error");
      return;
    }
    setSubmitting(true);
    try {
      const batch = await createImportBatch(accessToken, {
        source_type: "csv_upload",
        column_mapping: columnMapping,
        original_filename: csvFile.name,
        notes: notes || undefined,
      });
      await addCsvRows(accessToken, batch.id, parsedCsv.rows);
      await processBatch(accessToken, batch.id);
      showToast(`Batch #${batch.id} created and processed (${parsedCsv.rows.length} rows)`, "success");
      router.push(`/admin/batches/${batch.id}`);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Import failed", "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <RequirePermission permission="ingest">
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">New import</h1>
      <p className="mt-1 text-sm text-muted">
        Every row is normalized, validated, and quality-scored before it can ever influence a market estimate — see
        the review queue after processing.
      </p>

      <div className="mt-6">
        <Tabs
          tabs={[
            { value: "paste_single", label: "Paste one listing" },
            { value: "paste_multi", label: "Paste multiple" },
            { value: "csv_upload", label: "CSV upload" },
          ]}
          active={mode}
          onChange={(v) => setMode(v as Mode)}
        />
      </div>

      {(mode === "paste_single" || mode === "paste_multi") && (
        <Card className="mt-6 p-6">
          <div className="space-y-4">
            {texts.map((text, index) => (
              <div key={index} className="relative">
                <Textarea
                  rows={6}
                  placeholder={index === 0 ? PLACEHOLDER : "Paste another listing…"}
                  value={text}
                  onChange={(e) => {
                    const next = [...texts];
                    next[index] = e.target.value;
                    setTexts(next);
                  }}
                />
                {mode === "paste_multi" && texts.length > 1 && (
                  <button
                    type="button"
                    onClick={() => setTexts(texts.filter((_, i) => i !== index))}
                    className="absolute top-2 right-2 text-xs text-muted hover:text-[var(--avoid)]"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}

            {mode === "paste_multi" && (
              <Button variant="secondary" onClick={() => setTexts([...texts, ""])}>
                + Add another listing
              </Button>
            )}

            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted">Batch notes (optional)</label>
              <Textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="e.g. sourced from Kijiji Autos, GTA search" />
            </div>

            <Button onClick={handleSubmitPaste} disabled={submitting}>
              {submitting ? "Processing…" : "Create & process batch"}
            </Button>
          </div>
        </Card>
      )}

      {mode === "csv_upload" && (
        <Card className="mt-6 p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium">Upload a CSV export</p>
              <p className="mt-1 text-xs text-muted">Headers are mapped below — nothing is auto-applied without confirmation.</p>
            </div>
            <a href={csvTemplateUrl()} className="text-xs text-[var(--good)] hover:underline">
              Download template
            </a>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            className="mt-4 block w-full text-sm text-muted file:mr-4 file:rounded-full file:border-0 file:bg-white/[0.06] file:px-4 file:py-2 file:text-sm file:font-medium file:text-foreground hover:file:bg-white/[0.1]"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFileSelected(file);
            }}
          />

          {csvLoading && (
            <div className="mt-6">
              <Skeleton className="h-4 w-48" />
              <div className="mt-3 space-y-2 rounded-2xl border border-white/10 p-4">
                <Skeleton className="h-8 w-full" />
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            </div>
          )}

          {csvPreview && parsedCsv && !csvLoading && (
            <div className="mt-6">
              <p className="text-sm text-muted">
                {parsedCsv.rows.length} row(s) found in <span className="text-foreground">{csvFile?.name}</span>
              </p>

              <div className="mt-3 overflow-x-auto rounded-2xl border border-white/10">
                <table className="w-full border-collapse text-left text-sm">
                  <thead className="bg-white/[0.03] text-xs uppercase tracking-wide text-muted">
                    <tr>
                      <th className="px-4 py-3 font-medium">CSV column</th>
                      <th className="px-4 py-3 font-medium">Sample value</th>
                      <th className="px-4 py-3 font-medium">Maps to</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {csvPreview.headers.map((header) => (
                      <tr key={header}>
                        <td className="px-4 py-3 font-medium">{header}</td>
                        <td className="px-4 py-3 text-muted">{csvPreview.sample_rows[0]?.[header] ?? "—"}</td>
                        <td className="px-4 py-3">
                          <Select
                            value={columnMapping[header] ?? ""}
                            onChange={(e) =>
                              setColumnMapping((prev) => ({ ...prev, [header]: e.target.value }))
                            }
                          >
                            <option value="">— ignore —</option>
                            {CSV_CANONICAL_FIELDS.map((field) => (
                              <option key={field} value={field}>
                                {field}
                              </option>
                            ))}
                          </Select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4">
                <label className="mb-1.5 block text-xs font-medium text-muted">Batch notes (optional)</label>
                <Textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
              </div>

              <Button className="mt-4" onClick={handleSubmitCsv} disabled={submitting}>
                {submitting ? "Processing…" : `Import ${parsedCsv.rows.length} row(s)`}
              </Button>
            </div>
          )}
        </Card>
      )}
    </div>
    </RequirePermission>
  );
}
