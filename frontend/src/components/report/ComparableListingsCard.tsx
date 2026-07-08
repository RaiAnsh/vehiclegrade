import { Card } from "@/components/ui/Card";
import { SourceBadge } from "./SourceBadge";
import { ComparableListingsSummary, DataSourceInfo } from "@/lib/types";

interface ComparableListingsCardProps {
  comparables: ComparableListingsSummary;
  source: DataSourceInfo;
}

export function ComparableListingsCard({ comparables, source }: ComparableListingsCardProps) {
  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium">Comparable Listings</h2>
        <SourceBadge {...source} />
      </div>

      {comparables.count === 0 ? (
        <p className="mt-3 text-sm text-muted">
          No comparable listings found for this vehicle in the current sample data.
        </p>
      ) : (
        <>
          <div className="mt-4 grid gap-4 sm:grid-cols-4">
            <div>
              <p className="text-xs text-muted">Sample size</p>
              <p className="mt-1 text-xl font-semibold">{comparables.count}</p>
            </div>
            <div>
              <p className="text-xs text-muted">Average price</p>
              <p className="mt-1 text-xl font-semibold">${comparables.avg_price?.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-muted">Median price</p>
              <p className="mt-1 text-xl font-semibold">${comparables.median_price?.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-muted">Price percentile</p>
              <p className="mt-1 text-xl font-semibold">
                {comparables.price_percentile !== null ? `${comparables.price_percentile}th` : "—"}
              </p>
            </div>
          </div>

          {!comparables.band_applied && (
            <p className="mt-3 text-xs text-muted">
              Too few similar-mileage listings were available, so this sample was widened to the full generation.
            </p>
          )}

          <div className="mt-5 overflow-x-auto border-t border-white/5 pt-4">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs text-muted">
                  <th className="pb-2 pr-4 font-medium">Price</th>
                  <th className="pb-2 pr-4 font-medium">Mileage</th>
                  <th className="pb-2 pr-4 font-medium">Condition</th>
                  <th className="pb-2 pr-4 font-medium">Title</th>
                  <th className="pb-2 pr-4 font-medium">Location</th>
                  <th className="pb-2 font-medium">Days listed</th>
                </tr>
              </thead>
              <tbody>
                {comparables.comparables.map((row, i) => (
                  <tr key={i} className="border-t border-white/5">
                    <td className="py-2 pr-4">${row.price.toLocaleString()}</td>
                    <td className="py-2 pr-4">{row.mileage_km.toLocaleString()} km</td>
                    <td className="py-2 pr-4 capitalize">{row.condition}</td>
                    <td className="py-2 pr-4 capitalize">{row.title_status}</td>
                    <td className="py-2 pr-4">{row.location ?? "—"}</td>
                    <td className="py-2">{row.days_listed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <p className="mt-4 text-xs text-muted">{comparables.disclosure}</p>
    </Card>
  );
}
