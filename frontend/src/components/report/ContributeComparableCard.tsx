"use client";

import { useState } from "react";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { submitCommunityComparable } from "@/lib/api";
import { ListingDetail } from "@/lib/types";

interface ContributeComparableCardProps {
  listing: ListingDetail;
}

// Opt-in, unchecked-by-default contribution of this listing as an anonymous
// comparable data point. Only the whitelisted, structured fields already
// shown in this report are sent - nothing free-text, nothing that could
// carry PII (see CommunityComparable on the backend, which has no free-text
// column at all). Not surfaced anywhere as reliable market data yet; this is
// purely collection toward a future reviewed sample.
export function ContributeComparableCard({ listing }: ContributeComparableCardProps) {
  const [optedIn, setOptedIn] = useState(false);
  const [status, setStatus] = useState<"idle" | "submitting" | "done" | "error">("idle");

  function handleSubmit() {
    setStatus("submitting");
    submitCommunityComparable({
      year: listing.year,
      make: listing.make,
      model: listing.model,
      trim: listing.trim ?? undefined,
      price: listing.price,
      mileage_km: listing.mileage_km,
      condition: listing.condition,
      title_status: listing.title_status,
      city: listing.location ?? undefined,
    })
      .then(() => setStatus("done"))
      .catch(() => setStatus("error"));
  }

  return (
    <Card className="p-6">
      <h2 className="text-lg font-medium">Help Improve VehicleGrade</h2>
      <p className="mt-2 text-sm text-muted">
        Optionally contribute this listing&apos;s year, make, model, trim, price, mileage, condition,
        title status, and city anonymously as a comparable data point. No name, contact info, listing
        URL, or description text is ever collected. This isn&apos;t used anywhere in the app yet &mdash;
        it&apos;s collected toward a future, reviewed comparables dataset.
      </p>

      {status === "done" ? (
        <p className="mt-4 text-sm text-[var(--good)]">Thanks &mdash; your contribution was received.</p>
      ) : (
        <>
          <label className="mt-4 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={optedIn}
              onChange={(e) => setOptedIn(e.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-white/[0.04]"
            />
            Contribute this listing anonymously
          </label>

          {status === "error" && (
            <p className="mt-2 text-sm text-[var(--avoid)]">Something went wrong &mdash; please try again.</p>
          )}

          <div className="mt-4 flex justify-end">
            <Button onClick={handleSubmit} disabled={!optedIn || status === "submitting"}>
              {status === "submitting" ? "Submitting..." : "Submit"}
            </Button>
          </div>
        </>
      )}
    </Card>
  );
}
