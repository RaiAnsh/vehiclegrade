"use client";

import { motion } from "framer-motion";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ManualFormValue } from "@/components/analyze/ManualForm";

interface ParsedListingConfirmProps {
  formValue: ManualFormValue;
  aiFields: string[];
  onEdit: () => void;
  onConfirm: () => void;
  error: string | null;
  compact?: boolean;
}

function AIAssistedTag() {
  return (
    <span className="ml-1.5 rounded-full bg-purple-400/15 px-1.5 py-0.5 text-[10px] font-medium text-purple-300 ring-1 ring-purple-400/30">
      AI-assisted
    </span>
  );
}

export function ParsedListingConfirm({ formValue, aiFields, onEdit, onConfirm, error, compact }: ParsedListingConfirmProps) {
  const isAiField = (field: string) => aiFields.includes(field);

  const vehicle = [formValue.year, formValue.make, formValue.model, formValue.trim].filter(Boolean).join(" ");

  const rows: { label: string; value: string; field: string }[] = [
    { label: "Vehicle", value: vehicle || "—", field: "make" },
    {
      label: "Mileage",
      value: formValue.mileage_km !== undefined ? `${formValue.mileage_km.toLocaleString()} km` : "—",
      field: "mileage_km",
    },
    { label: "Transmission", value: formValue.transmission ?? "—", field: "transmission" },
    { label: "Price", value: formValue.price !== undefined ? `$${formValue.price.toLocaleString()}` : "—", field: "price" },
    { label: "Location", value: formValue.location ?? "—", field: "location" },
    { label: "Title status", value: formValue.title_status ? formValue.title_status : "Clean (default)", field: "title_status" },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
      <Card className={compact ? "p-4" : "p-6"}>
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--good)]/15 text-[var(--good)]">
            ✓
          </span>
          <h3 className="text-base font-medium">Here&rsquo;s what I found</h3>
        </div>

        <div className="mt-4 divide-y divide-white/5">
          {rows.map((row) => (
            <div key={row.label} className="flex items-center justify-between py-2 text-sm">
              <span className="text-muted">
                {row.label}
                {isAiField(row.field) && <AIAssistedTag />}
              </span>
              <span className="font-medium">{row.value}</span>
            </div>
          ))}
        </div>

        {error && <p className="mt-4 text-sm text-[var(--avoid)]">{error}</p>}

        <div className="mt-5 flex justify-end gap-3">
          <Button variant="secondary" onClick={onEdit}>
            Edit
          </Button>
          <Button onClick={onConfirm}>Analyze Vehicle →</Button>
        </div>
      </Card>
    </motion.div>
  );
}
