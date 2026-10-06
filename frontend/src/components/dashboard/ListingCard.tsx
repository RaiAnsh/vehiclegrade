"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";

import { Card } from "@/components/ui/Card";
import { DealBadge } from "@/components/ui/Badge";
import { ListingSummary } from "@/lib/types";
import { VehicleGlyph } from "./VehicleGlyph";
import { ScoreBadge } from "./ScoreBadge";

interface ListingCardProps {
  listing: ListingSummary;
  index?: number;
}

// Hands this listing to the flip calculator at the suggested offer. Built as
// query params (not state) so it works as a plain link from any page.
function flipHref(listing: ListingSummary) {
  const params = new URLSearchParams({
    make: listing.make,
    model: listing.model,
    year: String(listing.year),
    mileage: String(listing.mileage_km),
    price: String(Math.round(listing.suggested_offer)),
    title: listing.title_status,
    condition: listing.condition,
  });
  if (listing.trim) params.set("trim", listing.trim);
  return `/flip?${params.toString()}`;
}

export function ListingCard({ listing, index = 0 }: ListingCardProps) {
  if (listing.id === null) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: Math.min(index * 0.04, 0.4) }}
      whileHover={{ y: -4 }}
    >
      <Link href={`/listing/${listing.id}`}>
        <Card className="cursor-pointer p-5 transition-shadow hover:shadow-[0_0_32px_-8px_var(--accent-soft)]">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {listing.image_url ? (
                <Image
                  src={listing.image_url}
                  alt={`${listing.year} ${listing.make} ${listing.model}`}
                  width={48}
                  height={48}
                  unoptimized
                  className="h-12 w-12 rounded-lg object-cover"
                />
              ) : (
                <VehicleGlyph bodyType={listing.body_type} titleStatus={listing.title_status} />
              )}
              <div>
                <p className="font-medium">
                  {listing.year} {listing.make} {listing.model}
                  {listing.trim ? <span className="text-muted"> {listing.trim}</span> : null}
                </p>
                <p className="text-sm text-muted">{listing.location ?? "Unknown location"}</p>
              </div>
            </div>
            <ScoreBadge score={listing.vehiclegrade_score} dealLabel={listing.deal_label} />
          </div>

          <div className="mt-4 flex items-center justify-between">
            <p className="text-2xl font-semibold">${listing.price.toLocaleString()}</p>
            <DealBadge label={listing.deal_label} />
          </div>

          <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-muted">
            <div>
              <p className="text-foreground">{listing.mileage_km.toLocaleString()} km</p>
              <p>Mileage</p>
            </div>
            <div>
              <p className="text-foreground">{listing.transmission}</p>
              <p>Transmission</p>
            </div>
            <div>
              <p className="text-foreground capitalize">{listing.title_status}</p>
              <p>Title</p>
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
              <p className="text-muted">Potential savings</p>
              <p
                className={`font-medium ${
                  listing.potential_savings >= 0 ? "text-[var(--excellent)]" : "text-[var(--avoid)]"
                }`}
              >
                ${listing.potential_savings.toLocaleString()}
              </p>
            </div>
          </div>
        </Card>
      </Link>
      <Link
        href={flipHref(listing)}
        className="mt-2 block text-right text-xs text-muted transition-colors hover:text-foreground"
      >
        Run flip numbers at the suggested offer &rarr;
      </Link>
    </motion.div>
  );
}
