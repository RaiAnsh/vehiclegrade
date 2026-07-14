"use client";

import { ListingIntake } from "@/components/analyze/ListingIntake";
import { ManualFormValue } from "@/components/analyze/ManualForm";
import { ListingDetail } from "@/lib/types";

interface WorkspaceItemEditorProps {
  index: number;
  formValue: ManualFormValue;
  report: ListingDetail | null;
  onFormValueChange: (value: ManualFormValue) => void;
  onReportChange: (report: ListingDetail | null) => void;
  onRemove: () => void;
}

// One listing slot in the Comparison Workspace. Reuses the exact same
// paste -> confirm -> analyze flow as the standalone Analyze page, so a
// listing added here goes through the same review step before it's scored.
export function WorkspaceItemEditor({
  index,
  formValue,
  report,
  onFormValueChange,
  onReportChange,
  onRemove,
}: WorkspaceItemEditorProps) {
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

      <ListingIntake
        compact
        initialFormValue={formValue}
        onFormValueChange={onFormValueChange}
        onAnalyzed={onReportChange}
      />

      {report && (
        <p className="mt-3 text-xs text-[var(--good)]">
          Analyzed &mdash; VehicleGrade Score {report.vehiclegrade_score}/100
        </p>
      )}
    </div>
  );
}
