import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SourceBadge } from "./SourceBadge";
import { DataSourceInfo, IssueStatus, KnownIssue } from "@/lib/types";

const STATUS_COLOR: Record<IssueStatus, string> = {
  not_yet_relevant: "var(--muted)",
  approaching: "var(--fair)",
  common_now: "var(--slight)",
  overdue: "var(--avoid)",
};

const STATUS_LABEL: Record<IssueStatus, string> = {
  not_yet_relevant: "Not Yet Relevant",
  approaching: "Approaching",
  common_now: "Common Now",
  overdue: "Overdue",
};

const SEVERITY_LABEL: Record<string, string> = {
  minor: "Minor",
  moderate: "Moderate",
  severe: "Severe",
};

interface KnownIssuesListProps {
  issues: KnownIssue[];
  source: DataSourceInfo;
}

export function KnownIssuesList({ issues, source }: KnownIssuesListProps) {
  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium">Known Issues</h2>
        <SourceBadge {...source} />
      </div>
      <p className="mt-1 text-sm text-muted">
        Every known issue for this generation, checked against this listing&apos;s actual mileage.
      </p>

      <div className="mt-5 space-y-4">
        {issues.map((issue) => {
          const color = STATUS_COLOR[issue.status];
          return (
            <div key={issue.title} className="rounded-xl border border-white/5 p-4" style={{ borderLeft: `3px solid ${color}` }}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-medium">{issue.title}</p>
                <div className="flex items-center gap-2">
                  <Badge>{SEVERITY_LABEL[issue.severity]}</Badge>
                  <span
                    className="rounded-full px-3 py-1 text-xs font-medium"
                    style={{ backgroundColor: `${color}26`, color }}
                  >
                    {STATUS_LABEL[issue.status]}
                  </span>
                </div>
              </div>

              <p className="mt-2 text-sm text-muted">{issue.description}</p>
              {issue.symptoms && (
                <p className="mt-2 text-sm text-muted">
                  <span className="font-medium">What to look for: </span>
                  {issue.symptoms}
                </p>
              )}
              <p className="mt-2 text-sm" style={{ color }}>
                {issue.status_copy}
              </p>

              <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-white/5 pt-3 text-xs text-muted">
                <span>
                  Estimated repair: ${issue.estimated_repair_cost_min.toLocaleString()} - $
                  {issue.estimated_repair_cost_max.toLocaleString()}
                </span>
                <span>Typical onset: {issue.typical_mileage_km.toLocaleString()} km</span>
              </div>

              <p className="mt-2 text-sm">{issue.recommendation}</p>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
