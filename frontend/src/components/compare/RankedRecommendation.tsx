import { RankedItem } from "@/lib/rankComparables";

interface RankedRecommendationProps {
  ranked: RankedItem[];
}

// Deterministic ordering of the shortlist (see lib/rankComparables.ts) - not
// a new scoring model, just an explanation of why one listing outranks
// another using numbers already shown on each individual report.
export function RankedRecommendation({ ranked }: RankedRecommendationProps) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium">Worth inspecting first</h3>
      <ol className="space-y-3">
        {ranked.map(({ item, rank, reasons }) => {
          const report = item.report!;
          return (
            <li key={item.id} className="glass-card rounded-2xl p-4">
              <div className="flex items-center gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--surface-hover)] text-xs font-semibold">
                  {rank}
                </span>
                <span className="text-sm font-medium">
                  {report.year} {report.make} {report.model}
                  {report.trim ? ` ${report.trim}` : ""}
                </span>
              </div>
              <ul className="mt-2 ml-10 list-disc space-y-1 text-xs text-muted">
                {reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
