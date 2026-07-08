import { Card } from "@/components/ui/Card";
import { SourceBadge } from "./SourceBadge";
import { DataSourceInfo, MaintenanceTimeline as MaintenanceTimelineType, MaintenanceTimelineItem } from "@/lib/types";

const COLUMNS: { key: keyof MaintenanceTimelineType; label: string; color: string }[] = [
  { key: "immediate", label: "Immediate", color: "var(--avoid)" },
  { key: "soon", label: "Soon", color: "var(--fair)" },
  { key: "future", label: "Future", color: "var(--muted)" },
];

function ItemRow({ item, color }: { item: MaintenanceTimelineItem; color: string }) {
  return (
    <div className="rounded-lg border border-white/5 p-3">
      <p className="text-sm font-medium">{item.name}</p>
      <p className="mt-1 text-xs text-muted">
        Every {item.interval_km.toLocaleString()} km &middot;{" "}
        <span style={{ color }}>
          {item.due_in_km === 0 ? "due now" : `due in ${item.due_in_km.toLocaleString()} km`}
        </span>
      </p>
      {item.estimated_cost_min !== null && item.estimated_cost_max !== null && (
        <p className="mt-1 text-xs text-muted">
          Est. ${item.estimated_cost_min.toLocaleString()} - ${item.estimated_cost_max.toLocaleString()}
        </p>
      )}
    </div>
  );
}

interface MaintenanceTimelineProps {
  timeline: MaintenanceTimelineType;
  source: DataSourceInfo;
}

export function MaintenanceTimeline({ timeline, source }: MaintenanceTimelineProps) {
  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium">Maintenance Timeline</h2>
        <SourceBadge {...source} />
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        {COLUMNS.map((column) => {
          const items = timeline[column.key];
          return (
            <div key={column.key}>
              <p className="text-xs font-medium" style={{ color: column.color }}>
                {column.label}
              </p>
              <div className="mt-2 space-y-2">
                {items.length === 0 ? (
                  <p className="text-xs text-muted">Nothing here</p>
                ) : (
                  items.map((item) => <ItemRow key={item.name} item={item} color={column.color} />)
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
