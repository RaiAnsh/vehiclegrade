import { Condition } from "@/lib/types";

// Generated device thumbnail - a stylized phone silhouette, no photos or
// external image assets. Fill color is keyed to the phone generation, ring
// color to condition, so the grid is scannable at a glance before you read
// any text.
const MODEL_COLORS: Record<string, string> = {
  "iPhone 11": "#64748b",
  "iPhone 12": "#38bdf8",
  "iPhone 13": "#818cf8",
  "iPhone 14": "#34d399",
  "iPhone 15": "#fbbf24",
};

const CONDITION_RING: Record<Condition, string> = {
  excellent: "var(--excellent)",
  good: "var(--good)",
  fair: "var(--fair)",
  poor: "var(--avoid)",
};

interface DeviceGlyphProps {
  model: string;
  condition: Condition;
  size?: number;
}

export function DeviceGlyph({ model, condition, size = 56 }: DeviceGlyphProps) {
  const fill = MODEL_COLORS[model] ?? "var(--accent)";
  const ring = CONDITION_RING[condition];

  return (
    <svg width={size} height={size} viewBox="0 0 56 56" fill="none" aria-hidden="true">
      <rect x="1.5" y="1.5" width="53" height="53" rx="16" stroke={ring} strokeWidth="1.5" opacity="0.6" />
      <rect x="16" y="8" width="24" height="40" rx="6" fill={fill} opacity="0.18" />
      <rect x="16" y="8" width="24" height="40" rx="6" stroke={fill} strokeWidth="1.5" />
      <rect x="22" y="12" width="12" height="2" rx="1" fill={fill} opacity="0.8" />
      <circle cx="28" cy="44" r="1.6" fill={fill} opacity="0.8" />
    </svg>
  );
}
