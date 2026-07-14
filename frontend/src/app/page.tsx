"use client";

import { useState } from "react";

import { Hero } from "@/components/landing/Hero";
import { FeatureHighlights } from "@/components/landing/FeatureHighlights";
import { VehicleReport } from "@/components/report/VehicleReport";
import { ListingDetail } from "@/lib/types";

export default function LandingPage() {
  const [report, setReport] = useState<ListingDetail | null>(null);

  return (
    <>
      <Hero onAnalyzed={setReport} />
      {report && (
        <div className="mx-auto max-w-4xl px-6 pb-16">
          <VehicleReport listing={report} />
        </div>
      )}
      <FeatureHighlights />
    </>
  );
}
