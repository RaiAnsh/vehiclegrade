// Type shapes for the admin-only API surface (see backend/app/routes/auth.py,
// admin_ingestion.py, admin_review.py, admin_analytics.py, market_analytics.py).
// Kept separate from lib/types.ts since these are never used by the public app.

export type AdminRole = "admin" | "reviewer" | "analyst";

export type AdminPermission = "ingest" | "review" | "rollback" | "manage_users" | "view";

// Mirrors backend/app/models/admin_user.py's ROLE_PERMISSIONS - the backend
// is the actual source of truth/enforcement (every mutating route 403s on
// its own), this copy only drives which buttons the UI bothers to show.
// Keep in sync if the backend map ever changes.
export const ROLE_PERMISSIONS: Record<AdminRole, AdminPermission[]> = {
  admin: ["ingest", "review", "rollback", "manage_users", "view"],
  reviewer: ["ingest", "review", "view"],
  analyst: ["view"],
};

export interface AdminUser {
  id: number;
  email: string;
  role: AdminRole;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  csrf_token: string;
  user: AdminUser;
}

export type BatchSourceType = "paste_single" | "paste_multi" | "csv_upload";
export type BatchStatus = "open" | "processing" | "completed" | "rolled_back";
export type ReviewStatus = "pending" | "needs_review" | "approved" | "rejected";

export interface ObservationCounts {
  pending: number;
  needs_review: number;
  approved: number;
  rejected: number;
}

export interface ImportBatch {
  id: number;
  source_type: BatchSourceType;
  status: BatchStatus;
  original_filename: string | null;
  created_by_id: number;
  created_at: string;
  processed_at: string | null;
  row_count: number;
  notes: string | null;
  observation_counts: ObservationCounts;
}

export interface ListingObservation {
  id: number;
  import_batch_id?: number;
  raw_submission_id: number;
  review_status: ReviewStatus;
  make_raw: string | null;
  model_raw: string | null;
  generation_id: number | null;
  trim_id: number | null;
  location_id: number | null;
  year: number | null;
  mileage_km: number | null;
  price: number | null;
  title_status: string | null;
  condition: string | null;
  transmission: string | null;
  fuel_type: string | null;
  external_url?: string | null;
  duplicate_of_observation_id: number | null;
  quality_score: number | null;
  quality_factors?: { reason: string; points: number }[] | null;
  validation_errors: string[] | null;
  unresolved_fields: string[] | null;
  reviewed_by_id?: number | null;
  reviewed_at?: string | null;
  rejection_reason?: string | null;
  approved_listing_id?: number | null;
}

export interface RawRow {
  id: number;
  sequence_in_batch: number;
  raw_text: string | null;
  raw_row: Record<string, string> | null;
  submitted_at: string;
  observation: ListingObservation | null;
}

export interface BatchRowsResponse {
  batch_id: number;
  rows: RawRow[];
}

export interface BatchListResponse {
  batches: ImportBatch[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface CsvPreviewResponse {
  headers: string[];
  suggested_mapping: Record<string, string | null>;
  sample_rows: Record<string, string>[];
  row_count: number;
  original_filename: string | null;
}

export interface AnalyticsOverview {
  bronze: { import_batches: number; raw_submissions: number };
  silver: {
    total_observations: number;
    by_review_status: Partial<ObservationCounts>;
    duplicate_flagged: number;
    duplicate_rate_pct: number | null;
  };
  gold: {
    total_listings: number;
    admin_ingested_listings: number;
    archived_listings: number;
    generations_with_market_aggregates: number;
  };
  funnel: { approved: number; rejected: number; approval_rate_pct: number | null };
}

export interface MarketAggregateSlice {
  region: string | null;
  title_status: string | null;
  mileage_band: string | null;
  sample_size: number;
  min_price: number;
  max_price: number;
  avg_price: number;
  median_price: number;
  price_p25: number;
  price_p75: number;
  price_stddev: number | null;
  avg_mileage_km: number;
  market_confidence: "low" | "medium" | "high";
  sample_listing_ids: number[] | null;
  computed_at: string;
}

export interface MarketAggregatesResponse {
  generation_id: number;
  generation_label: string;
  overall: MarketAggregateSlice | null;
  by_region: MarketAggregateSlice[];
  by_title_status: MarketAggregateSlice[];
  by_mileage_band: MarketAggregateSlice[];
  disclosure: string;
}

// Mirrors backend/app/services/ingestion_normalizer.py's CSV_TEMPLATE_COLUMNS -
// the canonical fields a CSV column can be mapped to. Keep in sync.
export const CSV_CANONICAL_FIELDS = [
  "year", "make", "model", "trim", "price", "mileage_km", "title_status",
  "condition", "transmission", "fuel_type", "location", "source_identifier", "external_url",
] as const;

// Editable ListingObservation fields for PATCH /admin/observations/<id>
export interface ObservationEdit {
  generation_id?: number | null;
  trim_id?: number | null;
  location_id?: number | null;
  year?: number | null;
  mileage_km?: number | null;
  price?: number | null;
  title_status?: string | null;
  condition?: string | null;
  transmission?: string | null;
  fuel_type?: string | null;
  source_identifier?: string | null;
  external_url?: string | null;
}
