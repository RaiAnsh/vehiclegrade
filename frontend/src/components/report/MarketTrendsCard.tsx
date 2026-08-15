"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { getMarketAggregates } from "@/lib/api";
import { downloadCsv, toCsv } from "@/lib/csvExport";
import { MarketAggregatesResponse, MarketAggregateSlice } from "@/lib/types";

const CONFIDENCE_COLOR: Record<string, string> = {
  high: "var(--good)",
  medium: "var(--fair)",
  low: "var(--avoid)",
};

function formatPrice(value: number) {
  return `$${Math.round(value).toLocaleString()}`;
}

function SliceRow({ label, slice }: { label: string; slice: MarketAggregateSlice }) {
  return (
    <tr className="border-t border-white/5">
      <td className="py-2 pr-4 font-medium capitalize">{label}</td>
      <td className="py-2 pr-4">{slice.sample_size}</td>
      <td className="py-2 pr-4">{formatPrice(slice.median_price)}</td>
      <td className="py-2">
        {formatPrice(slice.price_p25)} – {formatPrice(slice.price_p75)}
      </td>
    </tr>
  );
}

// Surfaces the Gold-layer MarketAggregate cube (backend/app/services/
// market_aggregation.py) directly in the public report - previously this
// data only existed in the admin panel. Deliberately separate from
// ComparableListingsCard (which lists individual live listings): this
// shows the precomputed price *distribution* for the whole generation,
// sliced by region/title/mileage, not a sample of specific ads.
export function MarketTrendsCard({ generationId }: { generationId: number }) {
  const [data, setData] = useState<MarketAggregatesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getMarketAggregates(generationId)
      .then((res) => !cancelled && setData(res))
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [generationId]);

  function handleExport() {
    if (!data) return;
    const rows = [
      ...(data.overall ? [{ segment: "overall", ...data.overall }] : []),
      ...data.by_region.map((s) => ({ segment: `region:${s.region}`, ...s })),
      ...data.by_title_status.map((s) => ({ segment: `title_status:${s.title_status}`, ...s })),
      ...data.by_mileage_band.map((s) => ({ segment: `mileage_band:${s.mileage_band}`, ...s })),
    ];
    downloadCsv(`market-trends-${data.generation_label.replace(/\s+/g, "-")}.csv`, toCsv(rows));
  }

  if (loading) {
    return (
      <Card className="p-6">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="mt-4 h-16 w-full" />
      </Card>
    );
  }

  if (error || !data) return null; // non-critical section - fail quietly rather than break the report

  if (!data.overall) {
    return (
      <Card className="p-6">
        <h2 className="text-lg font-medium">Market Trends</h2>
        <p className="mt-3 text-sm text-muted">{data.disclosure}</p>
      </Card>
    );
  }

  const { overall } = data;
  const color = CONFIDENCE_COLOR[overall.market_confidence];

  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium">Market Trends</h2>
        <div className="flex items-center gap-2">
          <span className="rounded-full px-3 py-1 text-xs font-medium" style={{ backgroundColor: `${color}26`, color }}>
            {overall.market_confidence} confidence
          </span>
          <Button variant="secondary" onClick={handleExport} className="!px-3 !py-1.5 text-xs">
            Export CSV
          </Button>
        </div>
      </div>

      <p className="mt-1 text-xs text-muted">{data.generation_label}</p>

      <div className="mt-4 grid gap-4 sm:grid-cols-4">
        <div>
          <p className="text-xs text-muted">Sample size</p>
          <p className="mt-1 text-xl font-semibold">{overall.sample_size}</p>
        </div>
        <div>
          <p className="text-xs text-muted">Median price</p>
          <p className="mt-1 text-xl font-semibold">{formatPrice(overall.median_price)}</p>
        </div>
        <div>
          <p className="text-xs text-muted">25th – 75th percentile</p>
          <p className="mt-1 text-xl font-semibold">
            {formatPrice(overall.price_p25)} – {formatPrice(overall.price_p75)}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted">Avg mileage</p>
          <p className="mt-1 text-xl font-semibold">{overall.avg_mileage_km.toLocaleString()} km</p>
        </div>
      </div>

      {(data.by_region.length > 0 || data.by_title_status.length > 0 || data.by_mileage_band.length > 0) && (
        <div className="mt-5 overflow-x-auto border-t border-white/5 pt-4">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-xs text-muted">
                <th className="pb-2 pr-4 font-medium">Segment</th>
                <th className="pb-2 pr-4 font-medium">Sample</th>
                <th className="pb-2 pr-4 font-medium">Median</th>
                <th className="pb-2 font-medium">25th – 75th</th>
              </tr>
            </thead>
            <tbody>
              {data.by_region.map((slice) => (
                <SliceRow key={`region-${slice.region}`} label={slice.region ?? ""} slice={slice} />
              ))}
              {data.by_title_status.map((slice) => (
                <SliceRow key={`title-${slice.title_status}`} label={slice.title_status ?? ""} slice={slice} />
              ))}
              {data.by_mileage_band.map((slice) => (
                <SliceRow key={`mileage-${slice.mileage_band}`} label={slice.mileage_band ?? ""} slice={slice} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="mt-4 text-xs text-muted">{data.disclosure}</p>
    </Card>
  );
}
