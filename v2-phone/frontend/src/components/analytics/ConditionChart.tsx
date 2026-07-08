"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { DashboardStats } from "@/lib/types";
import { chartTooltipStyle, CONDITION_COLORS } from "./chartTheme";

export function ConditionChart({ data }: { data: DashboardStats["condition_distribution"] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="condition"
          innerRadius={55}
          outerRadius={90}
          paddingAngle={3}
          strokeWidth={0}
        >
          {data.map((entry) => (
            <Cell key={entry.condition} fill={CONDITION_COLORS[entry.condition] ?? "var(--accent)"} />
          ))}
        </Pie>
        <Tooltip contentStyle={chartTooltipStyle} formatter={(value, _name, props) => [value, props.payload.condition]} />
      </PieChart>
    </ResponsiveContainer>
  );
}
