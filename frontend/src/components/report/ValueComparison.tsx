import { Card } from "@/components/ui/Card";
import { SourceBadge } from "./SourceBadge";
import { ListingDetail } from "@/lib/types";

interface ValueComparisonProps {
  listing: ListingDetail;
}

export function ValueComparison({ listing }: ValueComparisonProps) {
  const { value_breakdown: breakdown } = listing;
  const savingsPositive = listing.potential_savings >= 0;

  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium">Market Value</h2>
        <SourceBadge {...listing.data_sources.market_value} />
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-4">
        <div>
          <p className="text-xs text-muted">Market value</p>
          <p className="mt-1 text-xl font-semibold">${listing.market_value.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-muted">Asking price</p>
          <p className="mt-1 text-xl font-semibold">${listing.price.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-muted">Potential savings</p>
          <p className={`mt-1 text-xl font-semibold ${savingsPositive ? "text-[var(--excellent)]" : "text-[var(--avoid)]"}`}>
            ${listing.potential_savings.toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted">Suggested offer</p>
          <p className="mt-1 text-xl font-semibold">${listing.suggested_offer.toLocaleString()}</p>
        </div>
      </div>

      <div className="mt-6 border-t border-white/5 pt-5">
        <p className="text-xs text-muted">How the market value was calculated</p>
        <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
          <div className="flex justify-between">
            <span className="text-muted">Base value</span>
            <span>${breakdown.base_value.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted">Trim adjustment</span>
            <span>{(breakdown.trim_adjustment * 100).toFixed(0)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted">Mileage adjustment</span>
            <span>{(breakdown.mileage_adjustment * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted">Title adjustment</span>
            <span>{(breakdown.title_adjustment * 100).toFixed(0)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted">Condition adjustment ({listing.condition})</span>
            <span>{(breakdown.condition_adjustment * 100).toFixed(0)}%</span>
          </div>
          <div className="flex justify-between font-medium sm:col-span-2">
            <span>Final market value</span>
            <span>${breakdown.final.toLocaleString()}</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
