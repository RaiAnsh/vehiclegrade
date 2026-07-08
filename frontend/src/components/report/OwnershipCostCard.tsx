import { Card } from "@/components/ui/Card";
import { SourceBadge } from "./SourceBadge";
import { DataSourceInfo, OwnershipCost } from "@/lib/types";

interface OwnershipCostCardProps {
  cost: OwnershipCost;
  source: DataSourceInfo;
}

export function OwnershipCostCard({ cost, source }: OwnershipCostCardProps) {
  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium">Estimated Annual Ownership Cost</h2>
        <SourceBadge {...source} />
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-4">
        <div>
          <p className="text-xs text-muted">Fuel</p>
          <p className="mt-1 font-medium">${cost.fuel_annual.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-muted">Insurance</p>
          <p className="mt-1 font-medium">${cost.insurance_annual.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-muted">Maintenance</p>
          <p className="mt-1 font-medium">${cost.maintenance_annual.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-muted">Total / year</p>
          <p className="mt-1 text-lg font-semibold">${cost.total_annual.toLocaleString()}</p>
        </div>
      </div>
    </Card>
  );
}
