"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { DashboardStats } from "@/lib/types";
import { chartTooltipStyle, chartAxisStyle } from "./chartTheme";

export function BatteryHealthChart({ data }: { data: DashboardStats["battery_by_model"] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
        <XAxis dataKey="model" {...chartAxisStyle} />
        <YAxis domain={[0, 100]} {...chartAxisStyle} />
        <Tooltip contentStyle={chartTooltipStyle} formatter={(value) => [`${value}%`, "Avg. battery"]} />
        <Bar dataKey="average_battery" fill="var(--excellent)" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
