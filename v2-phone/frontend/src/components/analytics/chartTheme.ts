// Shared Recharts styling so every chart in the analytics section matches
// the app's dark glassmorphism theme.

import type { CSSProperties } from "react";

export const chartAxisStyle = {
  tick: { fill: "#8b93a7", fontSize: 12 },
  tickLine: false,
  axisLine: { stroke: "rgba(255,255,255,0.09)" },
};

export const chartTooltipStyle: CSSProperties = {
  background: "#0a0e1a",
  border: "1px solid rgba(255,255,255,0.09)",
  borderRadius: 12,
  color: "#f4f6fb",
  fontSize: 13,
  boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
};

export const CHART_COLORS = ["#4f8cff", "#34d399", "#fbbf24", "#fb923c", "#a78bfa", "#f87171"];

export const CONDITION_COLORS: Record<string, string> = {
  excellent: "#34d399",
  good: "#4f8cff",
  fair: "#fbbf24",
  poor: "#f87171",
};

export const SCORE_BAND_COLORS: Record<string, string> = {
  "Excellent Buy": "#34d399",
  "Good Value": "#4f8cff",
  "Fair Market": "#fbbf24",
  "Slightly Overpriced": "#fb923c",
  Avoid: "#f87171",
};
