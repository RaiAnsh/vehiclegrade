"use client";

import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";

import { DashboardStats } from "@/lib/types";
import { chartTooltipStyle, chartAxisStyle } from "./chartTheme";

export function MileageVsPriceScatter({ data }: { data: DashboardStats["mileage_vs_price"] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
        <XAxis
          dataKey="mileage_km"
          type="number"
          name="Mileage"
          unit=" km"
          {...chartAxisStyle}
          tickFormatter={(value) => `${Math.round(value / 1000)}k`}
        />
        <YAxis
          dataKey="price"
          type="number"
          name="Price"
          {...chartAxisStyle}
          tickFormatter={(value) => `$${Math.round(value / 1000)}k`}
        />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          contentStyle={chartTooltipStyle}
          formatter={(value, name) => {
            const num = Number(value);
            return name === "Mileage" ? [`${num.toLocaleString()} km`, name] : [`$${num.toLocaleString()}`, name];
          }}
        />
        <Scatter data={data} fill="var(--accent)" fillOpacity={0.7} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
