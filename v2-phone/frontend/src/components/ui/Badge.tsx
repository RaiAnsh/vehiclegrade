import { ReactNode } from "react";
import clsx from "clsx";

import { DealLabel } from "@/lib/types";

const DEAL_STYLES: Record<DealLabel, string> = {
  "Excellent Buy": "bg-[var(--excellent)]/15 text-[var(--excellent)] ring-1 ring-[var(--excellent)]/30",
  "Good Value": "bg-[var(--good)]/15 text-[var(--good)] ring-1 ring-[var(--good)]/30",
  "Fair Market": "bg-[var(--fair)]/15 text-[var(--fair)] ring-1 ring-[var(--fair)]/30",
  "Slightly Overpriced": "bg-[var(--slight)]/15 text-[var(--slight)] ring-1 ring-[var(--slight)]/30",
  Avoid: "bg-[var(--avoid)]/15 text-[var(--avoid)] ring-1 ring-[var(--avoid)]/30",
};

export function DealBadge({ label }: { label: DealLabel }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium tracking-wide",
        DEAL_STYLES[label]
      )}
    >
      {label}
    </span>
  );
}

export function Badge({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium text-muted glass-card",
        className
      )}
    >
      {children}
    </span>
  );
}
