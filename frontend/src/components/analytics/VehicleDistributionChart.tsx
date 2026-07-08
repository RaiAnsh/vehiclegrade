"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { DashboardStats } from "@/lib/types";
import { chartTooltipStyle, BODY_TYPE_COLORS } from "./chartTheme";

export function VehicleDistributionChart({ data }: { data: DashboardStats["vehicle_distribution"] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="body_type"
          innerRadius={55}
          outerRadius={90}
          paddingAngle={3}
          strokeWidth={0}
        >
          {data.map((entry) => (
            <Cell key={entry.body_type} fill={BODY_TYPE_COLORS[entry.body_type] ?? "var(--accent)"} />
          ))}
        </Pie>
        <Tooltip contentStyle={chartTooltipStyle} formatter={(value, _name, props) => [value, props.payload.body_type]} />
      </PieChart>
    </ResponsiveContainer>
  );
}
