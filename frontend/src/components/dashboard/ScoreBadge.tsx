import { DealLabel } from "@/lib/types";

const SCORE_COLOR: Record<DealLabel, string> = {
  "Exceptional Buy": "var(--excellent)",
  "Good Buy": "var(--good)",
  "Fair Deal": "var(--fair)",
  Overpriced: "var(--slight)",
  Avoid: "var(--avoid)",
};

interface ScoreBadgeProps {
  score: number;
  dealLabel: DealLabel;
  size?: number;
}

// A ring-gauge showing the 0-100 VehicleGrade Score, colored by the same band as
// the deal label so the number and the verdict always read as one signal.
export function ScoreBadge({ score, dealLabel, size = 52 }: ScoreBadgeProps) {
  const color = SCORE_COLOR[dealLabel];
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 48 48" className="-rotate-90">
        <circle cx="24" cy="24" r={radius} stroke="rgba(255,255,255,0.08)" strokeWidth="4" fill="none" />
        <circle
          cx="24"
          cy="24"
          r={radius}
          stroke={color}
          strokeWidth="4"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <span className="absolute text-sm font-semibold" style={{ color }}>
        {score}
      </span>
    </div>
  );
}
