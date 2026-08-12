"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";
import { useToast } from "@/components/ui/Toast";
import { useAdminAuth } from "@/hooks/useAdminAuth";
import { approveObservation, rejectObservation, updateObservation } from "@/lib/adminApi";
import { ListingObservation, ObservationEdit, RawRow } from "@/lib/adminTypes";
import { flattenGenerations } from "@/lib/catalogHelpers";
import { Catalog } from "@/lib/types";
import { StatusPill } from "./StatusPill";

const TITLE_STATUSES = ["clean", "rebuilt", "salvage", "unknown"];
const CONDITIONS = ["excellent", "good", "fair", "poor"];

interface ObservationCardProps {
  row: RawRow;
  catalog: Catalog | null;
  onChanged: () => void;
}

export function ObservationCard({ row, catalog, onChanged }: ObservationCardProps) {
  const { accessToken, hasPermission } = useAdminAuth();
  const { showToast } = useToast();
  const observation = row.observation;

  const [edit, setEdit] = useState<ObservationEdit>({});
  const [saving, setSaving] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");

  if (!observation) {
    return (
      <Card className="p-5">
        <p className="text-sm text-muted">Row #{row.sequence_in_batch} — not yet processed.</p>
      </Card>
    );
  }

  const isTerminal = observation.review_status === "approved" || observation.review_status === "rejected";
  const canReview = hasPermission("review") && !isTerminal;

  function field<K extends keyof ObservationEdit>(key: K, fallback: ObservationEdit[K]) {
    return key in edit ? edit[key] : fallback;
  }

  function setField<K extends keyof ObservationEdit>(key: K, value: ObservationEdit[K]) {
    setEdit((prev) => ({ ...prev, [key]: value }));
  }

  // Approve/reject act on the server's current state of this observation -
  // any field edited but not yet saved has to be flushed first, or a fix
  // made right before clicking Approve would silently be lost (the approve
  // call would then correctly 400 on the still-unresolved field it never
  // saw). Reject flushes too, so a correction made before rejecting isn't
  // discarded from the audit trail.
  async function flushPendingEdits() {
    if (!accessToken || Object.keys(edit).length === 0) return;
    await updateObservation(accessToken, observation!.id, edit);
    setEdit({});
  }

  async function handleSave() {
    if (!accessToken || Object.keys(edit).length === 0) return;
    setSaving(true);
    try {
      await flushPendingEdits();
      showToast("Saved", "success");
      onChanged();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Save failed", "error");
    } finally {
      setSaving(false);
    }
  }

  async function handleApprove(overrideDuplicate = false) {
    if (!accessToken) return;
    setSaving(true);
    try {
      await flushPendingEdits();
      await approveObservation(accessToken, observation!.id, overrideDuplicate);
      showToast("Approved", "success");
      onChanged();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Approval failed", "error");
    } finally {
      setSaving(false);
    }
  }

  async function handleReject() {
    if (!accessToken || !rejectionReason.trim()) return;
    setSaving(true);
    try {
      await flushPendingEdits();
      await rejectObservation(accessToken, observation!.id, rejectionReason.trim());
      showToast("Rejected", "success");
      setRejecting(false);
      onChanged();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Rejection failed", "error");
    } finally {
      setSaving(false);
    }
  }

  const selectedGenerationId = field("generation_id", observation.generation_id);
  const flatGenerations = flattenGenerations(catalog);
  const selectedGeneration = flatGenerations.find((g) => g.id === selectedGenerationId);

  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <StatusPill status={observation.review_status} />
            {observation.quality_score !== null && (
              <span className="text-xs text-muted">Quality {observation.quality_score}/100</span>
            )}
          </div>
          <p className="mt-2 text-sm font-medium">
            {observation.make_raw ?? "?"} {observation.model_raw ?? ""} {observation.year ?? ""}
          </p>
        </div>
        {row.raw_text && (
          <details className="max-w-xs text-xs text-muted">
            <summary className="cursor-pointer hover:text-foreground">Raw text</summary>
            <pre className="mt-1 whitespace-pre-wrap">{row.raw_text}</pre>
          </details>
        )}
      </div>

      {observation.duplicate_of_observation_id && (
        <div className="mt-3 rounded-xl bg-[var(--fair)]/10 px-3 py-2 text-xs text-[var(--fair)]">
          Likely duplicate of observation #{observation.duplicate_of_observation_id}
        </div>
      )}

      {(observation.validation_errors?.length || observation.unresolved_fields?.length) && (
        <div className="mt-3 space-y-1 text-xs">
          {observation.unresolved_fields?.length ? (
            <p className="text-[var(--fair)]">Missing: {observation.unresolved_fields.join(", ")}</p>
          ) : null}
          {observation.validation_errors?.length ? (
            <p className="text-[var(--avoid)]">Invalid: {observation.validation_errors.join(", ")}</p>
          ) : null}
        </div>
      )}

      {observation.quality_factors && observation.quality_factors.length > 0 && (
        <details className="mt-2 text-xs text-muted">
          <summary className="cursor-pointer hover:text-foreground">Quality score breakdown</summary>
          <ul className="mt-1 space-y-0.5">
            {observation.quality_factors.map((factor, i) => (
              <li key={i}>
                {factor.reason} ({factor.points})
              </li>
            ))}
          </ul>
        </details>
      )}

      {canReview && (
        <div className="mt-4 grid grid-cols-2 gap-3 border-t border-white/5 pt-4 sm:grid-cols-3">
          <div className="col-span-2 sm:col-span-3">
            <label className="mb-1 block text-xs text-muted">Vehicle (generation)</label>
            <Select
              value={selectedGenerationId ?? ""}
              onChange={(e) => {
                setField("generation_id", e.target.value ? Number(e.target.value) : null);
                setField("trim_id", null);
              }}
            >
              <option value="">— unresolved —</option>
              {flatGenerations.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.label}
                </option>
              ))}
            </Select>
          </div>

          {selectedGeneration && selectedGeneration.trims.length > 0 && (
            <div className="col-span-2 sm:col-span-3">
              <label className="mb-1 block text-xs text-muted">Trim</label>
              <Select
                value={field("trim_id", observation.trim_id) ?? ""}
                onChange={(e) => setField("trim_id", e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">— unresolved —</option>
                {selectedGeneration.trims.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </Select>
            </div>
          )}

          <div>
            <label className="mb-1 block text-xs text-muted">Year</label>
            <Input
              type="number"
              value={field("year", observation.year) ?? ""}
              onChange={(e) => setField("year", e.target.value ? Number(e.target.value) : null)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted">Price</label>
            <Input
              type="number"
              value={field("price", observation.price) ?? ""}
              onChange={(e) => setField("price", e.target.value ? Number(e.target.value) : null)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted">Mileage (km)</label>
            <Input
              type="number"
              value={field("mileage_km", observation.mileage_km) ?? ""}
              onChange={(e) => setField("mileage_km", e.target.value ? Number(e.target.value) : null)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted">Title status</label>
            <Select
              value={field("title_status", observation.title_status) ?? ""}
              onChange={(e) => setField("title_status", e.target.value || null)}
            >
              <option value="">— unresolved —</option>
              {TITLE_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted">Condition</label>
            <Select
              value={field("condition", observation.condition) ?? ""}
              onChange={(e) => setField("condition", e.target.value || null)}
            >
              <option value="">—</option>
              {CONDITIONS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted">Transmission</label>
            <Input
              value={field("transmission", observation.transmission) ?? ""}
              onChange={(e) => setField("transmission", e.target.value || null)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted">Fuel type</label>
            <Input
              value={field("fuel_type", observation.fuel_type) ?? ""}
              onChange={(e) => setField("fuel_type", e.target.value || null)}
            />
          </div>

          <div className="col-span-2 flex items-end gap-2 sm:col-span-3">
            <Button variant="secondary" onClick={handleSave} disabled={saving || Object.keys(edit).length === 0}>
              Save changes
            </Button>

            {observation.duplicate_of_observation_id ? (
              <Button variant="secondary" onClick={() => handleApprove(true)} disabled={saving}>
                Approve anyway (override duplicate)
              </Button>
            ) : (
              <Button onClick={() => handleApprove(false)} disabled={saving}>
                Approve
              </Button>
            )}

            {!rejecting ? (
              <Button variant="ghost" onClick={() => setRejecting(true)} disabled={saving}>
                Reject
              </Button>
            ) : null}
          </div>

          {rejecting && (
            <div className="col-span-2 space-y-2 sm:col-span-3">
              <Textarea
                rows={2}
                placeholder="Why is this being rejected?"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
              />
              <div className="flex gap-2">
                <Button variant="secondary" onClick={handleReject} disabled={saving || !rejectionReason.trim()}>
                  Confirm reject
                </Button>
                <Button variant="ghost" onClick={() => setRejecting(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {isTerminal && observation.rejection_reason && (
        <p className="mt-3 text-xs text-muted">Rejection reason: {observation.rejection_reason}</p>
      )}
    </Card>
  );
}
