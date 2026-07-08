"use client";

import { motion } from "framer-motion";

import { Card } from "@/components/ui/Card";
import { DealBadge } from "@/components/ui/Badge";
import { DeviceGlyph } from "@/components/dashboard/DeviceGlyph";
import { ScoreBadge } from "@/components/dashboard/ScoreBadge";
import { ListingDetail } from "@/lib/types";

export function AnalyzeResult({ result }: { result: ListingDetail }) {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      <Card className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <DeviceGlyph model={result.model} condition={result.condition} size={64} />
            <div>
              <h2 className="text-xl font-semibold">
                {result.model} <span className="text-muted">{result.storage_gb}GB</span>
              </h2>
              <p className="text-sm text-muted">{result.unlocked ? "Unlocked" : "Locked"}</p>
            </div>
          </div>
          <ScoreBadge score={result.flipiq_score} dealLabel={result.deal_label} size={64} />
        </div>

        <div className="mt-6 flex items-center gap-3">
          <p className="text-3xl font-semibold">${result.price.toLocaleString()}</p>
          <DealBadge label={result.deal_label} />
        </div>

        <div className="mt-6 grid grid-cols-3 gap-4 border-t border-white/5 pt-6">
          <div>
            <p className="text-xs text-muted">Market value</p>
            <p className="text-lg font-medium">${result.market_value.toLocaleString()}</p>
            <p className="text-xs text-muted">
              {result.price_vs_market.percent > 0 ? "+" : ""}
              {result.price_vs_market.percent}% vs. asking price
            </p>
          </div>
          <div>
            <p className="text-xs text-muted">Suggested offer</p>
            <p className="text-lg font-medium">${result.suggested_offer.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted">Estimated flip profit</p>
            <p
              className={`text-lg font-medium ${
                result.estimated_profit >= 0 ? "text-[var(--excellent)]" : "text-[var(--avoid)]"
              }`}
            >
              ${result.estimated_profit.toLocaleString()}
            </p>
          </div>
        </div>

        <div className="mt-6 border-t border-white/5 pt-6">
          <p className="mb-3 text-sm font-medium">Why this score</p>
          <ul className="space-y-2">
            {result.score_reasons.map((reason) => (
              <li key={reason} className="flex items-start gap-2 text-sm text-muted">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[var(--accent)]" />
                {reason}
              </li>
            ))}
          </ul>
        </div>
      </Card>
    </motion.div>
  );
}
