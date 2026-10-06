"use client";

import { useState } from "react";

import { ListingIntake } from "@/components/analyze/ListingIntake";
import { VehicleReport } from "@/components/report/VehicleReport";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { CalculatorPrefill } from "@/components/flip/FlipCalculator";
import { ListingDetail, TitleStatus, Condition } from "@/lib/types";

// "Is this listing a good deal?" is exactly what /analyze already answers, so
// the research tab reuses that flow and then hands the vehicle straight to the
// flip calculator ("great deal to drive" and "great deal to flip" differ).
export function FlipResearch({ onRunNumbers }: { onRunNumbers: (prefill: CalculatorPrefill) => void }) {
  const [report, setReport] = useState<ListingDetail | null>(null);

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted">
        Paste any listing to see its specs, fair market value, red flags, known issues and what to ask the seller - then run the flip
        numbers on it.
      </p>
      <ListingIntake onAnalyzed={setReport} />

      {report && (
        <>
          <Card className="flex flex-wrap items-center justify-between gap-3 p-5">
            <div>
              <p className="text-sm font-medium">Thinking of flipping this {report.year} {report.make} {report.model}?</p>
              <p className="text-xs text-muted">
                Asking {Math.round(report.price).toLocaleString()} vs estimated value {Math.round(report.market_value).toLocaleString()}. See what
                you&apos;d actually net after tax, insurance, repairs and resale.
              </p>
            </div>
            <Button
              onClick={() =>
                onRunNumbers({
                  make: report.make, model: report.model, year: report.year, trim: report.trim ?? undefined,
                  mileage_km: report.mileage_km, purchase_price: Math.round(report.suggested_offer ?? report.price),
                  title_status: report.title_status as TitleStatus, condition: report.condition as Condition,
                })
              }
            >
              Run flip numbers at the suggested offer
            </Button>
          </Card>
          <VehicleReport listing={report} />
        </>
      )}
    </div>
  );
}
