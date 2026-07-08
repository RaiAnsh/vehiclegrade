"use client";

import { useStats } from "@/hooks/useStats";
import { StatCard, StatCardSkeleton } from "./StatCard";

export function StatsGrid() {
  const { stats, loading } = useStats();

  if (loading || !stats) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  const cards = [
    { label: "Listings Analyzed", value: stats.listings_analyzed.toLocaleString() },
    { label: "Average Market Value", value: `$${stats.average_market_value.toLocaleString()}` },
    { label: "Average VehicleGrade Score", value: stats.average_vehiclegrade_score.toFixed(1) },
    { label: "Average Mileage", value: `${stats.average_mileage_km.toLocaleString()} km` },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card, index) => (
        <StatCard key={card.label} label={card.label} value={card.value} index={index} />
      ))}
    </div>
  );
}
