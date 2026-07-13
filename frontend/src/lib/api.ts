// Thin typed fetch wrapper around the VehicleGrade Flask API. Every function here
// maps 1:1 to a backend endpoint - see backend/app/routes/.

import {
  AnalyzeInput,
  Catalog,
  Condition,
  DashboardStats,
  ListingDetail,
  ListingFilters,
  ListingsResponse,
  ParsedListing,
  TitleStatus,
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

export function getCatalog(): Promise<Catalog> {
  return apiFetch<Catalog>("/catalog");
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

export function parseListingText(text: string): Promise<ParsedListing> {
  return apiFetch<ParsedListing>("/parse-listing", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export interface FeedbackInput {
  message: string;
  email?: string;
  category?: string;
  page_url?: string;
}

export function submitFeedback(input: FeedbackInput): Promise<{ status: string }> {
  return apiFetch<{ status: string }>("/feedback", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export interface CommunityComparableInput {
  year: number;
  make: string;
  model: string;
  trim?: string;
  price: number;
  mileage_km: number;
  condition?: Condition;
  title_status?: TitleStatus;
  province?: string;
  city?: string;
  date_observed?: string;
  source_category?: string;
}

export function submitCommunityComparable(input: CommunityComparableInput): Promise<{ status: string }> {
  return apiFetch<{ status: string }>("/community/comparables", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
