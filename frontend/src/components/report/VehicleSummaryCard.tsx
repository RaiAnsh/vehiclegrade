import { Card } from "@/components/ui/Card";
import { SourceBadge } from "./SourceBadge";
import { EngineMatchStatus, ListingDetail } from "@/lib/types";

interface VehicleSummaryCardProps {
  listing: ListingDetail;
}

const ENGINE_MATCH_COLOR: Record<EngineMatchStatus, string> = {
  exact: "var(--good)",
  ambiguous: "var(--fair)",
  unidentified: "var(--muted)",
};

export function VehicleSummaryCard({ listing }: VehicleSummaryCardProps) {
  const { vehicle_summary: summary } = listing;
  const engineMatchColor = ENGINE_MATCH_COLOR[summary.engine_match.status];

  const fields = [
    { label: "Engine", value: summary.engine ?? "—" },
    { label: "Transmission", value: listing.transmission },
    { label: "Drivetrain", value: summary.drivetrain },
    { label: "Horsepower", value: `${summary.horsepower} hp` },
    { label: "Fuel economy", value: `${summary.fuel_economy_l_per_100km} L/100km` },
    { label: "Fuel type", value: listing.fuel_type },
  ];

  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium">Vehicle Summary</h2>
        <SourceBadge {...listing.data_sources.vehicle_summary} />
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        {fields.map((field) => (
          <div key={field.label}>
            <p className="text-xs text-muted">{field.label}</p>
            <p className="mt-1 font-medium">{field.value}</p>
          </div>
        ))}
      </div>

      {summary.engine_match.status !== "exact" && (
        <p
          className="mt-4 rounded-lg px-3 py-2 text-xs"
          style={{ backgroundColor: `${engineMatchColor}1a`, color: engineMatchColor }}
        >
          {summary.engine_match.label}
        </p>
      )}

      {summary.common_competitors && (
        <div className="mt-5 border-t border-white/5 pt-4">
          <p className="text-xs text-muted">Common competitors</p>
          <p className="mt-1 text-sm">{summary.common_competitors}</p>
        </div>
      )}
    </Card>
  );
}
