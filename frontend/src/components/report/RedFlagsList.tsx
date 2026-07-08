import { Card } from "@/components/ui/Card";

interface RedFlagsListProps {
  flags: string[];
}

export function RedFlagsList({ flags }: RedFlagsListProps) {
  if (flags.length === 0) {
    return (
      <Card className="p-6">
        <h2 className="text-lg font-medium">Red Flags</h2>
        <p className="mt-3 text-sm text-muted">No red flags detected for this listing.</p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h2 className="text-lg font-medium">Red Flags</h2>
      <ul className="mt-4 space-y-2">
        {flags.map((flag, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-[var(--avoid)]">
            <span>&#9888;</span>
            <span>{flag}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
