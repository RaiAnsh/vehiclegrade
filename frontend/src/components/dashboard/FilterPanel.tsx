"use client";

import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { useCatalog } from "@/hooks/useCatalog";
import { ListingFilters } from "@/lib/types";

const TITLE_STATUSES = ["clean", "unknown", "rebuilt", "salvage"];
const TRANSMISSIONS = ["Automatic", "Manual", "CVT"];
const FUEL_TYPES = ["Gasoline", "Hybrid", "Diesel"];
const LOCATIONS = [
  "Toronto",
  "Mississauga",
  "Ottawa",
  "Hamilton",
  "Winnipeg",
  "Calgary",
  "Vancouver",
  "Phoenix",
  "Buffalo",
  "Miami",
  "Chicago",
  "Denver",
];

interface FilterPanelProps {
  filters: ListingFilters;
  onChange: (filters: ListingFilters) => void;
}

export function FilterPanel({ filters, onChange }: FilterPanelProps) {
  const { catalog } = useCatalog();

  function update<K extends keyof ListingFilters>(key: K, value: ListingFilters[K]) {
    onChange({ ...filters, [key]: value });
  }

  const models = catalog?.makes.find((m) => m.name === filters.make)?.models ?? [];

  return (
    <Card className="p-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label className="mb-1.5 block text-xs text-muted">Make</label>
          <Select
            value={filters.make ?? ""}
            onChange={(e) => onChange({ ...filters, make: e.target.value || undefined, model: undefined })}
          >
            <option value="">Any make</option>
            {catalog?.makes.map((make) => (
              <option key={make.id} value={make.name}>
                {make.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Model</label>
          <Select
            value={filters.model ?? ""}
            onChange={(e) => update("model", e.target.value || undefined)}
            disabled={!filters.make}
          >
            <option value="">Any model</option>
            {models.map((model) => (
              <option key={model.id} value={model.name}>
                {model.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Max budget</label>
          <Input
            type="number"
            placeholder="$"
            value={filters.max_price ?? ""}
            onChange={(e) => update("max_price", e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Max mileage</label>
          <Input
            type="number"
            placeholder="km"
            value={filters.max_mileage ?? ""}
            onChange={(e) => update("max_mileage", e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Min year</label>
          <Input
            type="number"
            placeholder="e.g. 2015"
            value={filters.min_year ?? ""}
            onChange={(e) => update("min_year", e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Max year</label>
          <Input
            type="number"
            placeholder="e.g. 2024"
            value={filters.max_year ?? ""}
            onChange={(e) => update("max_year", e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Title status</label>
          <Select
            value={filters.title_status ?? ""}
            onChange={(e) => update("title_status", e.target.value as ListingFilters["title_status"])}
          >
            <option value="">Any title</option>
            {TITLE_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status[0].toUpperCase() + status.slice(1)}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Transmission</label>
          <Select value={filters.transmission ?? ""} onChange={(e) => update("transmission", e.target.value || undefined)}>
            <option value="">Any transmission</option>
            {TRANSMISSIONS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Fuel type</label>
          <Select value={filters.fuel_type ?? ""} onChange={(e) => update("fuel_type", e.target.value || undefined)}>
            <option value="">Any fuel type</option>
            {FUEL_TYPES.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Location</label>
          <Select value={filters.location ?? ""} onChange={(e) => update("location", e.target.value || undefined)}>
            <option value="">Any location</option>
            {LOCATIONS.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-end">
        <Button variant="ghost" onClick={() => onChange({})}>
          Clear filters
        </Button>
      </div>
    </Card>
  );
}
