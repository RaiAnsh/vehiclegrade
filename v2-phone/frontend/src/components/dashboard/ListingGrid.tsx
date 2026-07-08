"use client";

import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { ListingSummary } from "@/lib/types";
import { ListingCard } from "./ListingCard";

interface ListingGridProps {
  listings: ListingSummary[];
  loading: boolean;
  onSelect: (id: number) => void;
}

export function ListingGrid({ listings, loading, onSelect }: ListingGridProps) {
  if (loading) {
    return (
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} className="p-5">
            <Skeleton className="h-14 w-14 rounded-2xl" />
            <Skeleton className="mt-4 h-6 w-2/3" />
            <Skeleton className="mt-3 h-4 w-full" />
          </Card>
        ))}
      </div>
    );
  }

  if (listings.length === 0) {
    return (
      <Card className="flex flex-col items-center gap-2 p-12 text-center">
        <p className="text-lg font-medium">No listings match your filters</p>
        <p className="text-sm text-muted">Try widening your budget or clearing a filter.</p>
      </Card>
    );
  }

  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {listings.map((listing, index) =>
        listing.id === null ? null : (
          <ListingCard key={listing.id} listing={listing} index={index} onClick={() => onSelect(listing.id as number)} />
        )
      )}
    </div>
  );
}
