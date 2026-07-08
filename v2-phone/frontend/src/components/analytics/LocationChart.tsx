"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { DashboardStats } from "@/lib/types";
import { chartTooltipStyle, chartAxisStyle } from "./chartTheme";

export function LocationChart({ data }: { data: DashboardStats["listings_by_location"] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical" margin={{ left: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
        <XAxis type="number" allowDecimals={false} {...chartAxisStyle} />
        <YAxis dataKey="location" type="category" width={100} {...chartAxisStyle} />
        <Tooltip contentStyle={chartTooltipStyle} formatter={(value) => [value, "Listings"]} />
        <Bar dataKey="count" fill="var(--accent)" radius={[0, 6, 6, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
