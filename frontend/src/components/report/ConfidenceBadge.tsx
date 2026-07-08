"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { SourceBadge } from "./SourceBadge";
import { Confidence, ConfidenceLevel, DataSourceInfo } from "@/lib/types";

const LEVEL_COLOR: Record<ConfidenceLevel, string> = {
  high: "var(--good)",
  medium: "var(--fair)",
  low: "var(--avoid)",
};

const LEVEL_LABEL: Record<ConfidenceLevel, string> = {
  high: "High Confidence",
  medium: "Medium Confidence",
  low: "Low Confidence",
};

interface ConfidenceBadgeProps {
  confidence: Confidence;
  source: DataSourceInfo;
}

// Surfaces exactly how sure the report is of its own numbers, and - critically
// - names what's missing rather than silently defaulting it. This is the
// "if information is missing or confidence is low, say so instead of
// guessing" requirement made visible.
export function ConfidenceBadge({ confidence, source }: ConfidenceBadgeProps) {
  const [expanded, setExpanded] = useState(false);
  const color = LEVEL_COLOR[confidence.level];

  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            className="rounded-full px-3 py-1 text-xs font-medium"
            style={{ backgroundColor: `${color}26`, color }}
          >
            {LEVEL_LABEL[confidence.level]}
          </span>
          <span className="text-sm text-muted">{confidence.score}/100</span>
          <SourceBadge {...source} />
        </div>
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          className="text-xs text-muted underline underline-offset-2"
        >
          {expanded ? "Hide details" : "Why?"}
        </button>
      </div>

      {confidence.missing_data.length > 0 && (
        <p className="mt-3 text-sm text-muted">
          Missing data: {confidence.missing_data.join(", ")}
        </p>
      )}

      {expanded && (
        <ul className="mt-4 space-y-1.5 border-t border-white/5 pt-4 text-sm">
          {confidence.factors.map((factor, i) => (
            <li key={i} className="flex items-center justify-between gap-3">
              <span className="text-muted">{factor.reason}</span>
              <span className={factor.points < 0 ? "text-[var(--avoid)]" : "text-[var(--good)]"}>
                {factor.points > 0 ? "+" : ""}
                {factor.points}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
