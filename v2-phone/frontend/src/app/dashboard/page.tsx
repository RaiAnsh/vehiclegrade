"use client";

import { useState } from "react";

import { StatsGrid } from "@/components/dashboard/StatsGrid";
import { FilterPanel } from "@/components/dashboard/FilterPanel";
import { ListingGrid } from "@/components/dashboard/ListingGrid";
import { ListingModal } from "@/components/dashboard/ListingModal";
import { useDebounce } from "@/hooks/useDebounce";
import { useListings } from "@/hooks/useListings";
import { ListingFilters } from "@/lib/types";

export default function DashboardPage() {
  const [filters, setFilters] = useState<ListingFilters>({});
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const debouncedFilters = useDebounce(filters, 300);
  const { listings, loading } = useListings(debouncedFilters);

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
      <p className="mt-2 text-muted">A live read on today&apos;s iPhone listings and where the deals are.</p>

      <div className="mt-8">
        <StatsGrid />
      </div>

      <div className="mt-8">
        <FilterPanel filters={filters} onChange={setFilters} />
      </div>

      <div className="mt-8">
        <ListingGrid listings={listings} loading={loading} onSelect={setSelectedId} />
      </div>

      <ListingModal listingId={selectedId} onClose={() => setSelectedId(null)} />
    </div>
  );
}
