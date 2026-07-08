import { Card } from "@/components/ui/Card";
import { DealBadge } from "@/components/ui/Badge";
import { ScoreBadge } from "@/components/dashboard/ScoreBadge";
import { StarRating } from "@/components/dashboard/StarRating";
import { SourceBadge } from "./SourceBadge";
import { ListingDetail } from "@/lib/types";

interface ScoreHeaderProps {
  listing: ListingDetail;
}

export function ScoreHeader({ listing }: ScoreHeaderProps) {
  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div>
          <p className="text-sm text-muted">{listing.generation_label}</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            {listing.year} {listing.make} {listing.model}
            {listing.trim ? <span className="text-muted"> {listing.trim}</span> : null}
          </h1>
          <p className="mt-1 text-sm text-muted">{listing.location ?? "Unknown location"}</p>

          <div className="mt-4 flex items-center gap-3">
            <DealBadge label={listing.deal_label} />
            <StarRating value={listing.score_stars} showValue />
          </div>
        </div>

        <div className="flex flex-col items-center gap-2">
          <ScoreBadge score={listing.vehiclegrade_score} dealLabel={listing.deal_label} size={72} />
          <p className="text-xs text-muted">VehicleGrade Score</p>
          <SourceBadge {...listing.data_sources.vehiclegrade_score} />
        </div>
      </div>

      <ul className="mt-6 grid gap-2 border-t border-white/5 pt-5 sm:grid-cols-2">
        {listing.score_reasons.map((reason, i) => (
          <li key={i} className="text-sm text-muted">
            {reason}
          </li>
        ))}
      </ul>
    </Card>
  );
}
