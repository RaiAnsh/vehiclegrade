"use client";

import { useState } from "react";

import { InputModeToggle, InputMode } from "@/components/analyze/InputModeToggle";
import { ManualForm, ManualFormValue } from "@/components/analyze/ManualForm";
import { PasteTextForm } from "@/components/analyze/PasteTextForm";
import { VehicleReport } from "@/components/report/VehicleReport";
import { analyzeListing } from "@/lib/api";
import { AnalyzeInput, ListingDetail } from "@/lib/types";

export default function AnalyzePage() {
  const [mode, setMode] = useState<InputMode>("manual");
  const [formValue, setFormValue] = useState<ManualFormValue>({});
  const [report, setReport] = useState<ListingDetail | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit() {
    setSubmitting(true);
    setError(null);
    setReport(null);

    analyzeListing(formValue as AnalyzeInput)
      .then((data) => setReport(data))
      .catch((err) => setError(err.message))
      .finally(() => setSubmitting(false));
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Analyze a Listing</h1>
      <p className="mt-2 text-muted">
        Enter the details manually, or paste a listing description and let us prefill the form for you.
      </p>

      <div className="mt-6">
        <InputModeToggle mode={mode} onChange={setMode} />
      </div>

      <div className="mt-6 space-y-6">
        {mode === "paste" && (
          <PasteTextForm
            onParsed={(parsed) => {
              setFormValue((prev) => ({ ...prev, ...parsed }));
              setMode("manual");
            }}
          />
        )}

        {mode === "manual" && (
          <ManualForm value={formValue} onChange={setFormValue} onSubmit={handleSubmit} submitting={submitting} error={error} />
        )}

        {report && <VehicleReport listing={report} />}
      </div>
    </div>
  );
}
