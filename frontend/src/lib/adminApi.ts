// Admin-only API client. Deliberately separate from lib/api.ts (the public,
// unauthenticated client) rather than a shared generic wrapper - every
// function here needs a Bearer access token, several need multipart/CSV
// bodies instead of JSON, and none of it should ever be reachable from the
// public-facing pages that import lib/api.ts.
//
// Session model: the access token lives only in React state (see
// hooks/useAdminAuth.tsx), never localStorage/sessionStorage - so a hard
// page reload always requires logging in again. This isn't an oversight:
// the backend's CSRF token (required to use the refresh cookie) is
// deliberately returned only in the login/refresh JSON body, never as a
// readable cookie, specifically so it can't be exfiltrated by a
// persisted-storage XSS. Persisting it in localStorage to survive reloads
// would defeat that design. See backend/app/routes/auth.py's docstring.

import {
  AdminUser,
  AnalyticsOverview,
  BatchListResponse,
  BatchRowsResponse,
  BatchSourceType,
  BatchStatus,
  CsvPreviewResponse,
  ImportBatch,
  ListingObservation,
  LoginResponse,
  MarketAggregatesResponse,
  ObservationEdit,
  ReviewStatus,
} from "./adminTypes";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5001";

async function parseErrorBody(response: Response): Promise<Record<string, unknown>> {
  return response.json().catch(() => ({}));
}

async function adminFetch<T>(path: string, token: string | null, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${API_URL}${path}`, { ...options, headers: { ...headers, ...(options?.headers as Record<string, string> | undefined) } });

  if (!response.ok) {
    const body = await parseErrorBody(response);
    const error = new Error((body.error as string) ?? `Request to ${path} failed (${response.status})`);
    (error as Error & { status?: number; body?: Record<string, unknown> }).status = response.status;
    (error as Error & { status?: number; body?: Record<string, unknown> }).body = body;
    throw error;
  }

  return response.json();
}

// A CSV/file upload needs no Content-Type header of its own (the browser
// sets the multipart boundary) and no JSON body, so it can't reuse adminFetch.
async function adminFetchFormData<T>(path: string, token: string | null, formData: FormData): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${API_URL}${path}`, { method: "POST", headers, body: formData });
  if (!response.ok) {
    const body = await parseErrorBody(response);
    throw new Error((body.error as string) ?? `Request to ${path} failed (${response.status})`);
  }
  return response.json();
}

// --- Auth (cookie-authenticated calls need credentials: "include") ---

export async function adminLogin(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error ?? "Login failed");
  return body;
}

export async function adminRefresh(csrfToken: string): Promise<LoginResponse> {
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Token": csrfToken },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error ?? "Session refresh failed");
  return body;
}

export async function adminLogout(): Promise<void> {
  await fetch(`${API_URL}/auth/logout`, { method: "POST", credentials: "include" }).catch(() => {
    // Best-effort - the client clears its own state regardless of whether
    // this call succeeds (e.g. the refresh cookie may already be gone).
  });
}

export function getMe(token: string): Promise<AdminUser> {
  return adminFetch<AdminUser>("/auth/me", token);
}

export function listUsers(token: string): Promise<{ users: AdminUser[] }> {
  return adminFetch<{ users: AdminUser[] }>("/auth/users", token);
}

export function createUser(
  token: string,
  input: { email: string; password: string; role: string }
): Promise<AdminUser> {
  return adminFetch<AdminUser>("/auth/users", token, { method: "POST", body: JSON.stringify(input) });
}

export function deactivateUser(token: string, userId: number): Promise<AdminUser> {
  return adminFetch<AdminUser>(`/auth/users/${userId}/deactivate`, token, { method: "POST" });
}

// --- Ingestion (Bronze) ---

export function createImportBatch(
  token: string,
  input: { source_type: BatchSourceType; notes?: string; column_mapping?: Record<string, string | null>; original_filename?: string }
): Promise<ImportBatch> {
  return adminFetch<ImportBatch>("/admin/import-batches", token, { method: "POST", body: JSON.stringify(input) });
}

export function addPasteRows(token: string, batchId: number, texts: string[]): Promise<{ batch: ImportBatch; rows_added: number }> {
  return adminFetch(`/admin/import-batches/${batchId}/rows`, token, {
    method: "POST",
    body: JSON.stringify({ texts }),
  });
}

export function addCsvRows(
  token: string,
  batchId: number,
  rows: Record<string, string>[]
): Promise<{ batch: ImportBatch; rows_added: number }> {
  return adminFetch(`/admin/import-batches/${batchId}/rows`, token, { method: "POST", body: JSON.stringify({ rows }) });
}

export function processBatch(token: string, batchId: number): Promise<ImportBatch> {
  return adminFetch<ImportBatch>(`/admin/import-batches/${batchId}/process`, token, { method: "POST" });
}

export function getBatch(token: string, batchId: number): Promise<ImportBatch> {
  return adminFetch<ImportBatch>(`/admin/import-batches/${batchId}`, token);
}

export function listBatches(token: string, page = 1, status?: BatchStatus): Promise<BatchListResponse> {
  const params = new URLSearchParams({ page: String(page), per_page: "25" });
  if (status) params.set("status", status);
  return adminFetch<BatchListResponse>(`/admin/import-batches?${params.toString()}`, token);
}

export function listBatchRows(token: string, batchId: number, reviewStatus?: ReviewStatus): Promise<BatchRowsResponse> {
  const query = reviewStatus ? `?review_status=${reviewStatus}` : "";
  return adminFetch<BatchRowsResponse>(`/admin/import-batches/${batchId}/rows${query}`, token);
}

export function previewCsv(token: string, file: File): Promise<CsvPreviewResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return adminFetchFormData<CsvPreviewResponse>("/admin/import-batches/csv-preview", token, formData);
}

export function csvTemplateUrl(): string {
  return `${API_URL}/admin/import-batches/csv-template`;
}

export function rejectedExportUrl(batchId: number): string {
  return `${API_URL}/admin/import-batches/${batchId}/rejected/export`;
}

// --- Review (Silver -> Gold) ---

export function updateObservation(token: string, observationId: number, edit: ObservationEdit): Promise<ListingObservation> {
  return adminFetch<ListingObservation>(`/admin/observations/${observationId}`, token, {
    method: "PATCH",
    body: JSON.stringify(edit),
  });
}

export function approveObservation(token: string, observationId: number, overrideDuplicate = false): Promise<ListingObservation> {
  return adminFetch<ListingObservation>(`/admin/observations/${observationId}/approve`, token, {
    method: "POST",
    body: JSON.stringify({ override_duplicate: overrideDuplicate }),
  });
}

export function rejectObservation(token: string, observationId: number, reason: string): Promise<ListingObservation> {
  return adminFetch<ListingObservation>(`/admin/observations/${observationId}/reject`, token, {
    method: "POST",
    body: JSON.stringify({ rejection_reason: reason }),
  });
}

export interface RollbackResult {
  batch_id: number;
  status: string;
  observations_rejected: number;
  listings_archived: number[];
}

export function rollbackBatch(token: string, batchId: number): Promise<RollbackResult> {
  return adminFetch<RollbackResult>(`/admin/import-batches/${batchId}/rollback`, token, { method: "POST" });
}

// --- Analytics (Gold) ---

export function getAnalyticsOverview(token: string): Promise<AnalyticsOverview> {
  return adminFetch<AnalyticsOverview>("/admin/analytics/overview", token);
}

export function triggerRecompute(token: string, generationId?: number): Promise<Record<string, number>> {
  return adminFetch("/admin/analytics/recompute", token, {
    method: "POST",
    body: JSON.stringify(generationId ? { generation_id: generationId } : {}),
  });
}

export function getMarketAggregates(token: string, generationId: number): Promise<MarketAggregatesResponse> {
  return adminFetch<MarketAggregatesResponse>(`/market/aggregates?generation_id=${generationId}`, token);
}
