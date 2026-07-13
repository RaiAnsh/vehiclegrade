import { Card } from "@/components/ui/Card";
import { SourceBadge } from "./SourceBadge";
import { DataSourceInfo } from "@/lib/types";

interface GeneralGuidanceCardProps {
  guidance: string[];
  source: DataSourceInfo;
}

// Shown only when this vehicle has no known-issue/maintenance data of its
// own, direct or engine-linked - i.e. match_type is "general_guidance". Makes
// the fallback explicit rather than silently showing an empty Known Issues
// section, so the report never implies coverage it doesn't have.
export function GeneralGuidanceCard({ guidance, source }: GeneralGuidanceCardProps) {
  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium">General Guidance</h2>
        <SourceBadge {...source} />
      </div>
      <p className="mt-1 text-sm text-muted">
        We don&apos;t have vehicle-specific known-issue data for this generation yet - here&apos;s
        generic guidance based on mileage and age instead.
      </p>
      <ul className="mt-4 space-y-2">
        {guidance.map((line, i) => (
          <li key={i} className="text-sm text-muted">
            {line}
          </li>
        ))}
      </ul>
    </Card>
  );
}
