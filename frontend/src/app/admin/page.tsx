"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatCard, StatCardSkeleton } from "@/components/dashboard/StatCard";
import { useAdminAuth } from "@/hooks/useAdminAuth";
import { useToast } from "@/components/ui/Toast";
import { getAnalyticsOverview, triggerRecompute } from "@/lib/adminApi";
import { AnalyticsOverview } from "@/lib/adminTypes";

export default function AdminOverviewPage() {
  const { accessToken, hasPermission } = useAdminAuth();
  const { showToast } = useToast();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recomputing, setRecomputing] = useState(false);

  function load() {
    if (!accessToken) return;
    setLoading(true);
    getAnalyticsOverview(accessToken)
      .then((data) => {
        setOverview(data);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [accessToken]);

  async function handleRecompute() {
    if (!accessToken) return;
    setRecomputing(true);
    try {
      const result = await triggerRecompute(accessToken);
      showToast(`Recomputed ${result.generations_recomputed} generation(s), ${result.total_rows_written} rows written`, "success");
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Recompute failed", "error");
    } finally {
      setRecomputing(false);
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Pipeline overview</h1>
          <p className="mt-1 text-sm text-muted">Bronze → Silver → Gold record counts and funnel health.</p>
        </div>
        <div className="flex gap-3">
          {hasPermission("rollback") && (
            <Button variant="secondary" onClick={handleRecompute} disabled={recomputing}>
              {recomputing ? "Recomputing…" : "Recompute market aggregates"}
            </Button>
          )}
          {hasPermission("ingest") && (
            <Link href="/admin/import">
              <Button>New import</Button>
            </Link>
          )}
        </div>
      </div>

      {error && (
        <Card className="mt-6 p-6 text-sm text-[var(--avoid)]">Couldn&apos;t load pipeline stats: {error}</Card>
      )}

      {loading && !overview && (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
      )}

      {overview && (
        <>
          <section className="mt-6">
            <h2 className="text-sm font-medium text-muted uppercase tracking-wide">Bronze — raw submissions</h2>
            <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <StatCard label="Import batches" value={String(overview.bronze.import_batches)} />
              <StatCard label="Raw submissions" value={String(overview.bronze.raw_submissions)} />
            </div>
          </section>

          <section className="mt-8">
            <h2 className="text-sm font-medium text-muted uppercase tracking-wide">Silver — reviewed observations</h2>
            <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Total observations" value={String(overview.silver.total_observations)} />
              <StatCard label="Pending review" value={String(overview.silver.by_review_status.pending ?? 0)} />
              <StatCard label="Needs review" value={String(overview.silver.by_review_status.needs_review ?? 0)} />
              <StatCard
                label="Duplicate rate"
                value={overview.silver.duplicate_rate_pct !== null ? `${overview.silver.duplicate_rate_pct}%` : "—"}
              />
            </div>
          </section>

          <section className="mt-8">
            <h2 className="text-sm font-medium text-muted uppercase tracking-wide">Gold — materialized listings</h2>
            <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Total listings" value={String(overview.gold.total_listings)} />
              <StatCard label="Admin-ingested" value={String(overview.gold.admin_ingested_listings)} />
              <StatCard label="Archived" value={String(overview.gold.archived_listings)} />
              <StatCard label="Generations with market data" value={String(overview.gold.generations_with_market_aggregates)} />
            </div>
          </section>

          <section className="mt-8">
            <h2 className="text-sm font-medium text-muted uppercase tracking-wide">Review funnel</h2>
            <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <StatCard label="Approved" value={String(overview.funnel.approved)} />
              <StatCard label="Rejected" value={String(overview.funnel.rejected)} />
              <StatCard
                label="Approval rate"
                value={overview.funnel.approval_rate_pct !== null ? `${overview.funnel.approval_rate_pct}%` : "—"}
              />
            </div>
          </section>
        </>
      )}
    </div>
  );
}
