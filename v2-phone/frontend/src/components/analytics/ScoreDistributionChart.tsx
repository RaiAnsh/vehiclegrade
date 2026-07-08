"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { DashboardStats } from "@/lib/types";
import { chartTooltipStyle, chartAxisStyle, SCORE_BAND_COLORS } from "./chartTheme";

const BAND_ORDER = ["Excellent Buy", "Good Value", "Fair Market", "Slightly Overpriced", "Avoid"];

export function ScoreDistributionChart({ data }: { data: DashboardStats["score_distribution"] }) {
  const ordered = [...data].sort((a, b) => BAND_ORDER.indexOf(a.band) - BAND_ORDER.indexOf(b.band));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={ordered}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
        <XAxis dataKey="band" {...chartAxisStyle} interval={0} tick={{ ...chartAxisStyle.tick, fontSize: 10 }} />
        <YAxis allowDecimals={false} {...chartAxisStyle} />
        <Tooltip contentStyle={chartTooltipStyle} formatter={(value) => [value, "Listings"]} />
        <Bar dataKey="count" radius={[6, 6, 0, 0]}>
          {ordered.map((entry) => (
            <Cell key={entry.band} fill={SCORE_BAND_COLORS[entry.band] ?? "var(--accent)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
