"use client";

import { ChartCard } from "@/components/analytics/ChartCard";
import { DemoDataNotice } from "@/components/layout/DemoDataNotice";
import { PriceByMakeChart } from "@/components/analytics/PriceByMakeChart";
import { PriceByModelChart } from "@/components/analytics/PriceByModelChart";
import { MileageVsPriceScatter } from "@/components/analytics/MileageVsPriceScatter";
import { VehicleDistributionChart } from "@/components/analytics/VehicleDistributionChart";
import { ScoreDistributionChart } from "@/components/analytics/ScoreDistributionChart";
import { TopDealsToday } from "@/components/analytics/TopDealsToday";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { useStats } from "@/hooks/useStats";

export default function AnalyticsPage() {
  const { stats, loading } = useStats();

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Analytics</h1>
      <p className="mt-2 text-muted">Aggregate view across the sample listings in VehicleGrade&apos;s demo dataset.</p>
      <DemoDataNotice />

      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        <ChartCard title="Average price by make" loading={loading} index={0}>
          {stats && <PriceByMakeChart data={stats.price_by_make} />}
        </ChartCard>
        <ChartCard title="Average price by model" loading={loading} index={1}>
          {stats && <PriceByModelChart data={stats.price_by_model} />}
        </ChartCard>
        <ChartCard title="Mileage vs. price" loading={loading} index={2}>
          {stats && <MileageVsPriceScatter data={stats.mileage_vs_price} />}
        </ChartCard>
        <ChartCard title="Vehicle distribution by body type" loading={loading} index={3}>
          {stats && <VehicleDistributionChart data={stats.vehicle_distribution} />}
        </ChartCard>
        <ChartCard title="VehicleGrade score distribution" loading={loading} index={4}>
          {stats && <ScoreDistributionChart data={stats.score_distribution} />}
        </ChartCard>
      </div>

      <div className="mt-8">
        <p className="mb-4 text-sm font-medium">Top deals today</p>
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Card className="p-5">
              <Skeleton className="h-40 w-full" />
            </Card>
            <Card className="p-5">
              <Skeleton className="h-40 w-full" />
            </Card>
            <Card className="p-5">
              <Skeleton className="h-40 w-full" />
            </Card>
          </div>
        ) : (
          stats && <TopDealsToday data={stats.top_deals_today} />
        )}
      </div>
    </div>
  );
}
