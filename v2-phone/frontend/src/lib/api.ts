// Thin typed fetch wrapper around the FlipIQ Flask API. Every function here
// maps 1:1 to a backend endpoint - see backend/app/routes/.

import {
  AnalyzeInput,
  DashboardStats,
  ListingDetail,
  ListingFilters,
  ListingsResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5001";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error ?? `Request to ${path} failed (${response.status})`);
  }

  return response.json();
}

function buildQueryString(filters: ListingFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "" && value !== null) {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function getListings(filters: ListingFilters = {}): Promise<ListingsResponse> {
  return apiFetch<ListingsResponse>(`/listings${buildQueryString(filters)}`);
}

export function getListing(id: number): Promise<ListingDetail> {
  return apiFetch<ListingDetail>(`/listing/${id}`);
}

export function getStats(): Promise<DashboardStats> {
  return apiFetch<DashboardStats>("/stats");
}

export function searchListings(filters: ListingFilters): Promise<ListingsResponse> {
  return apiFetch<ListingsResponse>("/search", {
    method: "POST",
    body: JSON.stringify(filters),
  });
}

export function analyzeListing(input: AnalyzeInput): Promise<ListingDetail> {
  return apiFetch<ListingDetail>("/analyze", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
