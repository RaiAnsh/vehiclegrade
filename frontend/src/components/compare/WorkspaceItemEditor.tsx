"use client";

import { useState } from "react";

import { InputMode, InputModeToggle } from "@/components/analyze/InputModeToggle";
import { ManualForm, ManualFormValue } from "@/components/analyze/ManualForm";
import { PasteTextForm } from "@/components/analyze/PasteTextForm";
import { analyzeListing } from "@/lib/api";
import { AnalyzeInput, ListingDetail } from "@/lib/types";

interface WorkspaceItemEditorProps {
  index: number;
  formValue: ManualFormValue;
  report: ListingDetail | null;
  onFormValueChange: (value: ManualFormValue) => void;
  onReportChange: (report: ListingDetail | null) => void;
  onRemove: () => void;
}

// One listing slot in the Comparison Workspace. Reuses the exact same
// manual-entry / paste-and-review / analyze flow as the standalone Analyze
// page, so a listing added here goes through the same required review step
// before it's scored.
export function WorkspaceItemEditor({
  index,
  formValue,
  report,
  onFormValueChange,
  onReportChange,
  onRemove,
}: WorkspaceItemEditorProps) {
  const [mode, setMode] = useState<InputMode>("manual");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiFields, setAiFields] = useState<string[]>([]);

  function handleAnalyze() {
    setSubmitting(true);
    setError(null);
    analyzeListing(formValue as AnalyzeInput)
      .then((data) => onReportChange(data))
      .catch((err) => setError(err.message))
      .finally(() => setSubmitting(false));
  }

  const label = report ? `${report.year} ${report.make} ${report.model}` : `Listing ${index + 1}`;

  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-medium">{label}</h3>
        <button
          type="button"
          onClick={onRemove}
          className="text-xs text-muted underline underline-offset-2 hover:text-foreground"
        >
          Remove
        </button>
      </div>

      <div className="mb-4">
        <InputModeToggle mode={mode} onChange={setMode} />
      </div>

      {mode === "paste" && (
        <PasteTextForm
          onParsed={({ _fields_from_ai, ...parsed }) => {
            onFormValueChange({ ...formValue, ...parsed });
            setAiFields(_fields_from_ai ?? []);
            setMode("manual");
          }}
        />
      )}

      {mode === "manual" && (
        <ManualForm
          value={formValue}
          onChange={onFormValueChange}
          onSubmit={handleAnalyze}
          submitting={submitting}
          error={error}
          aiFields={aiFields}
        />
      )}

      {report && (
        <p className="mt-3 text-xs text-[var(--good)]">
          Analyzed &mdash; VehicleGrade Score {report.vehiclegrade_score}/100
        </p>
      )}
    </div>
  );
}
