import { MatchType, MatchTypeTier } from "@/lib/types";

const TIER_COLOR: Record<MatchTypeTier, string> = {
  exact_vehicle: "var(--good)",
  generation: "var(--fair)",
  engine_component: "var(--fair)",
  unsupported: "var(--avoid)",
};

const TIER_LABEL: Record<MatchTypeTier, string> = {
  exact_vehicle: "Matched to this exact trim/engine",
  generation: "Matched to this generation (trim not identified)",
  engine_component: "Matched via a shared engine/component",
  unsupported: "No known-issue data recorded yet",
};

interface MatchTypeBadgeProps {
  matchType: MatchType | undefined;
}

// Names how specifically the known-issue/reliability data attached to this
// report actually matches the vehicle, rather than letting a generation-wide
// match read as if it were verified for this exact trim/engine.
export function MatchTypeBadge({ matchType }: MatchTypeBadgeProps) {
  if (!matchType) return null;
  const color = TIER_COLOR[matchType];

  return (
    <span className="rounded-full px-3 py-1 text-xs font-medium" style={{ backgroundColor: `${color}26`, color }}>
      {TIER_LABEL[matchType]}
    </span>
  );
}
