import { useEffect, useState } from "react";

import { getListings } from "@/lib/api";
import { ListingFilters, ListingSummary } from "@/lib/types";

export function useListings(filters: ListingFilters) {
  const [listings, setListings] = useState<ListingSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    getListings(filters)
      .then((data) => {
        if (!cancelled) {
          setListings(data.listings);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filters)]);

  return { listings, loading, error };
}
