import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SourceBadge } from "./SourceBadge";
import { DataSourceInfo, RepairEstimate } from "@/lib/types";

const SEVERITY_LABEL: Record<string, string> = {
  minor: "Minor",
  moderate: "Moderate",
  major: "Major",
  severe: "Severe",
};

interface RepairEstimateCardProps {
  estimate: RepairEstimate;
  source: DataSourceInfo;
}

// Renders the issues the buyer's own pasted description mentioned - "the
// transmission is slipping", "windshield is cracked" - turned into real
// repair-cost ranges and a repair-adjusted offer. Absent entirely when the
// listing had no description text or nothing detectable in it.
export function RepairEstimateCard({ estimate, source }: RepairEstimateCardProps) {
  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium">Repair Cost Estimate</h2>
        <SourceBadge {...source} />
      </div>
      <p className="mt-1 text-sm text-muted">
        Issues detected in the listing&apos;s own description, with an estimated cost to fix each one.
      </p>

      <div className="mt-5 space-y-3">
        {estimate.detected_issues.map((issue) => (
          <div key={issue.title} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/5 p-4">
            <div className="flex items-center gap-2">
              <p className="font-medium">{issue.title}</p>
              <Badge>{SEVERITY_LABEL[issue.severity] ?? issue.severity}</Badge>
              {issue.matched_known_issue && (
                <span className="text-xs text-[var(--good)]">Matches a documented issue for this generation</span>
              )}
            </div>
            <span className="text-sm text-muted">
              ${issue.estimated_repair_cost_min.toLocaleString()} - ${issue.estimated_repair_cost_max.toLocaleString()}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-4 border-t border-white/5 pt-5 sm:grid-cols-3">
        <div>
          <p className="text-xs text-muted">Total estimated repair cost</p>
          <p className="mt-1 text-xl font-semibold text-[var(--avoid)]">
            ${estimate.total_estimated_repair_cost_min.toLocaleString()} - $
            {estimate.total_estimated_repair_cost_max.toLocaleString()}
          </p>
        </div>
        <div className="sm:col-span-2">
          <p className="text-xs text-muted">Repair-adjusted offer range</p>
          <p className="mt-1 text-xl font-semibold">
            ${estimate.adjusted_offer_min.toLocaleString()} - ${estimate.adjusted_offer_max.toLocaleString()}
          </p>
        </div>
      </div>

      <p className="mt-4 text-xs text-muted">{estimate.disclosure}</p>
    </Card>
  );
}
