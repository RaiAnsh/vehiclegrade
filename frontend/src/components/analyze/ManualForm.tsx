"use client";

import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { useCatalog } from "@/hooks/useCatalog";
import { AnalyzeInput, TitleStatus } from "@/lib/types";

const TITLE_STATUSES: TitleStatus[] = ["clean", "unknown", "rebuilt", "salvage"];
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

export interface ManualFormValue extends Partial<AnalyzeInput> {
  make?: string;
  model?: string;
}

interface ManualFormProps {
  value: ManualFormValue;
  onChange: (value: ManualFormValue) => void;
  onSubmit: () => void;
  submitting: boolean;
  error: string | null;
  // Field names that were filled in by the AI parsing fallback rather than
  // the rule-based parser or the user, so the form can flag them for a
  // closer review instead of implying they're as certain as a manual entry.
  aiFields?: string[];
}

function AIAssistedTag() {
  return (
    <span className="ml-1.5 rounded-full bg-purple-400/15 px-1.5 py-0.5 text-[10px] font-medium text-purple-300 ring-1 ring-purple-400/30">
      AI-assisted
    </span>
  );
}

export function ManualForm({ value, onChange, onSubmit, submitting, error, aiFields = [] }: ManualFormProps) {
  const { catalog } = useCatalog();

  function update<K extends keyof ManualFormValue>(key: K, val: ManualFormValue[K]) {
    onChange({ ...value, [key]: val });
  }

  const isAiField = (field: string) => aiFields.includes(field);

  const selectedMake = catalog?.makes.find((m) => m.name === value.make);
  const models = selectedMake?.models ?? [];
  const selectedModel = models.find((m) => m.name === value.model);

  const matchingGeneration = selectedModel?.generations.find(
    (g) => value.year !== undefined && value.year >= g.start_year && value.year <= g.end_year
  );

  const trimOptions = matchingGeneration
    ? matchingGeneration.trims
    : (selectedModel?.generations.flatMap((g) => g.trims) ?? []);

  const canSubmit =
    value.make &&
    value.model &&
    value.year &&
    value.mileage_km !== undefined &&
    value.price !== undefined &&
    value.transmission &&
    value.seller_rating !== undefined &&
    value.days_listed !== undefined;

  return (
    <Card className="p-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1.5 block text-xs text-muted">
            Make
            {isAiField("make") && <AIAssistedTag />}
          </label>
          <Select
            value={value.make ?? ""}
            onChange={(e) => onChange({ ...value, make: e.target.value || undefined, model: undefined, trim: undefined })}
          >
            <option value="">Select make</option>
            {catalog?.makes.map((make) => (
              <option key={make.id} value={make.name}>
                {make.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">
            Model
            {isAiField("model") && <AIAssistedTag />}
          </label>
          <Select
            value={value.model ?? ""}
            onChange={(e) => onChange({ ...value, model: e.target.value || undefined, trim: undefined })}
            disabled={!value.make}
          >
            <option value="">Select model</option>
            {models.map((model) => (
              <option key={model.id} value={model.name}>
                {model.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">
            Year
            {isAiField("year") && <AIAssistedTag />}
          </label>
          <Input
            type="number"
            placeholder="e.g. 2018"
            value={value.year ?? ""}
            onChange={(e) => update("year", e.target.value ? Number(e.target.value) : undefined)}
            disabled={!value.model}
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Trim (optional)</label>
          <Select value={value.trim ?? ""} onChange={(e) => update("trim", e.target.value || undefined)} disabled={!value.model}>
            <option value="">Any trim</option>
            {trimOptions.map((trim) => (
              <option key={trim.id} value={trim.name}>
                {trim.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">
            Mileage (km)
            {isAiField("mileage_km") && <AIAssistedTag />}
          </label>
          <Input
            type="number"
            placeholder="e.g. 95000"
            value={value.mileage_km ?? ""}
            onChange={(e) => update("mileage_km", e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">
            Price ($)
            {isAiField("price") && <AIAssistedTag />}
          </label>
          <Input
            type="number"
            placeholder="e.g. 15900"
            value={value.price ?? ""}
            onChange={(e) => update("price", e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">
            Transmission
            {isAiField("transmission") && <AIAssistedTag />}
          </label>
          <Select value={value.transmission ?? ""} onChange={(e) => update("transmission", e.target.value || undefined)}>
            <option value="">Select transmission</option>
            {TRANSMISSIONS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">
            Fuel type
            {isAiField("fuel_type") && <AIAssistedTag />}
          </label>
          <Select value={value.fuel_type ?? ""} onChange={(e) => update("fuel_type", e.target.value || undefined)}>
            <option value="">Gasoline (default)</option>
            {FUEL_TYPES.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">
            Title status
            {isAiField("title_status") && <AIAssistedTag />}
          </label>
          <Select
            value={value.title_status ?? ""}
            onChange={(e) => update("title_status", (e.target.value || undefined) as TitleStatus | undefined)}
          >
            <option value="">Clean (default)</option>
            {TITLE_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status[0].toUpperCase() + status.slice(1)}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">
            Location
            {isAiField("location") && <AIAssistedTag />}
          </label>
          <Select value={value.location ?? ""} onChange={(e) => update("location", e.target.value || undefined)}>
            <option value="">Unknown</option>
            {LOCATIONS.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Seller rating (1-5)</label>
          <Input
            type="number"
            min={1}
            max={5}
            step={0.1}
            placeholder="e.g. 4.5"
            value={value.seller_rating ?? ""}
            onChange={(e) => update("seller_rating", e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted">Days listed</label>
          <Input
            type="number"
            placeholder="e.g. 10"
            value={value.days_listed ?? ""}
            onChange={(e) => update("days_listed", e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>
      </div>

      <div className="mt-5">
        <label className="mb-1.5 block text-xs text-muted">Image URL (optional)</label>
        <Input
          type="url"
          placeholder="Paste a photo URL from the listing..."
          value={value.image_url ?? ""}
          onChange={(e) => update("image_url", e.target.value || undefined)}
        />
      </div>

      <div className="mt-5">
        <label className="mb-1.5 block text-xs text-muted">Description (optional)</label>
        <textarea
          className="w-full rounded-xl bg-white/[0.04] border border-white/10 px-4 py-2.5 text-sm text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50 transition-colors"
          rows={3}
          placeholder="Any additional context from the listing..."
          value={value.description_text ?? ""}
          onChange={(e) => update("description_text", e.target.value || undefined)}
        />
      </div>

      {error && <p className="mt-4 text-sm text-[var(--avoid)]">{error}</p>}

      <div className="mt-6 flex justify-end">
        <Button onClick={onSubmit} disabled={!canSubmit || submitting}>
          {submitting ? "Analyzing..." : "Analyze Listing"}
        </Button>
      </div>
    </Card>
  );
}
