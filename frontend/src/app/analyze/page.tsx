"use client";

import { useState } from "react";

import { ListingIntake } from "@/components/analyze/ListingIntake";
import { VehicleReport } from "@/components/report/VehicleReport";
import { ListingDetail } from "@/lib/types";

export default function AnalyzePage() {
  const [report, setReport] = useState<ListingDetail | null>(null);

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Paste any used vehicle listing.</h1>
      <p className="mt-2 text-muted">Marketplace &middot; AutoTrader &middot; Kijiji &middot; Dealer websites</p>

      <div className="mt-6 space-y-6">
        <ListingIntake onAnalyzed={setReport} />
        {report && <VehicleReport listing={report} />}
      </div>
    </div>
  );
}
