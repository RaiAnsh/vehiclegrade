"use client";

import { useState } from "react";

import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Toggle } from "@/components/ui/Toggle";
import { Button } from "@/components/ui/Button";
import { AnalyzeInput, Condition } from "@/lib/types";

const MODELS = ["iPhone 11", "iPhone 12", "iPhone 13", "iPhone 14", "iPhone 15"];
const STORAGE_TIERS = [64, 128, 256, 512];
const CONDITIONS: Condition[] = ["excellent", "good", "fair", "poor"];

const DEFAULT_INPUT: AnalyzeInput = {
  model: "iPhone 13",
  storage_gb: 128,
  price: 400,
  battery_health: 88,
  condition: "good",
  unlocked: true,
  seller_rating: 4.5,
  days_listed: 5,
};

interface AnalyzeFormProps {
  onSubmit: (input: AnalyzeInput) => void;
  loading: boolean;
}

export function AnalyzeForm({ onSubmit, loading }: AnalyzeFormProps) {
  const [input, setInput] = useState<AnalyzeInput>(DEFAULT_INPUT);

  function update<K extends keyof AnalyzeInput>(key: K, value: AnalyzeInput[K]) {
    setInput((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <Card className="p-6">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(input);
        }}
        className="space-y-5"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-xs text-muted">Model</label>
            <Select value={input.model} onChange={(e) => update("model", e.target.value)}>
              {MODELS.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="mb-1.5 block text-xs text-muted">Storage</label>
            <Select value={input.storage_gb} onChange={(e) => update("storage_gb", Number(e.target.value))}>
              {STORAGE_TIERS.map((tier) => (
                <option key={tier} value={tier}>
                  {tier}GB
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="mb-1.5 block text-xs text-muted">Asking price</label>
            <Input
              type="number"
              value={input.price}
              onChange={(e) => update("price", Number(e.target.value))}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs text-muted">Battery health (%)</label>
            <Input
              type="number"
              min={0}
              max={100}
              value={input.battery_health}
              onChange={(e) => update("battery_health", Number(e.target.value))}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs text-muted">Condition</label>
            <Select value={input.condition} onChange={(e) => update("condition", e.target.value as Condition)}>
              {CONDITIONS.map((condition) => (
                <option key={condition} value={condition}>
                  {condition[0].toUpperCase() + condition.slice(1)}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="mb-1.5 block text-xs text-muted">Seller rating</label>
            <Input
              type="number"
              min={1}
              max={5}
              step={0.1}
              value={input.seller_rating}
              onChange={(e) => update("seller_rating", Number(e.target.value))}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs text-muted">Days listed</label>
            <Input
              type="number"
              min={0}
              value={input.days_listed}
              onChange={(e) => update("days_listed", Number(e.target.value))}
            />
          </div>

          <div className="flex items-end">
            <Toggle checked={input.unlocked} onChange={(checked) => update("unlocked", checked)} label="Unlocked" />
          </div>
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze listing"}
        </Button>
      </form>
    </Card>
  );
}
