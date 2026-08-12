"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import { Tabs } from "@/components/ui/Tabs";
import { useToast } from "@/components/ui/Toast";
import { StatusPill } from "@/components/admin/StatusPill";
import { ObservationCard } from "@/components/admin/ObservationCard";
import { useAdminAuth } from "@/hooks/useAdminAuth";
import { getBatch, listBatchRows, rejectedExportUrl, rollbackBatch } from "@/lib/adminApi";
import { BatchRowsResponse, ImportBatch, ReviewStatus } from "@/lib/adminTypes";
import { getCatalog } from "@/lib/api";
import { Catalog } from "@/lib/types";

interface BatchDetailPageProps {
  params: Promise<{ id: string }>;
}

const STATUS_TABS: { value: ReviewStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "needs_review", label: "Needs review" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
];

export default function BatchDetailPage({ params }: BatchDetailPageProps) {
  const { id } = use(params);
  const batchId = Number(id);
  const { accessToken, hasPermission } = useAdminAuth();
  const { showToast } = useToast();

  const [batch, setBatch] = useState<ImportBatch | null>(null);
  const [rowsData, setRowsData] = useState<BatchRowsResponse | null>(null);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [statusFilter, setStatusFilter] = useState<ReviewStatus | "all">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rollingBack, setRollingBack] = useState(false);
  const [confirmingRollback, setConfirmingRollback] = useState(false);

  const load = useCallback(() => {
    if (!accessToken) return;
    setLoading(true);
    Promise.all([getBatch(accessToken, batchId), listBatchRows(accessToken, batchId)])
      .then(([batchRes, rowsRes]) => {
        setBatch(batchRes);
        setRowsData(rowsRes);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [accessToken, batchId]);

  useEffect(load, [load]);
  useEffect(() => {
    getCatalog().then(setCatalog).catch(() => setCatalog(null));
  }, []);

  async function handleRollback() {
    if (!accessToken || !batch) return;
    setRollingBack(true);
    try {
      const result = await rollbackBatch(accessToken, batch.id);
      showToast(`Rolled back — ${result.observations_rejected} rejected, ${result.listings_archived.length} listing(s) archived`, "success");
      setConfirmingRollback(false);
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Rollback failed", "error");
    } finally {
      setRollingBack(false);
    }
  }

  const filteredRows = rowsData?.rows.filter((row) => statusFilter === "all" || row.observation?.review_status === statusFilter) ?? [];

  return (
    <div>
      <Link href="/admin/batches" className="text-sm text-muted hover:text-foreground">
        &larr; All batches
      </Link>

      {loading && !batch && (
        <div className="mt-4 space-y-4">
          <Skeleton className="h-10 w-1/2" />
          <Skeleton className="h-32 w-full" />
        </div>
      )}

      {error && <Card className="mt-4 p-6 text-sm text-[var(--avoid)]">{error}</Card>}

      {batch && (
        <>
          <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-semibold tracking-tight">Batch #{batch.id}</h1>
                <StatusPill status={batch.status} />
              </div>
              <p className="mt-1 text-sm text-muted">
                {batch.source_type} · {batch.row_count} row(s) · created {new Date(batch.created_at).toLocaleString()}
              </p>
              {batch.notes && <p className="mt-1 text-sm text-muted">Notes: {batch.notes}</p>}
            </div>

            <div className="flex gap-2">
              <a href={rejectedExportUrl(batch.id)} className="inline-flex">
                <Button variant="secondary">Export rejected (CSV)</Button>
              </a>
              {hasPermission("rollback") && batch.status !== "rolled_back" && (
                <Button variant="ghost" onClick={() => setConfirmingRollback(true)} disabled={rollingBack}>
                  {rollingBack ? "Rolling back…" : "Roll back batch"}
                </Button>
              )}
            </div>
          </div>

          <div className="mt-6">
            <Tabs
              tabs={STATUS_TABS.map((tab) => ({
                value: tab.value,
                label: tab.label,
                count: tab.value === "all" ? batch.row_count : batch.observation_counts[tab.value as ReviewStatus],
              }))}
              active={statusFilter}
              onChange={(v) => setStatusFilter(v as ReviewStatus | "all")}
            />
          </div>

          <div className="mt-6 space-y-4">
            {filteredRows.length === 0 && (
              <Card className="p-8 text-center text-sm text-muted">No rows match this filter.</Card>
            )}
            {filteredRows.map((row) => (
              <ObservationCard key={row.id} row={row} catalog={catalog} onChanged={load} />
            ))}
          </div>

          <Modal open={confirmingRollback} onClose={() => setConfirmingRollback(false)}>
            <h2 className="text-lg font-semibold">Roll back batch #{batch.id}?</h2>
            <p className="mt-2 text-sm text-muted">
              Any approved listings from this batch will be archived (not deleted), and every remaining row will be
              rejected. This is terminal — the batch cannot be reprocessed afterward.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setConfirmingRollback(false)} disabled={rollingBack}>
                Cancel
              </Button>
              <Button variant="secondary" onClick={handleRollback} disabled={rollingBack}>
                {rollingBack ? "Rolling back…" : "Roll back batch"}
              </Button>
            </div>
          </Modal>
        </>
      )}
    </div>
  );
}
