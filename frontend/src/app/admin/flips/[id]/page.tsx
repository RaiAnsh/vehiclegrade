"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";
import { useAdminAuth } from "@/hooks/useAdminAuth";
import { addFlipExpense, deleteFlip, deleteFlipExpense, getFlip, sellFlip } from "@/lib/adminApi";
import { ExpenseCategory, Flip } from "@/lib/adminTypes";

const CATEGORIES: ExpenseCategory[] = ["insurance", "fuel", "maintenance", "repair", "inspection_prep", "safety", "other"];
const money = (n: number | null | undefined) =>
  n === null || n === undefined ? "-" : `${n < 0 ? "-" : ""}$${Math.abs(Math.round(n)).toLocaleString()}`;
const netClass = (n: number | null | undefined) => (n === null || n === undefined ? "" : n >= 0 ? "text-green-400" : "text-red-400");

export default function FlipDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const flipId = Number(id);
  const router = useRouter();
  const { accessToken, hasPermission } = useAdminAuth();
  const { showToast } = useToast();

  const [flip, setFlip] = useState<Flip | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState<ExpenseCategory>("fuel");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [selling, setSelling] = useState(false);
  const [sale, setSale] = useState({ price: "", fees: "", date: "", mileage: "" });
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const load = useCallback(() => {
    if (!accessToken) return;
    getFlip(accessToken, flipId).then(setFlip).catch((e) => setError(e.message));
  }, [accessToken, flipId]);
  useEffect(load, [load]);

  const canEdit = hasPermission("ingest");

  async function run(action: () => Promise<Flip>, success: string) {
    try {
      setFlip(await action());
      showToast(success, "success");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Something went wrong", "error");
    }
  }

  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!flip) return <Skeleton className="h-64 w-full" />;

  const s = flip.summary;
  const cmp = s.comparison;

  return (
    <div>
      <Link href="/admin/flips" className="text-xs text-muted hover:text-foreground">&larr; Flip ledger</Link>
      <div className="mt-2 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {flip.year} {flip.make} {flip.model}{flip.trim ? ` ${flip.trim}` : ""}
          </h1>
          <p className="mt-1 text-sm text-muted">
            {flip.status === "sold" ? "Sold" : "Holding"} &middot; bought {flip.purchase_date} at{" "}
            {flip.mileage_at_purchase.toLocaleString()} km &middot; {s.months_held} months
          </p>
        </div>
        {canEdit && (
          <div className="flex gap-2">
            {flip.status === "holding" && <Button onClick={() => setSelling(true)}>Mark sold</Button>}
            <Button variant="secondary" onClick={() => setConfirmingDelete(true)}>Delete</Button>
          </div>
        )}
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-4">
        <Card className="p-4"><p className="text-xs text-muted">Acquisition</p><p className="mt-1 text-xl font-semibold">{money(s.acquisition_cost)}</p>
          <p className="text-xs text-muted">{money(flip.purchase_price)} + {money(flip.purchase_tax)} tax + {money(flip.purchase_fees)} fees</p></Card>
        <Card className="p-4"><p className="text-xs text-muted">Running costs</p><p className="mt-1 text-xl font-semibold">{money(s.expenses_total)}</p>
          <p className="text-xs text-muted">{s.monthly_burn === null ? "" : `${money(s.monthly_burn)}/month`}</p></Card>
        <Card className="p-4"><p className="text-xs text-muted">Total invested</p><p className="mt-1 text-xl font-semibold">{money(s.total_invested)}</p></Card>
        {flip.status === "sold" ? (
          <Card className="p-4"><p className="text-xs text-muted">Actual net</p>
            <p className={`mt-1 text-xl font-semibold ${netClass(s.actual_net)}`}>{money(s.actual_net)}</p>
            <p className="text-xs text-muted">sold {money(flip.sale_price)} on {flip.sale_date}</p></Card>
        ) : (
          <Card className="p-4"><p className="text-xs text-muted">Break-even sale price now</p>
            <p className="mt-1 text-xl font-semibold">{money(s.break_even_sale_price)}</p>
            <p className="text-xs text-muted">includes typical selling costs</p></Card>
        )}
      </div>

      {cmp && (
        <Card className="mt-6 p-6">
          <h2 className="text-lg font-medium">Predicted vs actual</h2>
          <table className="mt-3 w-full text-sm">
            <thead className="text-left text-xs text-muted">
              <tr><th className="py-1">Line</th><th>Predicted{flip.status !== "sold" ? " (to date)" : ""}</th><th>Actual</th></tr>
            </thead>
            <tbody>
              {cmp.lines.map((row) => (
                <tr key={row.line} className="border-t border-white/10">
                  <td className="py-1.5 capitalize">{row.line}</td><td>{money(row.predicted)}</td><td>{money(row.actual)}</td>
                </tr>
              ))}
              <tr className="border-t border-white/10">
                <td className="py-1.5">Sale price</td><td>{money(cmp.predicted_sale_price)}</td><td>{money(flip.sale_price)}</td>
              </tr>
              <tr className="border-t border-white/10 font-medium">
                <td className="py-1.5">Net result</td><td>{money(cmp.predicted_net)}</td>
                <td className={netClass(cmp.actual_net)}>{money(cmp.actual_net)}</td>
              </tr>
            </tbody>
          </table>
          {cmp.net_error !== undefined && (
            <p className="mt-3 text-sm text-muted">
              This flip finished <span className={netClass(cmp.net_error)}>{money(Math.abs(cmp.net_error))} {cmp.net_error >= 0 ? "better" : "worse"}</span> than predicted
              {cmp.months_error !== undefined && `, ${Math.abs(cmp.months_error)} months ${cmp.months_error > 0 ? "longer" : "shorter"} than planned`}.
            </p>
          )}
        </Card>
      )}

      <Card className="mt-6 p-6">
        <h2 className="text-lg font-medium">Expenses</h2>
        {canEdit && flip.status === "holding" && (
          <div className="mt-3 flex flex-wrap gap-2">
            <Select value={category} onChange={(e) => setCategory(e.target.value as ExpenseCategory)} className="w-44">
              {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace("_", " ")}</option>)}
            </Select>
            <Input type="number" placeholder="Amount ($)" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-36" />
            <Input placeholder="Note (optional)" value={note} onChange={(e) => setNote(e.target.value)} className="w-56" />
            <Button
              disabled={!amount || Number(amount) <= 0}
              onClick={async () => {
                if (!accessToken) return;
                await run(() => addFlipExpense(accessToken, flipId, { category, amount: Number(amount), note: note || undefined }), "Expense added");
                setAmount(""); setNote("");
              }}
            >
              Add
            </Button>
          </div>
        )}
        <ul className="mt-4 divide-y divide-white/10 text-sm">
          {(flip.expenses ?? []).length === 0 && <li className="py-2 text-muted">No expenses yet.</li>}
          {(flip.expenses ?? []).map((e) => (
            <li key={e.id} className="flex items-center justify-between gap-3 py-2">
              <span><span className="capitalize">{e.category.replace("_", " ")}</span>
                <span className="text-muted"> &middot; {e.date}{e.note ? ` · ${e.note}` : ""}</span></span>
              <span className="flex items-center gap-3">
                {money(e.amount)}
                {canEdit && (
                  <button className="text-xs text-muted hover:text-red-400"
                    onClick={() => accessToken && run(() => deleteFlipExpense(accessToken, flipId, e.id), "Expense removed")}>
                    remove
                  </button>
                )}
              </span>
            </li>
          ))}
        </ul>
      </Card>

      <Modal open={selling} onClose={() => setSelling(false)}>
        <Card className="w-full max-w-md p-6">
          <h2 className="text-lg font-semibold">Mark as sold</h2>
          <div className="mt-4 grid gap-3">
            <Input type="number" placeholder="Sale price ($)" value={sale.price} onChange={(e) => setSale({ ...sale, price: e.target.value })} />
            <Input type="number" placeholder="Selling costs paid by you ($) e.g. safety, detail" value={sale.fees} onChange={(e) => setSale({ ...sale, fees: e.target.value })} />
            <div>
              <label className="mb-1 block text-xs text-muted">Sale date (blank = today)</label>
              <Input type="date" value={sale.date} onChange={(e) => setSale({ ...sale, date: e.target.value })} />
            </div>
            <Input type="number" placeholder="Mileage at sale (optional)" value={sale.mileage} onChange={(e) => setSale({ ...sale, mileage: e.target.value })} />
          </div>
          <div className="mt-5 flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setSelling(false)}>Cancel</Button>
            <Button
              disabled={!sale.price}
              onClick={async () => {
                if (!accessToken) return;
                await run(() => sellFlip(accessToken, flipId, {
                  sale_price: Number(sale.price), sale_fees: sale.fees ? Number(sale.fees) : undefined,
                  sale_date: sale.date || undefined, mileage_at_sale: sale.mileage ? Number(sale.mileage) : undefined,
                }), "Marked sold");
                setSelling(false);
              }}
            >
              Save sale
            </Button>
          </div>
        </Card>
      </Modal>

      <Modal open={confirmingDelete} onClose={() => setConfirmingDelete(false)}>
        <Card className="w-full max-w-md p-6">
          <h2 className="text-lg font-semibold">Delete this flip?</h2>
          <p className="mt-2 text-sm text-muted">This permanently removes it and all its expenses from your ledger. It can&apos;t be undone.</p>
          <div className="mt-5 flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setConfirmingDelete(false)}>Cancel</Button>
            <Button
              onClick={async () => {
                if (!accessToken) return;
                try {
                  await deleteFlip(accessToken, flipId);
                  router.push("/admin/flips");
                } catch (err) {
                  showToast(err instanceof Error ? err.message : "Could not delete", "error");
                }
              }}
            >
              Delete
            </Button>
          </div>
        </Card>
      </Modal>
    </div>
  );
}
