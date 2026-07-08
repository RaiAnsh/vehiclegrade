"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";

import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { VehicleReport } from "@/components/report/VehicleReport";
import { getListing } from "@/lib/api";
import { ListingDetail } from "@/lib/types";

interface ListingDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function ListingDetailPage({ params }: ListingDetailPageProps) {
  const { id } = use(params);
  const [listing, setListing] = useState<ListingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    getListing(Number(id))
      .then((data) => {
        if (!cancelled) {
          setListing(data);
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
  }, [id]);

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <Link href="/dashboard" className="text-sm text-muted hover:text-foreground">
        &larr; Back to dashboard
      </Link>

      <div className="mt-6">
        {loading && (
          <div className="space-y-6">
            <Card className="p-6">
              <Skeleton className="h-6 w-1/3" />
              <Skeleton className="mt-4 h-10 w-2/3" />
              <Skeleton className="mt-3 h-4 w-1/4" />
            </Card>
            <Card className="p-6">
              <Skeleton className="h-32 w-full" />
            </Card>
          </div>
        )}

        {!loading && error && (
          <Card className="p-8 text-center">
            <p className="text-lg font-medium">Couldn&apos;t load this listing</p>
            <p className="mt-2 text-sm text-muted">{error}</p>
          </Card>
        )}

        {!loading && !error && listing && <VehicleReport listing={listing} />}
      </div>
    </div>
  );
}
