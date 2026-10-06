"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useCatalog } from "@/hooks/useCatalog";
import { calculateFlip } from "@/lib/api";
import { Condition, FlipInput, FlipResult, FlipVerdict, LocalFlip, TitleStatus } from "@/lib/types";

const TITLE_STATUSES: TitleStatus[] = ["clean", "unknown", "rebuilt", "salvage"];
const CONDITIONS: Condition[] = ["excellent", "good", "fair", "poor"];

const VERDICT_COPY: Record<FlipVerdict, { label: string; className: string }> = {
  profitable: { label: "Profitable", className: "text-green-400" },
  break_even: { label: "Break-even / small loss", className: "text-green-300" },
  only_works_if_sale_goes_well: { label: "Only works if the sale goes well", className: "text-amber-300" },
  likely_loss: { label: "Likely loss", className: "text-red-400" },
};

const LINE_LABELS: Record<string, string> = {
  purchase_price: "Purchase price",
  ontario_rst: "Ontario RST (13%)",
  uvip_and_transfer: "UVIP + ownership transfer",
  history_report: "History report",
  pre_purchase_inspection: "Pre-purchase inspection",
  insurance: "Insurance",
  fuel: "Fuel",
  routine_maintenance: "Routine maintenance",
  safety_certificate: "Safety certificate",
  detail_and_prep: "Detail & prep",
  listing_and_admin: "Listing & admin",
};

const money = (n: number) => `${n < 0 ? "-" : ""}$${Math.abs(Math.round(n)).toLocaleString()}`;

interface FormState {
  make?: string;
  model?: string;
  year?: number;
  trim?: string;
  mileage_km?: number;
  purchase_price?: number;
  months_held: number;
  title_status: TitleStatus;
  condition: Condition;
  insurance_annual?: number;
  repair_budget?: number;
  expected_sale_price?: number;
}

function LineItems({ title, items, total }: { title: string; items: Record<string, number>; total: number }) {
  return (
    <div>
      <div className="mb-2 flex justify-between text-sm font-medium">
        <span>{title}</span>
        <span>{money(total)}</span>
      </div>
      <dl className="space-y-1 text-xs text-muted">
        {Object.entries(items).map(([key, value]) => (
          <div key={key} className="flex justify-between">
            <dt>{LINE_LABELS[key] ?? key}</dt>
            <dd>{money(value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export interface CalculatorPrefill {
  make?: string;
  model?: string;
  year?: number;
  trim?: string;
  mileage_km?: number;
  purchase_price?: number;
  title_status?: TitleStatus;
  condition?: Condition;
}

interface FlipCalculatorProps {
  prefill?: CalculatorPrefill;
  // Called when the user says they actually bought it: the hub saves it to
  // their browser-stored ledger together with this prediction snapshot.
  onTrack?: (flip: Omit<LocalFlip, "id" | "status" | "expenses" | "purchase_date">) => void;
}

export function FlipCalculator({ prefill, onTrack }: FlipCalculatorProps) {
  const { catalog } = useCatalog();
  const [form, setForm] = useState<FormState>({ months_held: 3, title_status: "clean", condition: "good", ...prefill });
  const [tracked, setTracked] = useState(false);
  const [result, setResult] = useState<FlipResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((f) => ({ ...f, [key]: value }));
  const num = (v: string) => (v === "" ? undefined : Number(v));

  const models = catalog?.makes.find((m) => m.name === form.make)?.models ?? [];
  const generation = models
    .find((m) => m.name === form.model)
    ?.generations.find((g) => form.year !== undefined && form.year >= g.start_year && form.year <= g.end_year);

  const canSubmit = form.make && form.model && form.year && form.mileage_km !== undefined && form.purchase_price;

  async function submit() {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const input: FlipInput = {
        make: form.make!, model: form.model!, year: form.year!, trim: form.trim,
        mileage_km: form.mileage_km!, purchase_price: form.purchase_price!, months_held: form.months_held,
        title_status: form.title_status, condition: form.condition,
        insurance_annual: form.insurance_annual, repair_budget: form.repair_budget,
        expected_sale_price: form.expected_sale_price,
      };
      setResult(await calculateFlip(input));
      setTracked(false);
    } catch (e) {
      setResult(null);
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  const verdict = result ? VERDICT_COPY[result.verdict] : null;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-xs text-muted">Make</label>
            <Select value={form.make ?? ""} onChange={(e) => setForm((f) => ({ ...f, make: e.target.value || undefined, model: undefined, trim: undefined }))}>
              <option value="">Select make</option>
              {catalog?.makes.map((m) => (
                <option key={m.id} value={m.name}>{m.name}</option>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-muted">Model</label>
            <Select value={form.model ?? ""} disabled={!form.make} onChange={(e) => setForm((f) => ({ ...f, model: e.target.value || undefined, trim: undefined }))}>
              <option value="">Select model</option>
              {models.map((m) => (
                <option key={m.id} value={m.name}>{m.name}</option>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-muted">Year</label>
            <Input type="number" placeholder="e.g. 2011" value={form.year ?? ""} disabled={!form.model} onChange={(e) => update("year", num(e.target.value))} />
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-muted">Trim (optional)</label>
            <Select value={form.trim ?? ""} disabled={!generation} onChange={(e) => update("trim", e.target.value || undefined)}>
              <option value="">Any trim</option>
              {generation?.trims.map((t) => (
                <option key={t.id} value={t.name}>{t.name}</option>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-muted">Mileage (km)</label>
            <Input type="number" placeholder="e.g. 150000" value={form.mileage_km ?? ""} onChange={(e) => update("mileage_km", num(e.target.value))} />
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-muted">Purchase price ($)</label>
            <Input type="number" placeholder="e.g. 9000" value={form.purchase_price ?? ""} onChange={(e) => update("purchase_price", num(e.target.value))} />
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-muted">Months you&apos;ll hold it</label>
            <Input type="number" step="0.5" min="0.5" max="36" value={form.months_held} onChange={(e) => update("months_held", Number(e.target.value))} />
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-muted">Title</label>
            <Select value={form.title_status} onChange={(e) => update("title_status", e.target.value as TitleStatus)}>
              {TITLE_STATUSES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-muted">Condition</label>
            <Select value={form.condition} onChange={(e) => update("condition", e.target.value as Condition)}>
              {CONDITIONS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </Select>
          </div>
        </div>

        <details className="mt-5 text-sm">
          <summary className="cursor-pointer text-muted">Override my assumptions (recommended once you have real quotes)</summary>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <div>
              <label className="mb-1.5 block text-xs text-muted">Insurance per year ($)</label>
              <Input type="number" placeholder="Default: young-driver estimate" value={form.insurance_annual ?? ""} onChange={(e) => update("insurance_annual", num(e.target.value))} />
            </div>
            <div>
              <label className="mb-1.5 block text-xs text-muted">Repair budget ($)</label>
              <Input type="number" placeholder="Default: known-issue reserve" value={form.repair_budget ?? ""} onChange={(e) => update("repair_budget", num(e.target.value))} />
            </div>
            <div>
              <label className="mb-1.5 block text-xs text-muted">Expected sale price ($)</label>
              <Input type="number" placeholder="Default: market estimate" value={form.expected_sale_price ?? ""} onChange={(e) => update("expected_sale_price", num(e.target.value))} />
            </div>
          </div>
        </details>

        {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
        <div className="mt-6">
          <Button onClick={submit} disabled={!canSubmit || submitting}>
            {submitting ? "Calculating..." : "Calculate flip"}
          </Button>
        </div>
      </Card>

      {result && verdict && (
        <>
          <Card className="p-6">
            <p className="text-xs uppercase tracking-wide text-muted">
              {result.vehicle.year} {result.vehicle.make} {result.vehicle.model} &middot; {result.months_held} month hold
            </p>
            <p className={`mt-2 text-3xl font-semibold ${verdict.className}`}>
              {money(result.expected_net)} <span className="text-base font-normal">expected</span>
            </p>
            <p className={`mt-1 text-sm ${verdict.className}`}>{verdict.label}</p>

            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              {(["pessimistic", "expected", "optimistic"] as const).map((key) => (
                <div key={key} className="rounded-xl border border-white/10 p-4">
                  <p className="text-xs capitalize text-muted">{key} sale</p>
                  <p className="mt-1 text-lg font-medium">{money(result.scenarios[key].sale_price)}</p>
                  <p className={`text-sm ${result.scenarios[key].net >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {money(result.scenarios[key].net)}
                  </p>
                </div>
              ))}
            </div>

            {onTrack && (
              <div className="mt-6">
                <Button
                  variant="secondary"
                  disabled={tracked}
                  onClick={() => {
                    const buying = result.costs.buying;
                    onTrack({
                      make: result.vehicle.make, model: result.vehicle.model, year: result.vehicle.year,
                      trim: form.trim, mileage_at_purchase: form.mileage_km!, planned_months: result.months_held,
                      purchase_price: buying.purchase_price, purchase_tax: buying.ontario_rst,
                      purchase_fees: buying.uvip_and_transfer + buying.history_report + buying.pre_purchase_inspection,
                      predicted: result,
                    });
                    setTracked(true);
                  }}
                >
                  {tracked ? "Saved to My Flips" : "I bought this - track it in My Flips"}
                </Button>
              </div>
            )}

            <div className="mt-6 grid gap-4 text-sm sm:grid-cols-3">
              <div>
                <p className="text-xs text-muted">Break-even sale price</p>
                <p className="font-medium">{money(result.break_even_sale_price)}</p>
              </div>
              <div>
                <p className="text-xs text-muted">Max price to pay for target of {money(result.target_net)}</p>
                <p className="font-medium">{money(result.max_purchase_price)}</p>
              </div>
              <div>
                <p className="text-xs text-muted">Holding cost per month</p>
                <p className="font-medium">{money(result.monthly_cost_to_hold)}</p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="mb-4 text-lg font-medium">Where the money goes</h2>
            <div className="grid gap-6 sm:grid-cols-2">
              <LineItems title="Buying" items={result.costs.buying} total={result.costs.totals.buying} />
              <LineItems title="Holding" items={result.costs.holding} total={result.costs.totals.holding} />
              <LineItems title="Selling" items={result.costs.selling} total={result.costs.totals.selling} />
              <div>
                <div className="mb-2 flex justify-between text-sm font-medium">
                  <span>Repair reserve</span>
                  <span>{money(result.costs.repair_reserve)}</span>
                </div>
                <ul className="space-y-1 text-xs text-muted">
                  {result.repair_reserve_items.slice(0, 5).map((item) => (
                    <li key={item.issue} className="flex justify-between gap-3">
                      <span>{item.issue} ({Math.round(item.probability * 100)}% of {money(item.cost_range[0])}-{money(item.cost_range[1])})</span>
                      <span>{money(item.expected_cost)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <p className="mt-5 flex justify-between border-t border-white/10 pt-4 text-sm font-medium">
              <span>All-in cost</span>
              <span>{money(result.costs.totals.all_in)}</span>
            </p>
          </Card>

          {(result.warnings.length > 0 || result.assumptions.length > 0) && (
            <Card className="p-6 text-sm">
              {result.warnings.map((w) => (
                <p key={w} className="mb-2 text-amber-300">&#9888; {w}</p>
              ))}
              <p className="mt-2 text-xs uppercase tracking-wide text-muted">Assumptions to check</p>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
                {result.assumptions.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
