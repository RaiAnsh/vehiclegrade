import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SourceBadge } from "./SourceBadge";
import { ComparableVehicle, DataSourceInfo } from "@/lib/types";

interface ComparableVehiclesCardProps {
  vehicles: ComparableVehicle[];
  source: DataSourceInfo;
}

export function ComparableVehiclesCard({ vehicles, source }: ComparableVehiclesCardProps) {
  if (vehicles.length === 0) return null;

  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium">Instead, Also Consider</h2>
        <SourceBadge {...source} />
      </div>
      <p className="mt-1 text-sm text-muted">Common competitors to this vehicle.</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {vehicles.map((vehicle) => (
          <Badge key={vehicle.name}>
            {vehicle.name}
            {!vehicle.has_data && <span className="ml-1.5 text-[10px] text-muted">(not yet in VehicleGrade)</span>}
          </Badge>
        ))}
      </div>
    </Card>
  );
}
