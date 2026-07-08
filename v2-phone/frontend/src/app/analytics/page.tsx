"use client";

import { ChartCard } from "@/components/analytics/ChartCard";
import { PriceByModelChart } from "@/components/analytics/PriceByModelChart";
import { BatteryHealthChart } from "@/components/analytics/BatteryHealthChart";
import { LocationChart } from "@/components/analytics/LocationChart";
import { ConditionChart } from "@/components/analytics/ConditionChart";
import { StorageChart } from "@/components/analytics/StorageChart";
import { ScoreDistributionChart } from "@/components/analytics/ScoreDistributionChart";
import { useStats } from "@/hooks/useStats";

export default function AnalyticsPage() {
  const { stats, loading } = useStats();

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Analytics</h1>
      <p className="mt-2 text-muted">A market-wide view across every listing FlipIQ has analyzed.</p>

      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        <ChartCard title="Average price by model" loading={loading} index={0}>
          {stats && <PriceByModelChart data={stats.price_by_model} />}
        </ChartCard>
        <ChartCard title="Average battery health by model" loading={loading} index={1}>
          {stats && <BatteryHealthChart data={stats.battery_by_model} />}
        </ChartCard>
        <ChartCard title="Listings by location" loading={loading} index={2}>
          {stats && <LocationChart data={stats.listings_by_location} />}
        </ChartCard>
        <ChartCard title="Condition distribution" loading={loading} index={3}>
          {stats && <ConditionChart data={stats.condition_distribution} />}
        </ChartCard>
        <ChartCard title="Storage distribution" loading={loading} index={4}>
          {stats && <StorageChart data={stats.storage_distribution} />}
        </ChartCard>
        <ChartCard title="FlipIQ score distribution" loading={loading} index={5}>
          {stats && <ScoreDistributionChart data={stats.score_distribution} />}
        </ChartCard>
      </div>
    </div>
  );
}
