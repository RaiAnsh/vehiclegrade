import { Card } from "@/components/ui/Card";
import { SourceBadge } from "./SourceBadge";
import { DataSourceInfo, Verdict, VerdictRecommendation } from "@/lib/types";

const RECOMMENDATION_COLOR: Record<VerdictRecommendation, string> = {
  Recommended: "var(--good)",
  Consider: "var(--fair)",
  Avoid: "var(--avoid)",
};

interface VerdictCardProps {
  verdict: Verdict;
  source: DataSourceInfo;
}

export function VerdictCard({ verdict, source }: VerdictCardProps) {
  const color = RECOMMENDATION_COLOR[verdict.recommendation];

  return (
    <Card className="p-6" style={{ borderLeft: `3px solid ${color}` }}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-medium">Verdict</h2>
          <span
            className="rounded-full px-3 py-1 text-xs font-medium"
            style={{ backgroundColor: `${color}26`, color }}
          >
            {verdict.recommendation}
          </span>
        </div>
        <SourceBadge {...source} />
      </div>
      <p className="mt-3 text-sm text-muted">{verdict.paragraph}</p>
    </Card>
  );
}
