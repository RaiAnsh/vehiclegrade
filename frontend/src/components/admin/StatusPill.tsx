import clsx from "clsx";

// Reuses the same 5-color semantic ramp as the public app's deal-quality
// badges (--excellent/--good/--fair/--slight/--avoid), applied here to
// pipeline states instead of deal quality - keeps the admin panel visually
// consistent with the rest of VehicleGrade rather than inventing a second
// color language.
const STYLES: Record<string, string> = {
  pending: "bg-[var(--good)]/15 text-[var(--good)] ring-1 ring-[var(--good)]/30",
  needs_review: "bg-[var(--fair)]/15 text-[var(--fair)] ring-1 ring-[var(--fair)]/30",
  approved: "bg-[var(--excellent)]/15 text-[var(--excellent)] ring-1 ring-[var(--excellent)]/30",
  rejected: "bg-[var(--avoid)]/15 text-[var(--avoid)] ring-1 ring-[var(--avoid)]/30",
  open: "bg-[var(--good)]/15 text-[var(--good)] ring-1 ring-[var(--good)]/30",
  processing: "bg-[var(--fair)]/15 text-[var(--fair)] ring-1 ring-[var(--fair)]/30",
  completed: "bg-[var(--excellent)]/15 text-[var(--excellent)] ring-1 ring-[var(--excellent)]/30",
  rolled_back: "bg-[var(--avoid)]/15 text-[var(--avoid)] ring-1 ring-[var(--avoid)]/30",
  low: "bg-[var(--avoid)]/15 text-[var(--avoid)] ring-1 ring-[var(--avoid)]/30",
  medium: "bg-[var(--fair)]/15 text-[var(--fair)] ring-1 ring-[var(--fair)]/30",
  high: "bg-[var(--excellent)]/15 text-[var(--excellent)] ring-1 ring-[var(--excellent)]/30",
};

export function StatusPill({ status }: { status: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium tracking-wide whitespace-nowrap",
        STYLES[status] ?? "glass-card text-muted"
      )}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
