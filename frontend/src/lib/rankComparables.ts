import { WorkspaceItem } from "@/hooks/useComparisonWorkspace";
import { ListingDetail } from "@/lib/types";

export interface RankedItem {
  item: WorkspaceItem;
  rank: number;
  reasons: string[];
}

// Deterministic sort over numbers every listing's report already computed -
// no new scoring model, just ordering the shortlist by the same rule-based
// numbers shown on each individual report. Primary: VehicleGrade Score
// (higher is better). Ties broken by confidence (more trustworthy numbers
// win), then by potential savings (bigger gap under market value wins).
export function rankComparables(items: WorkspaceItem[]): RankedItem[] {
  const withReports = items.filter((item): item is WorkspaceItem & { report: ListingDetail } => item.report !== null);

  const sorted = [...withReports].sort((a, b) => {
    const scoreDiff = b.report.vehiclegrade_score - a.report.vehiclegrade_score;
    if (scoreDiff !== 0) return scoreDiff;

    const confidenceDiff = b.report.confidence.score - a.report.confidence.score;
    if (confidenceDiff !== 0) return confidenceDiff;

    return b.report.potential_savings - a.report.potential_savings;
  });

  return sorted.map((item, index) => ({
    item,
    rank: index + 1,
    reasons: buildReasons(item.report),
  }));
}

function buildReasons(report: ListingDetail): string[] {
  const reasons = [`VehicleGrade Score ${report.vehiclegrade_score}/100 (${report.deal_label})`];

  if (report.potential_savings > 0) {
    reasons.push(`Priced about $${Math.round(report.potential_savings).toLocaleString()} under estimated market value`);
  } else if (report.potential_savings < 0) {
    reasons.push(`Priced about $${Math.round(Math.abs(report.potential_savings)).toLocaleString()} over estimated market value`);
  } else {
    reasons.push("Priced at estimated market value");
  }

  const overdueIssues = report.known_issues.filter((issue) => issue.status === "overdue").length;
  reasons.push(
    overdueIssues > 0
      ? `${overdueIssues} known issue${overdueIssues > 1 ? "s" : ""} already overdue at this mileage`
      : "No known issues overdue at this mileage"
  );

  reasons.push(`${report.confidence.level} confidence (${report.confidence.score}/100)`);

  return reasons;
}
