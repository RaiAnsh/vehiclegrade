import clsx from "clsx";
import { DataSourceType } from "@/lib/types";

const SOURCE_STYLES: Record<DataSourceType, string> = {
  reference_data: "bg-[var(--good)]/15 text-[var(--good)] ring-1 ring-[var(--good)]/30",
  market_sample: "bg-[var(--fair)]/15 text-[var(--fair)] ring-1 ring-[var(--fair)]/30",
  estimate: "bg-white/10 text-muted ring-1 ring-white/15",
};

interface SourceBadgeProps {
  source: DataSourceType;
  label: string;
  className?: string;
}

// Small reusable pill labeling exactly where a report section's numbers came
// from - reference database, the seeded marketplace sample, or a rule-based
// estimate - so nothing in the report implies more certainty than it has.
export function SourceBadge({ source, label, className }: SourceBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium tracking-wide",
        SOURCE_STYLES[source],
        className
      )}
    >
      {label}
    </span>
  );
}
