import { Card } from "@/components/ui/Card";
import { StarRating } from "@/components/dashboard/StarRating";
import { SourceBadge } from "./SourceBadge";
import { ListingDetail } from "@/lib/types";

const PARTS_AVAILABILITY_LABEL: Record<string, string> = {
  excellent: "Excellent",
  good: "Good",
  fair: "Fair",
  poor: "Poor",
};

const INSURANCE_CATEGORY_LABEL: Record<string, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

interface ReliabilityCardProps {
  listing: ListingDetail;
}

export function ReliabilityCard({ listing }: ReliabilityCardProps) {
  const { reliability } = listing;

  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium">Reliability</h2>
        <div className="flex items-center gap-3">
          <StarRating value={reliability.stars} showValue color="var(--good)" />
          <SourceBadge {...listing.data_sources.reliability} />
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <div>
          <p className="text-xs text-muted">Expected annual maintenance</p>
          <p className="mt-1 font-medium">${reliability.expected_annual_maintenance_cost.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-muted">Typical lifespan</p>
          <p className="mt-1 font-medium">{reliability.typical_lifespan_km.toLocaleString()} km</p>
        </div>
        <div>
          <p className="text-xs text-muted">Parts availability</p>
          <p className="mt-1 font-medium">{PARTS_AVAILABILITY_LABEL[reliability.parts_availability]}</p>
        </div>
        <div>
          <p className="text-xs text-muted">Insurance category</p>
          <p className="mt-1 font-medium">{INSURANCE_CATEGORY_LABEL[reliability.insurance_category]}</p>
        </div>
      </div>
    </Card>
  );
}
