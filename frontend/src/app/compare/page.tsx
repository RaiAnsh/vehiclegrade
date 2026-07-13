"use client";

import { useEffect } from "react";

import { ComparisonTable } from "@/components/compare/ComparisonTable";
import { RankedRecommendation } from "@/components/compare/RankedRecommendation";
import { WorkspaceItemEditor } from "@/components/compare/WorkspaceItemEditor";
import { useComparisonWorkspace } from "@/hooks/useComparisonWorkspace";
import { rankComparables } from "@/lib/rankComparables";
import { ListingDetail } from "@/lib/types";

const MIN_ITEMS = 2;

export default function ComparePage() {
  const { items, hydrated, addItem, removeItem, updateFormValue, setReport, canAddMore } =
    useComparisonWorkspace();

  // Comparing requires at least two listings - seed two empty slots the
  // first time someone visits with an empty workspace, rather than making
  // them click "Add listing" twice before they can do anything.
  useEffect(() => {
    if (hydrated && items.length === 0) {
      addItem();
      addItem();
    }
  }, [hydrated, items.length, addItem]);

  const analyzed = items.filter(
    (item): item is typeof item & { report: ListingDetail } => item.report !== null
  );
  const ranked = rankComparables(items);

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Comparison Workspace</h1>
      <p className="mt-2 text-muted">
        Add two or more listings, analyze each one, and see them ranked side by side. Nothing here
        is saved to an account &mdash; the workspace lives only in this browser.
      </p>

      <div className="mt-8 grid gap-6 sm:grid-cols-2">
        {items.map((item, index) => (
          <WorkspaceItemEditor
            key={item.id}
            index={index}
            formValue={item.formValue}
            report={item.report}
            onFormValueChange={(value) => updateFormValue(item.id, value)}
            onReportChange={(report) => setReport(item.id, report)}
            onRemove={() => removeItem(item.id)}
          />
        ))}
      </div>

      <div className="mt-6">
        <button
          type="button"
          onClick={addItem}
          disabled={!canAddMore}
          className="rounded-full glass-card px-4 py-2 text-sm transition-colors hover:bg-[var(--surface-hover)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          Add listing
        </button>
        {!canAddMore && <p className="mt-2 text-xs text-muted">Maximum of 10 listings per workspace.</p>}
      </div>

      {analyzed.length < MIN_ITEMS && (
        <p className="mt-8 text-sm text-muted">
          Analyze at least {MIN_ITEMS} listings to see a side-by-side comparison and ranked
          recommendation.
        </p>
      )}

      {analyzed.length >= MIN_ITEMS && (
        <div className="mt-10 space-y-8">
          <ComparisonTable items={analyzed} />
          <RankedRecommendation ranked={ranked} />
        </div>
      )}
    </div>
  );
}
