"use client";

import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Toggle } from "@/components/ui/Toggle";
import { Button } from "@/components/ui/Button";
import { ListingFilters } from "@/lib/types";

const MODELS = ["iPhone 11", "iPhone 12", "iPhone 13", "iPhone 14", "iPhone 15"];
const STORAGE_TIERS = [64, 128, 256, 512];
const CONDITIONS = ["excellent", "good", "fair", "poor"];
const LOCATIONS = [
  "Toronto",
  "Mississauga",
  "Brampton",
  "Markham",
  "Vaughan",
  "Scarborough",
  "North York",
  "Etobicoke",
  "Oakville",
  "Hamilton",
];

interface FilterPanelProps {
  filters: ListingFilters;
  onChange: (filters: ListingFilters) => void;
}

export function FilterPanel({ filters, onChange }: FilterPanelProps) {
  function update<K extends keyof ListingFilters>(key: K, value: ListingFilters[K]) {
    onChange({ ...filters, [key]: value });
  }

  return (
    <Card className="p-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
        <div className="lg:col-span-1">
          <label className="mb-1.5 block text-xs text-muted">Model</label>
          <Select value={filters.model ?? ""} onChange={(e) => update("model", e.target.value)}>
            <option value="">Any model</option>
            {MODELS.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </Select>
        </div>

        <div className="lg:col-span-1">
          <label className="mb-1.5 block text-xs text-muted">Max budget</label>
          <Input
            type="number"
            placeholder="$"
            value={filters.max_price ?? ""}
            onChange={(e) => update("max_price", e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <div className="lg:col-span-1">
          <label className="mb-1.5 block text-xs text-muted">Storage</label>
          <Select
            value={filters.storage ?? ""}
            onChange={(e) => update("storage", e.target.value ? Number(e.target.value) : undefined)}
          >
            <option value="">Any storage</option>
            {STORAGE_TIERS.map((tier) => (
              <option key={tier} value={tier}>
                {tier}GB
              </option>
            ))}
          </Select>
        </div>

        <div className="lg:col-span-1">
          <label className="mb-1.5 block text-xs text-muted">Min battery health</label>
          <Input
            type="number"
            placeholder="e.g. 85"
            value={filters.battery_min ?? ""}
            onChange={(e) => update("battery_min", e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <div className="lg:col-span-1">
          <label className="mb-1.5 block text-xs text-muted">Condition</label>
          <Select value={filters.condition ?? ""} onChange={(e) => update("condition", e.target.value as ListingFilters["condition"])}>
            <option value="">Any condition</option>
            {CONDITIONS.map((condition) => (
              <option key={condition} value={condition}>
                {condition[0].toUpperCase() + condition.slice(1)}
              </option>
            ))}
          </Select>
        </div>

        <div className="lg:col-span-1">
          <label className="mb-1.5 block text-xs text-muted">Location</label>
          <Select value={filters.location ?? ""} onChange={(e) => update("location", e.target.value)}>
            <option value="">Any location</option>
            {LOCATIONS.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div className="w-48">
          <Toggle
            checked={filters.unlocked === true}
            onChange={(checked) => update("unlocked", checked ? true : undefined)}
            label="Unlocked only"
          />
        </div>
        <Button variant="ghost" onClick={() => onChange({})}>
          Clear filters
        </Button>
      </div>
    </Card>
  );
}
