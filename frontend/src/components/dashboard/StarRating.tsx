interface StarRatingProps {
  value: number; // 0-5, supports half-star increments (e.g. 3.5)
  size?: number;
  color?: string;
  showValue?: boolean;
}

// Renders a row of 5 stars, each independently filled 0/50/100% based on how
// much of that star's point value is covered by `value`. Used for both the
// VehicleGrade score-as-stars display and the reliability rating.
export function StarRating({ value, size = 16, color = "var(--accent)", showValue = false }: StarRatingProps) {
  const clamped = Math.max(0, Math.min(5, value));

  return (
    <div className="flex items-center gap-1.5">
      <div className="flex items-center gap-0.5">
        {Array.from({ length: 5 }).map((_, i) => {
          const fill = Math.max(0, Math.min(1, clamped - i)) * 100;
          return (
            <span key={i} className="relative inline-block" style={{ width: size, height: size }}>
              <svg viewBox="0 0 24 24" width={size} height={size} className="absolute inset-0" fill="rgba(255,255,255,0.12)">
                <path d="M12 2.5l2.94 6.42 6.98.66-5.26 4.75 1.53 6.9L12 17.77l-6.19 3.46 1.53-6.9L2.08 9.58l6.98-.66L12 2.5z" />
              </svg>
              <span className="absolute inset-0 overflow-hidden" style={{ width: `${fill}%` }}>
                <svg viewBox="0 0 24 24" width={size} height={size} fill={color}>
                  <path d="M12 2.5l2.94 6.42 6.98.66-5.26 4.75 1.53 6.9L12 17.77l-6.19 3.46 1.53-6.9L2.08 9.58l6.98-.66L12 2.5z" />
                </svg>
              </span>
            </span>
          );
        })}
      </div>
      {showValue && <span className="text-sm text-muted">{clamped.toFixed(1)}</span>}
    </div>
  );
}
