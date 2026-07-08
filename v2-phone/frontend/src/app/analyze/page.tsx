"use client";

import { useState } from "react";

import { AnalyzeForm } from "@/components/analyze/AnalyzeForm";
import { AnalyzeResult } from "@/components/analyze/AnalyzeResult";
import { Card } from "@/components/ui/Card";
import { analyzeListing } from "@/lib/api";
import { AnalyzeInput, ListingDetail } from "@/lib/types";

export default function AnalyzePage() {
  const [result, setResult] = useState<ListingDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(input: AnalyzeInput) {
    setLoading(true);
    setError(null);
    try {
      const detail = await analyzeListing(input);
      setResult(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Analyze a listing</h1>
      <p className="mt-2 text-muted">
        Paste in the details of a listing you found elsewhere and get an instant FlipIQ Score — nothing here is
        saved to the database.
      </p>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <AnalyzeForm onSubmit={handleSubmit} loading={loading} />

        {error && (
          <Card className="flex items-center p-6 text-sm text-[var(--avoid)]">{error}</Card>
        )}

        {!error && result && <AnalyzeResult result={result} />}

        {!error && !result && (
          <Card className="flex flex-col items-center justify-center gap-2 p-12 text-center text-muted">
            <p className="text-sm">Fill out the form and click &quot;Analyze listing&quot; to see your result.</p>
          </Card>
        )}
      </div>
    </div>
  );
}
