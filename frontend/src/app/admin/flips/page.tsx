"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { Table, Tbody, Td, Th, Thead, Tr } from "@/components/ui/Table";
import { useToast } from "@/components/ui/Toast";
import { RequirePermission } from "@/components/admin/RequirePermission";
import { useAdminAuth } from "@/hooks/useAdminAuth";
import { createFlip, listFlips } from "@/lib/adminApi";
import { FlipListResponse } from "@/lib/adminTypes";
import { getCatalog } from "@/lib/api";
import { Catalog } from "@/lib/types";

const money = (n: number | null | undefined) =>
  n === null || n === undefined ? "-" : `${n < 0 ? "-" : ""}$${Math.abs(Math.round(n)).toLocaleString()}`;

const netClass = (n: number | null | undefined) => (n === null || n === undefined ? "" : n >= 0 ? "text-green-400" : "text-red-400");

function Stat({ label, value, className = "" }: { label: string; value: string; className?: string }) {
  return (
    <Card className="p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${className}`}>{value}</p>
    </Card>
  );
}

interface Draft {
  make?: string;
  model?: string;
  year?: string;
  trim?: string;
  mileage_km?: string;
  purchase_price?: string;
  purchase_date?: string;
  planned_months?: string;
  purchase_fees?: string;
  insurance_annual?: string;
}

function LogFlipModal({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: () => void }) {
  const { accessToken } = useAdminAuth();
  const { showToast } = useToast();
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [draft, setDraft] = useState<Draft>({ planned_months: "3" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getCatalog().then(setCatalog).catch(() => setCatalog(null));
  }, []);

  const set = (key: keyof Draft, value: string) => setDraft((d) => ({ ...d, [key]: value }));
  const models = catalog?.makes.find((m) => m.name === draft.make)?.models ?? [];
  const year = Number(draft.year);
  const generation = models
    .find((m) => m.name === draft.model)
    ?.generations.find((g) => year >= g.start_year && year <= g.end_year);
  const can = draft.make && draft.model && draft.year && draft.mileage_km && draft.purchase_price;

  async function submit() {
    if (!accessToken || !can) return;
    setSaving(true);
    try {
      const num = (v?: string) => (v ? Number(v) : undefined);
      await createFlip(accessToken, {
        make: draft.make!, model: draft.model!, year, trim: draft.trim || undefined,
        mileage_km: Number(draft.mileage_km), purchase_price: Number(draft.purchase_price),
        purchase_date: draft.purchase_date || undefined, planned_months: num(draft.planned_months),
        purchase_fees: num(draft.purchase_fees), insurance_annual: num(draft.insurance_annual),
      });
      showToast("Flip logged", "success");
      setDraft({ planned_months: "3" });
      onCreated();
      onClose();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Could not log flip", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose}>
      <Card className="w-full max-w-lg p-6">
        <h2 className="text-lg font-semibold">Log a purchase</h2>
        <p className="mt-1 text-xs text-muted">
          The Flip Calculator&apos;s prediction is saved now, so you can compare it with what really happens.
          Ontario RST defaults to 13% of the price.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <Select value={draft.make ?? ""} onChange={(e) => setDraft((d) => ({ ...d, make: e.target.value, model: undefined, trim: undefined }))}>
            <option value="">Make</option>
            {catalog?.makes.map((m) => <option key={m.id} value={m.name}>{m.name}</option>)}
          </Select>
          <Select value={draft.model ?? ""} disabled={!draft.make} onChange={(e) => setDraft((d) => ({ ...d, model: e.target.value, trim: undefined }))}>
            <option value="">Model</option>
            {models.map((m) => <option key={m.id} value={m.name}>{m.name}</option>)}
          </Select>
          <Input type="number" placeholder="Year" value={draft.year ?? ""} onChange={(e) => set("year", e.target.value)} />
          <Select value={draft.trim ?? ""} disabled={!generation} onChange={(e) => set("trim", e.target.value)}>
            <option value="">Any trim</option>
            {generation?.trims.map((t) => <option key={t.id} value={t.name}>{t.name}</option>)}
          </Select>
          <Input type="number" placeholder="Mileage (km)" value={draft.mileage_km ?? ""} onChange={(e) => set("mileage_km", e.target.value)} />
          <Input type="number" placeholder="Purchase price ($)" value={draft.purchase_price ?? ""} onChange={(e) => set("purchase_price", e.target.value)} />
          <div>
            <label className="mb-1 block text-xs text-muted">Purchase date</label>
            <Input type="date" value={draft.purchase_date ?? ""} onChange={(e) => set("purchase_date", e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted">Planned months</label>
            <Input type="number" step="0.5" value={draft.planned_months ?? ""} onChange={(e) => set("planned_months", e.target.value)} />
          </div>
          <Input type="number" placeholder="UVIP / transfer / report fees ($)" value={draft.purchase_fees ?? ""} onChange={(e) => set("purchase_fees", e.target.value)} />
          <Input type="number" placeholder="Insurance quote per year ($)" value={draft.insurance_annual ?? ""} onChange={(e) => set("insurance_annual", e.target.value)} />
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={submit} disabled={!can || saving}>{saving ? "Saving..." : "Log flip"}</Button>
        </div>
      </Card>
    </Modal>
  );
}

export default function FlipLedgerPage() {
  const { accessToken, hasPermission } = useAdminAuth();
  const [data, setData] = useState<FlipListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [logging, setLogging] = useState(false);

  const load = useCallback(() => {
    if (!accessToken) return;
    listFlips(accessToken).then(setData).catch((e) => setError(e.message));
  }, [accessToken]);

  useEffect(load, [load]);

  const p = data?.portfolio;

  return (
    <RequirePermission permission="view">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Flip ledger</h1>
          <p className="mt-1 text-sm text-muted">Real money in and out, compared against the calculator&apos;s prediction.</p>
        </div>
        {hasPermission("ingest") && <Button onClick={() => setLogging(true)}>Log a purchase</Button>}
      </div>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
      {!data && !error && <Skeleton className="mt-6 h-40 w-full" />}

      {data && p && (
        <>
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Total net (sold)" value={money(p.total_net)} className={netClass(p.total_net)} />
            <Stat label="Win rate" value={p.win_rate_pct === null ? "-" : `${p.win_rate_pct}%`} />
            <Stat label="Capital tied up" value={money(p.capital_in_holding)} />
            <Stat
              label="Calculator accuracy (avg error)"
              value={p.prediction?.avg_net_error == null ? "needs a sold flip" : money(p.prediction.avg_net_error)}
              className={netClass(p.prediction?.avg_net_error)}
            />
          </div>
          {p.prediction && <p className="mt-2 text-xs text-muted">{p.prediction.note}</p>}

          <div className="mt-6">
            {data.flips.length === 0 ? (
              <Card className="p-8 text-center text-sm text-muted">No flips logged yet.</Card>
            ) : (
              <Table>
                <Thead>
                  <Tr>
                    <Th>Car</Th><Th>Status</Th><Th>Bought</Th><Th>Invested</Th><Th>Months</Th><Th>Net</Th><Th>Predicted</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {data.flips.map((f) => (
                    <Tr key={f.id}>
                      <Td className="font-medium">
                        <Link href={`/admin/flips/${f.id}`} className="hover:underline">
                          {f.year} {f.make} {f.model}{f.trim ? ` ${f.trim}` : ""}
                        </Link>
                      </Td>
                      <Td>{f.status}</Td>
                      <Td>{f.purchase_date}</Td>
                      <Td>{money(f.summary.total_invested)}</Td>
                      <Td>{f.summary.months_held}</Td>
                      <Td className={netClass(f.summary.actual_net)}>{money(f.summary.actual_net)}</Td>
                      <Td>{money(f.summary.comparison?.predicted_net)}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            )}
          </div>
        </>
      )}

      <LogFlipModal open={logging} onClose={() => setLogging(false)} onCreated={load} />
    </RequirePermission>
  );
}
