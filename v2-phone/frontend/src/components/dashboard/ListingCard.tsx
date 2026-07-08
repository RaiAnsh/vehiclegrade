"use client";

import { motion } from "framer-motion";

import { Card } from "@/components/ui/Card";
import { DealBadge } from "@/components/ui/Badge";
import { ListingSummary } from "@/lib/types";
import { DeviceGlyph } from "./DeviceGlyph";
import { ScoreBadge } from "./ScoreBadge";

interface ListingCardProps {
  listing: ListingSummary;
  onClick: () => void;
  index?: number;
}

export function ListingCard({ listing, onClick, index = 0 }: ListingCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: Math.min(index * 0.04, 0.4) }}
      whileHover={{ y: -4 }}
    >
      <Card
        onClick={onClick}
        className="cursor-pointer p-5 transition-shadow hover:shadow-[0_0_32px_-8px_var(--accent-soft)]"
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <DeviceGlyph model={listing.model} condition={listing.condition} />
            <div>
              <p className="font-medium">
                {listing.model} <span className="text-muted">{listing.storage_gb}GB</span>
              </p>
              <p className="text-sm text-muted">{listing.location}</p>
            </div>
          </div>
          <ScoreBadge score={listing.flipiq_score} dealLabel={listing.deal_label} />
        </div>

        <div className="mt-4 flex items-center justify-between">
          <p className="text-2xl font-semibold">${listing.price.toLocaleString()}</p>
          <DealBadge label={listing.deal_label} />
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-muted">
          <div>
            <p className="text-foreground">{listing.battery_health}%</p>
            <p>Battery</p>
          </div>
          <div>
            <p className="text-foreground capitalize">{listing.condition}</p>
            <p>Condition</p>
          </div>
          <div>
            <p className="text-foreground">{listing.unlocked ? "Unlocked" : "Locked"}</p>
            <p>Carrier</p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2 border-t border-white/5 pt-4 text-xs">
          <div>
            <p className="text-muted">Market value</p>
            <p className="font-medium">${listing.market_value.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-muted">Suggested offer</p>
            <p className="font-medium">${listing.suggested_offer.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-muted">Flip profit</p>
            <p className={`font-medium ${listing.estimated_profit >= 0 ? "text-[var(--excellent)]" : "text-[var(--avoid)]"}`}>
              ${listing.estimated_profit.toLocaleString()}
            </p>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
