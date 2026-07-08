"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { DashboardStats } from "@/lib/types";
import { chartTooltipStyle, chartAxisStyle } from "./chartTheme";

export function PriceByMakeChart({ data }: { data: DashboardStats["price_by_make"] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
        <XAxis dataKey="make" {...chartAxisStyle} />
        <YAxis {...chartAxisStyle} />
        <Tooltip contentStyle={chartTooltipStyle} formatter={(value) => [`$${Number(value).toLocaleString()}`, "Avg. price"]} />
        <Bar dataKey="average_price" fill="var(--accent)" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
