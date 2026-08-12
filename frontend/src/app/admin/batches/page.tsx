"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { Table, Tbody, Td, Th, Thead, Tr } from "@/components/ui/Table";
import { StatusPill } from "@/components/admin/StatusPill";
import { useAdminAuth } from "@/hooks/useAdminAuth";
import { listBatches } from "@/lib/adminApi";
import { BatchListResponse } from "@/lib/adminTypes";

const SOURCE_LABELS: Record<string, string> = {
  paste_single: "Paste (single)",
  paste_multi: "Paste (multi)",
  csv_upload: "CSV upload",
};

export default function BatchesListPage() {
  const { accessToken } = useAdminAuth();
  const [page, setPage] = useState(1);
  const [data, setData] = useState<BatchListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    setLoading(true);
    listBatches(accessToken, page)
      .then((res) => !cancelled && setData(res))
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [accessToken, page]);

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Import batches</h1>
      <p className="mt-1 text-sm text-muted">Every paste/CSV import, most recent first.</p>

      {error && <Card className="mt-6 p-6 text-sm text-[var(--avoid)]">{error}</Card>}

      {loading && !data && (
        <div className="mt-6 space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      )}

      {data && data.batches.length === 0 && (
        <Card className="mt-6 p-8 text-center text-sm text-muted">No import batches yet.</Card>
      )}

      {data && data.batches.length > 0 && (
        <div className="mt-6">
          <Table>
            <Thead>
              <Tr>
                <Th>ID</Th>
                <Th>Source</Th>
                <Th>Status</Th>
                <Th>Rows</Th>
                <Th>Pending</Th>
                <Th>Needs review</Th>
                <Th>Approved</Th>
                <Th>Rejected</Th>
                <Th>Created</Th>
              </Tr>
            </Thead>
            <Tbody>
              {data.batches.map((batch) => (
                <Tr key={batch.id}>
                  <Td>
                    <Link href={`/admin/batches/${batch.id}`} className="font-medium text-[var(--good)] hover:underline">
                      #{batch.id}
                    </Link>
                  </Td>
                  <Td>{SOURCE_LABELS[batch.source_type] ?? batch.source_type}</Td>
                  <Td>
                    <StatusPill status={batch.status} />
                  </Td>
                  <Td>{batch.row_count}</Td>
                  <Td>{batch.observation_counts.pending}</Td>
                  <Td>{batch.observation_counts.needs_review}</Td>
                  <Td>{batch.observation_counts.approved}</Td>
                  <Td>{batch.observation_counts.rejected}</Td>
                  <Td className="text-muted">{new Date(batch.created_at).toLocaleString()}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>

          {data.total_pages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm text-muted">
              <span>
                Page {data.page} of {data.total_pages} ({data.total} total)
              </span>
              <div className="flex gap-2">
                <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  Previous
                </Button>
                <Button variant="secondary" disabled={page >= data.total_pages} onClick={() => setPage((p) => p + 1)}>
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
