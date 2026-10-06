"use client";

import { useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { FlipLedger } from "@/hooks/useFlipLedger";
import { ExpenseCategory, LocalFlip } from "@/lib/types";

const CATEGORIES: ExpenseCategory[] = ["insurance", "fuel", "maintenance", "repair", "inspection_prep", "safety", "other"];
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

function FlipCard({ flip, ledger }: { flip: LocalFlip; ledger: FlipLedger }) {
  const entry = ledger.summary?.flips[flip.id];
  const s = entry?.summary;
  const cmp = s?.comparison;
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<ExpenseCategory>("fuel");
  const [amount, setAmount] = useState("");
  const [selling, setSelling] = useState(false);
  const [salePrice, setSalePrice] = useState("");
  const [saleFees, setSaleFees] = useState("");
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  return (
    <Card className="p-5">
      <button className="flex w-full items-start justify-between gap-4 text-left" onClick={() => setOpen(!open)}>
        <div>
          <p className="font-medium">
            {flip.year} {flip.make} {flip.model}{flip.trim ? ` ${flip.trim}` : ""}
          </p>
          <p className="mt-0.5 text-xs text-muted">
            {flip.status === "sold" ? "Sold" : "Holding"} &middot; bought {flip.purchase_date}
            {entry?.level ? ` · Level ${entry.level}` : ""}
          </p>
        </div>
        <div className="text-right">
          {flip.status === "sold" ? (
            <p className={`text-lg font-semibold ${netClass(s?.actual_net)}`}>{money(s?.actual_net)}</p>
          ) : (
            <p className="text-sm text-muted">{money(s?.total_invested)} in</p>
          )}
          <p className="text-xs text-muted">predicted {money(cmp?.predicted_net)}</p>
        </div>
      </button>

      {open && s && (
        <div className="mt-5 space-y-5 border-t border-white/10 pt-5 text-sm">
          <div className="grid gap-3 sm:grid-cols-3">
            <div><p className="text-xs text-muted">Acquisition</p><p className="font-medium">{money(s.acquisition_cost)}</p>
              <p className="text-xs text-muted">{money(flip.purchase_price)} + {money(flip.purchase_tax)} tax + {money(flip.purchase_fees)} fees</p></div>
            <div><p className="text-xs text-muted">Running costs</p><p className="font-medium">{money(s.expenses_total)}</p>
              {s.monthly_burn !== null && <p className="text-xs text-muted">{money(s.monthly_burn)}/month</p>}</div>
            {flip.status === "holding" ? (
              <div><p className="text-xs text-muted">Break-even sale price now</p><p className="font-medium">{money(s.break_even_sale_price)}</p></div>
            ) : (
              <div><p className="text-xs text-muted">Sold for</p><p className="font-medium">{money(flip.sale_price)}</p></div>
            )}
          </div>

          {cmp && (
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-muted">
                <tr><th className="py-1">Line</th><th>Predicted{flip.status !== "sold" ? " (to date)" : ""}</th><th>Actual</th></tr>
              </thead>
              <tbody>
                {cmp.lines.map((row) => (
                  <tr key={row.line} className="border-t border-white/10">
                    <td className="py-1.5 capitalize">{row.line}</td><td>{money(row.predicted)}</td><td>{money(row.actual)}</td>
                  </tr>
                ))}
                {flip.status === "sold" && (
                  <tr className="border-t border-white/10 font-medium">
                    <td className="py-1.5">Net result</td><td>{money(cmp.predicted_net)}</td>
                    <td className={netClass(cmp.actual_net)}>{money(cmp.actual_net)}</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
          {cmp?.net_error !== undefined && (
            <p className="text-muted">
              Finished <span className={netClass(cmp.net_error)}>{money(Math.abs(cmp.net_error))} {cmp.net_error >= 0 ? "better" : "worse"}</span> than predicted.
            </p>
          )}

          <div>
            <p className="mb-2 text-xs uppercase tracking-wide text-muted">Expenses</p>
            {flip.status === "holding" && (
              <div className="mb-3 flex flex-wrap gap-2">
                <Select value={category} onChange={(e) => setCategory(e.target.value as ExpenseCategory)} className="w-40">
                  {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace("_", " ")}</option>)}
                </Select>
                <Input type="number" placeholder="Amount ($)" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-32" />
                <Button variant="secondary" disabled={!amount || Number(amount) <= 0}
                  onClick={() => { ledger.addExpense(flip.id, category, Number(amount)); setAmount(""); }}>
                  Add
                </Button>
              </div>
            )}
            <ul className="divide-y divide-white/10">
              {flip.expenses.length === 0 && <li className="py-1.5 text-muted">None yet.</li>}
              {flip.expenses.map((e) => (
                <li key={e.id} className="flex items-center justify-between py-1.5">
                  <span className="capitalize">{e.category.replace("_", " ")} <span className="text-muted">&middot; {e.date}</span></span>
                  <span className="flex gap-3">{money(e.amount)}
                    <button className="text-xs text-muted hover:text-red-400" onClick={() => ledger.removeExpense(flip.id, e.id)}>remove</button>
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex gap-2">
            {flip.status === "holding" && <Button onClick={() => setSelling(true)}>Mark sold</Button>}
            <Button variant="secondary" onClick={() => setConfirmingDelete(true)}>Delete</Button>
          </div>
        </div>
      )}

      <Modal open={selling} onClose={() => setSelling(false)}>
        <Card className="w-full max-w-md p-6">
          <h2 className="text-lg font-semibold">Mark as sold</h2>
          <div className="mt-4 grid gap-3">
            <Input type="number" placeholder="Sale price ($)" value={salePrice} onChange={(e) => setSalePrice(e.target.value)} />
            <Input type="number" placeholder="Selling costs you paid ($) e.g. safety, detail" value={saleFees} onChange={(e) => setSaleFees(e.target.value)} />
          </div>
          <div className="mt-5 flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setSelling(false)}>Cancel</Button>
            <Button disabled={!salePrice || Number(salePrice) <= 0}
              onClick={() => { ledger.sell(flip.id, Number(salePrice), Number(saleFees || 0)); setSelling(false); }}>
              Save sale
            </Button>
          </div>
        </Card>
      </Modal>

      <Modal open={confirmingDelete} onClose={() => setConfirmingDelete(false)}>
        <Card className="w-full max-w-md p-6">
          <h2 className="text-lg font-semibold">Delete this flip?</h2>
          <p className="mt-2 text-sm text-muted">It&apos;s removed from this browser and can&apos;t be recovered unless you exported a backup.</p>
          <div className="mt-5 flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setConfirmingDelete(false)}>Cancel</Button>
            <Button onClick={() => ledger.remove(flip.id)}>Delete</Button>
          </div>
        </Card>
      </Modal>
    </Card>
  );
}

export function MyFlips({ ledger, goToCalculator }: { ledger: FlipLedger; goToCalculator: () => void }) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const p = ledger.summary?.portfolio;

  function exportBackup() {
    const blob = new Blob([JSON.stringify(ledger.flips, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "vehiclegrade-flips.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function importBackup(file: File) {
    try {
      const data = JSON.parse(await file.text());
      const looksValid = (f: unknown) => {
        const o = f as Record<string, unknown>;
        return !!o && typeof o.id === "string" && typeof o.make === "string" && typeof o.model === "string"
          && (o.status === "holding" || o.status === "sold") && typeof o.purchase_price === "number" && Array.isArray(o.expenses);
      };
      if (!Array.isArray(data) || !data.every(looksValid)) throw new Error("That doesn't look like a VehicleGrade flips backup.");
      ledger.replaceAll(data);
      setImportError(null);
    } catch (e) {
      setImportError(e instanceof Error ? e.message : "Could not read that file.");
    }
  }

  return (
    <div className="space-y-6">
      <Card className="p-4 text-xs text-muted">
        Your flips are saved <strong>only in this browser</strong> - no account, nothing stored on our servers. Clearing site data or
        switching browsers erases them, so export a backup now and then.
        {!ledger.storageWorks && <span className="text-amber-300"> Your browser is blocking storage, so flips won&apos;t persist.</span>}
      </Card>

      {ledger.error && <p className="text-sm text-red-400">{ledger.error}</p>}

      {p && ledger.flips.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Total net (sold)" value={money(p.total_net)} className={netClass(p.total_net)} />
          <Stat label="Win rate" value={p.win_rate_pct === null ? "-" : `${p.win_rate_pct}%`} />
          <Stat label="Capital tied up" value={money(p.capital_in_holding)} />
          <Stat label="Calculator accuracy (avg error)" value={p.prediction?.avg_net_error == null ? "needs a sold flip" : money(p.prediction.avg_net_error)} className={netClass(p.prediction?.avg_net_error)} />
        </div>
      )}

      {ledger.ready && ledger.flips.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-sm font-medium">No flips yet</p>
          <p className="mt-1 text-sm text-muted">Run the numbers in the calculator, then hit &ldquo;I bought this&rdquo; to start tracking it.</p>
          <Button className="mt-4" onClick={goToCalculator}>Open the calculator</Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {ledger.flips.map((f) => <FlipCard key={f.id} flip={f} ledger={ledger} />)}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <Button variant="secondary" onClick={exportBackup} disabled={ledger.flips.length === 0}>Export backup</Button>
        <Button variant="secondary" onClick={() => fileRef.current?.click()}>Import backup</Button>
        <input ref={fileRef} type="file" accept="application/json" className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) importBackup(f); e.target.value = ""; }} />
        {importError && <span className="text-xs text-red-400">{importError}</span>}
      </div>
    </div>
  );
}
