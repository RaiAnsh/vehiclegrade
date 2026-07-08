import { Card } from "@/components/ui/Card";

interface InspectionChecklistCardProps {
  checklist: string[];
}

export function InspectionChecklistCard({ checklist }: InspectionChecklistCardProps) {
  if (checklist.length === 0) return null;

  return (
    <Card className="p-6">
      <h2 className="text-lg font-medium">Inspection Checklist</h2>
      <p className="mt-1 text-sm text-muted">
        What to physically check before buying, based on this vehicle&apos;s known issues, upcoming
        maintenance, and location.
      </p>
      <ul className="mt-4 space-y-2">
        {checklist.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm">
            <span className="mt-0.5 text-muted">☐</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
