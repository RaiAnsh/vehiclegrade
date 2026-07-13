import { WorkspaceItem } from "@/hooks/useComparisonWorkspace";
import { ListingDetail } from "@/lib/types";

interface ComparisonTableProps {
  items: (WorkspaceItem & { report: ListingDetail })[];
}

// Side-by-side comparison of every analyzed listing in the workspace. Every
// column is a value the individual report already computed - this table adds
// no new numbers, it just lines them up for easy scanning across listings.
export function ComparisonTable({ items }: ComparisonTableProps) {
  const rows: { label: string; render: (report: ListingDetail) => string }[] = [
    { label: "Vehicle", render: (r) => `${r.year} ${r.make} ${r.model}` },
    { label: "Trim", render: (r) => r.trim ?? "—" },
    { label: "Asking price", render: (r) => `$${r.price.toLocaleString()}` },
    { label: "Mileage", render: (r) => `${r.mileage_km.toLocaleString()} km` },
    { label: "Condition", render: (r) => r.condition },
    { label: "Title status", render: (r) => r.title_status },
    { label: "Location", render: (r) => r.location ?? "—" },
    {
      label: "Known issue risk",
      render: (r) => {
        const overdue = r.known_issues.filter((i) => i.status === "overdue").length;
        return overdue > 0 ? `${overdue} overdue` : "None overdue";
      },
    },
    {
      label: "Immediate maintenance",
      render: (r) => {
        const items = r.maintenance_timeline.immediate;
        if (items.length === 0) return "None due now";
        const min = items.reduce((sum, i) => sum + (i.estimated_cost_min ?? 0), 0);
        const max = items.reduce((sum, i) => sum + (i.estimated_cost_max ?? 0), 0);
        return `$${min.toLocaleString()}–$${max.toLocaleString()}`;
      },
    },
    { label: "Price assessment", render: (r) => r.deal_label },
    { label: "VehicleGrade Score", render: (r) => `${r.vehiclegrade_score}/100` },
    { label: "Confidence", render: (r) => `${r.confidence.level} (${r.confidence.score}/100)` },
  ];

  return (
    <div className="glass-card overflow-x-auto rounded-2xl p-5">
      <table className="w-full min-w-[640px] border-collapse text-sm">
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className="border-b border-white/5 last:border-0">
              <th className="whitespace-nowrap px-3 py-2 text-left font-medium text-muted">{row.label}</th>
              {items.map(({ id, report }) => (
                <td key={id} className="px-3 py-2 text-left">
                  {row.render(report)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
