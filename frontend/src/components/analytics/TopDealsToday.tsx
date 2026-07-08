"use client";

import { DashboardStats } from "@/lib/types";
import { ListingCard } from "@/components/dashboard/ListingCard";

export function TopDealsToday({ data }: { data: DashboardStats["top_deals_today"] }) {
  if (data.length === 0) {
    return <p className="text-sm text-muted">No standout deals right now.</p>;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data.map((listing, index) => (
        <ListingCard key={listing.id} listing={listing} index={index} />
      ))}
    </div>
  );
}
