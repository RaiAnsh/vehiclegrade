import { TitleStatus } from "@/lib/types";

// Generated vehicle thumbnail - a stylized car silhouette, no photos or
// external image assets. Fill color is keyed to body type, ring color to
// title status, so the grid is scannable at a glance before you read any text.
const BODY_TYPE_COLOR: Record<string, string> = {
  sedan: "#4f8cff",
  suv: "#34d399",
  truck: "#fbbf24",
  hatchback: "#a78bfa",
};

const TITLE_STATUS_RING: Record<TitleStatus, string> = {
  clean: "var(--excellent)",
  unknown: "var(--fair)",
  rebuilt: "var(--slight)",
  salvage: "var(--avoid)",
};

// Body-type-specific car silhouettes: differ mainly in roofline/cargo profile
// so sedan vs. suv vs. truck vs. hatchback read distinctly even at small size.
const BODY_PATHS: Record<string, string> = {
  sedan: "M6 34 L9 24 Q12 18 20 18 L34 18 Q42 18 45 24 L48 34 L48 38 L6 38 Z",
  suv: "M6 34 L8 22 Q10 16 20 16 L34 16 Q44 16 46 22 L48 34 L48 39 L6 39 Z",
  truck: "M6 34 L7 26 Q8 20 16 20 L26 20 L26 34 M26 26 L40 26 Q45 26 46 30 L48 34 L48 38 L6 38 Z",
  hatchback: "M6 34 L9 23 Q12 17 20 17 L32 17 Q40 17 44 24 L48 34 L48 38 L6 38 Z",
};

interface VehicleGlyphProps {
  bodyType: string;
  titleStatus: TitleStatus;
  size?: number;
}

export function VehicleGlyph({ bodyType, titleStatus, size = 56 }: VehicleGlyphProps) {
  const fill = BODY_TYPE_COLOR[bodyType] ?? "var(--accent)";
  const ring = TITLE_STATUS_RING[titleStatus] ?? "var(--muted)";
  const path = BODY_PATHS[bodyType] ?? BODY_PATHS.sedan;

  return (
    <svg width={size} height={size} viewBox="0 0 56 56" fill="none" aria-hidden="true">
      <rect x="1.5" y="1.5" width="53" height="53" rx="16" stroke={ring} strokeWidth="1.5" opacity="0.6" />
      <path d={path} fill={fill} opacity="0.18" />
      <path d={path} stroke={fill} strokeWidth="1.5" strokeLinejoin="round" />
      <circle cx="16" cy="38" r="3" fill={fill} opacity="0.8" />
      <circle cx="38" cy="38" r="3" fill={fill} opacity="0.8" />
    </svg>
  );
}
