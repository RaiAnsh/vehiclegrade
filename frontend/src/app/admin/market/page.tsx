"use client";

import { useEffect, useState } from "react";

import { Card } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatusPill } from "@/components/admin/StatusPill";
import { Table, Tbody, Td, Th, Thead, Tr } from "@/components/ui/Table";
import { useAdminAuth } from "@/hooks/useAdminAuth";
import { getMarketAggregates } from "@/lib/adminApi";
import { MarketAggregateSlice, MarketAggregatesResponse } from "@/lib/adminTypes";
import { flattenGenerations } from "@/lib/catalogHelpers";
import { getCatalog } from "@/lib/api";
import { Catalog } from "@/lib/types";

function currency(value: number) {
  return value.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function SliceTable({ title, dimensionLabel, rows }: { title: string; dimensionLabel: string; rows: MarketAggregateSlice[] }) {
  if (rows.length === 0) return null;
  return (
    <div className="mt-6">
      <h2 className="text-sm font-medium text-muted uppercase tracking-wide">{title}</h2>
      <div className="mt-3">
        <Table>
          <Thead>
            <Tr>
              <Th>{dimensionLabel}</Th>
              <Th>Sample</Th>
              <Th>Median</Th>
              <Th>P25 – P75</Th>
              <Th>Avg mileage</Th>
              <Th>Confidence</Th>
            </Tr>
          </Thead>
          <Tbody>
            {rows.map((row, i) => (
              <Tr key={i}>
                <Td className="font-medium">{row.region ?? row.title_status ?? row.mileage_band}</Td>
                <Td>{row.sample_size}</Td>
                <Td>{currency(row.median_price)}</Td>
                <Td>
                  {currency(row.price_p25)} – {currency(row.price_p75)}
                </Td>
                <Td>{row.avg_mileage_km.toLocaleString()} km</Td>
                <Td>
                  <StatusPill status={row.market_confidence} />
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </div>
    </div>
  );
}

export default function MarketDataPage() {
  const { accessToken } = useAdminAuth();
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [generationId, setGenerationId] = useState<number | null>(null);
  const [data, setData] = useState<MarketAggregatesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCatalog().then(setCatalog).catch(() => setCatalog(null));
  }, []);

  const flatGenerations = flattenGenerations(catalog);

  useEffect(() => {
    if (!accessToken || generationId === null) {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    getMarketAggregates(accessToken, generationId)
      .then((res) => !cancelled && setData(res))
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [accessToken, generationId]);

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Market data</h1>
      <p className="mt-1 text-sm text-muted">
        The Gold-layer <code>MarketAggregate</code> cube for one generation — median/percentile pricing, sliced by
        region, title status, and mileage band. Recomputed automatically on every approval or rollback.
      </p>

      <Card className="mt-6 p-6">
        <label className="mb-1.5 block text-xs font-medium text-muted">Generation</label>
        <Select
          value={generationId ?? ""}
          onChange={(e) => setGenerationId(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">Select a generation…</option>
          {flatGenerations.map((g) => (
            <option key={g.id} value={g.id}>
              {g.label}
            </option>
          ))}
        </Select>
      </Card>

      {error && <Card className="mt-6 p-6 text-sm text-[var(--avoid)]">{error}</Card>}

      {loading && (
        <div className="mt-6 space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      )}

      {!loading && generationId !== null && data && !data.overall && (
        <Card className="mt-6 p-8 text-center text-sm text-muted">{data.disclosure}</Card>
      )}

      {!loading && data?.overall && (
        <>
          <Card className="mt-6 p-6">
            <p className="text-sm text-muted">{data.generation_label}</p>
            <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div>
                <p className="text-xs text-muted">Sample size</p>
                <p className="mt-1 text-2xl font-semibold">{data.overall.sample_size}</p>
              </div>
              <div>
                <p className="text-xs text-muted">Median price</p>
                <p className="mt-1 text-2xl font-semibold">{currency(data.overall.median_price)}</p>
              </div>
              <div>
                <p className="text-xs text-muted">P25 – P75</p>
                <p className="mt-1 text-2xl font-semibold">
                  {currency(data.overall.price_p25)} – {currency(data.overall.price_p75)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted">Confidence</p>
                <p className="mt-2">
                  <StatusPill status={data.overall.market_confidence} />
                </p>
              </div>
            </div>
            <p className="mt-4 text-xs text-muted">{data.disclosure}</p>
          </Card>

          <SliceTable title="By region" dimensionLabel="Region" rows={data.by_region} />
          <SliceTable title="By title status" dimensionLabel="Title status" rows={data.by_title_status} />
          <SliceTable title="By mileage band" dimensionLabel="Mileage band" rows={data.by_mileage_band} />
        </>
      )}
    </div>
  );
}
