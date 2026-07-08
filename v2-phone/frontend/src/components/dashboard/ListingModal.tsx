"use client";

import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { DealBadge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { getListing } from "@/lib/api";
import { ListingDetail } from "@/lib/types";
import { DeviceGlyph } from "./DeviceGlyph";
import { ScoreBadge } from "./ScoreBadge";

interface ListingModalProps {
  listingId: number | null;
  onClose: () => void;
}

export function ListingModal({ listingId, onClose }: ListingModalProps) {
  const [detail, setDetail] = useState<ListingDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (listingId === null) {
      setDetail(null);
      return;
    }
    setLoading(true);
    getListing(listingId)
      .then(setDetail)
      .finally(() => setLoading(false));
  }, [listingId]);

  return (
    <Modal open={listingId !== null} onClose={onClose}>
      {loading || !detail ? (
        <div className="space-y-4">
          <Skeleton className="h-14 w-14 rounded-2xl" />
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : (
        <div>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <DeviceGlyph model={detail.model} condition={detail.condition} size={64} />
              <div>
                <h2 className="text-xl font-semibold">
                  {detail.model} <span className="text-muted">{detail.storage_gb}GB</span>
                </h2>
                <p className="text-sm text-muted">{detail.location}</p>
              </div>
            </div>
            <ScoreBadge score={detail.flipiq_score} dealLabel={detail.deal_label} size={64} />
          </div>

          <div className="mt-6 flex items-center gap-3">
            <p className="text-3xl font-semibold">${detail.price.toLocaleString()}</p>
            <DealBadge label={detail.deal_label} />
          </div>

          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              { label: "Battery", value: `${detail.battery_health}%` },
              { label: "Condition", value: detail.condition, capitalize: true },
              { label: "Carrier", value: detail.unlocked ? "Unlocked" : "Locked" },
              { label: "Seller rating", value: `${detail.seller_rating} / 5` },
            ].map((item) => (
              <div key={item.label} className="rounded-xl bg-white/[0.03] p-3">
                <p className="text-xs text-muted">{item.label}</p>
                <p className={`mt-1 text-sm font-medium ${item.capitalize ? "capitalize" : ""}`}>{item.value}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 grid grid-cols-3 gap-4 border-t border-white/5 pt-6">
            <div>
              <p className="text-xs text-muted">Market value</p>
              <p className="text-lg font-medium">${detail.market_value.toLocaleString()}</p>
              <p className="text-xs text-muted">
                {detail.price_vs_market.percent > 0 ? "+" : ""}
                {detail.price_vs_market.percent}% vs. asking price
              </p>
            </div>
            <div>
              <p className="text-xs text-muted">Suggested offer</p>
              <p className="text-lg font-medium">${detail.suggested_offer.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-muted">Estimated flip profit</p>
              <p
                className={`text-lg font-medium ${
                  detail.estimated_profit >= 0 ? "text-[var(--excellent)]" : "text-[var(--avoid)]"
                }`}
              >
                ${detail.estimated_profit.toLocaleString()}
              </p>
            </div>
          </div>

          <div className="mt-6 border-t border-white/5 pt-6">
            <p className="mb-3 text-sm font-medium">Why this score</p>
            <ul className="space-y-2">
              {detail.score_reasons.map((reason) => (
                <li key={reason} className="flex items-start gap-2 text-sm text-muted">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[var(--accent)]" />
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </Modal>
  );
}
