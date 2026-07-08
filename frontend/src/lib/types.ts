// Mirrors the JSON shapes returned by the VehicleGrade Flask API.
// See backend/app/services/serializers.py and stats_service.py.

export type TitleStatus = "clean" | "rebuilt" | "salvage" | "unknown";

export type DealLabel =
  | "Exceptional Buy"
  | "Good Buy"
  | "Fair Deal"
  | "Overpriced"
  | "Avoid";

export type IssueSeverity = "minor" | "moderate" | "severe";

export type IssueStatus = "not_yet_relevant" | "approaching" | "common_now" | "overdue";

export type Condition = "excellent" | "good" | "fair" | "poor";

export type DataSourceType = "reference_data" | "market_sample" | "estimate";

export interface DataSourceInfo {
  source: DataSourceType;
  label: string;
}

export type ConfidenceLevel = "high" | "medium" | "low";

export interface ConfidenceFactor {
  reason: string;
  points: number;
}

export interface Confidence {
  score: number;
  level: ConfidenceLevel;
  factors: ConfidenceFactor[];
  missing_data: string[];
}

export interface ComparableListing {
  price: number;
  mileage_km: number;
  title_status: TitleStatus;
  condition: Condition;
  location: string | null;
  days_listed: number;
}

export interface ComparableListingsSummary {
  count: number;
  avg_price: number | null;
  median_price: number | null;
  min_price: number | null;
  max_price: number | null;
  price_percentile: number | null;
  band_applied: boolean;
  comparables: ComparableListing[];
  source: "market_sample";
  disclosure: string;
}

export type VerdictRecommendation = "Recommended" | "Consider" | "Avoid";

export interface Verdict {
  recommendation: VerdictRecommendation;
  paragraph: string;
}

export type MileageClassification = "low" | "typical" | "high";

export interface MileageAnalysis {
  vehicle_age_years: number;
  expected_km: number;
  ratio: number;
  classification: MileageClassification;
  explanation: string;
}

export interface ComparableVehicle {
  name: string;
  has_data: boolean;
}

export interface ListingSummary {
  id: number | null;
  year: number;
  make: string;
  model: string;
  trim: string | null;
  generation_label: string;
  body_type: string;
  mileage_km: number;
  price: number;
  location: string | null;
  transmission: string;
  fuel_type: string;
  title_status: TitleStatus;
  condition: Condition;
  seller_rating: number;
  days_listed: number;
  market_value: number;
  vehiclegrade_score: number;
  score_stars: number;
  deal_label: DealLabel;
  suggested_offer: number;
  potential_savings: number;
}

export interface ValueBreakdown {
  base_value: number;
  trim_adjustment: number;
  mileage_adjustment: number;
  title_adjustment: number;
  condition_adjustment: number;
  final: number;
}

export interface VehicleSummary {
  engine: string | null;
  fuel_type: string;
  fuel_economy_l_per_100km: number;
  drivetrain: string;
  horsepower: number;
  common_competitors: string | null;
}

export interface Reliability {
  stars: number;
  expected_annual_maintenance_cost: number;
  typical_lifespan_km: number;
  parts_availability: "excellent" | "good" | "fair" | "poor";
  insurance_category: "low" | "medium" | "high";
}

export interface KnownIssue {
  title: string;
  description: string;
  severity: IssueSeverity;
  status: IssueStatus;
  status_copy: string;
  typical_mileage_km: number;
  estimated_repair_cost_min: number;
  estimated_repair_cost_max: number;
  symptoms: string | null;
  recommendation: string;
}

export interface MaintenanceTimelineItem {
  name: string;
  interval_km: number;
  due_in_km: number;
  estimated_cost_min: number | null;
  estimated_cost_max: number | null;
}

export interface MaintenanceTimeline {
  immediate: MaintenanceTimelineItem[];
  soon: MaintenanceTimelineItem[];
  future: MaintenanceTimelineItem[];
}

export interface Negotiation {
  suggested_offer: number;
  reasoning: string;
  message: string;
}

export interface OwnershipCost {
  fuel_annual: number;
  insurance_annual: number;
  maintenance_annual: number;
  total_annual: number;
}

export interface ListingDetail extends ListingSummary {
  score_reasons: string[];
  value_breakdown: ValueBreakdown;
  vehicle_summary: VehicleSummary;
  reliability: Reliability;
  known_issues: KnownIssue[];
  maintenance_timeline: MaintenanceTimeline;
  seller_questions: string[];
  negotiation: Negotiation;
  red_flags: string[];
  ownership_cost: OwnershipCost;
  mileage_analysis: MileageAnalysis;
  comparable_listings: ComparableListingsSummary;
  comparable_vehicles: ComparableVehicle[];
  confidence: Confidence;
  verdict: Verdict;
  inspection_checklist: string[];
  data_sources: Record<string, DataSourceInfo>;
}

export interface ListingsResponse {
  listings: ListingSummary[];
  count: number;
}

export interface DashboardStats {
  listings_analyzed: number;
  average_market_value: number;
  average_vehiclegrade_score: number;
  average_mileage_km: number;
  price_by_make: { make: string; average_price: number }[];
  price_by_model: { model: string; average_price: number }[];
  mileage_vs_price: { mileage_km: number; price: number }[];
  vehicle_distribution: { body_type: string; count: number }[];
  top_deals_today: ListingSummary[];
  score_distribution: { band: DealLabel; count: number }[];
}

export interface ListingFilters {
  make?: string;
  model?: string;
  max_price?: number;
  max_mileage?: number;
  min_year?: number;
  max_year?: number;
  title_status?: TitleStatus | "";
  transmission?: string;
  fuel_type?: string;
  location?: string;
}

export interface CatalogTrim {
  id: number;
  name: string;
}

export interface CatalogGeneration {
  id: number;
  label: string;
  start_year: number;
  end_year: number;
  body_type: string;
  trims: CatalogTrim[];
}

export interface CatalogModel {
  id: number;
  name: string;
  generations: CatalogGeneration[];
}

export interface CatalogMake {
  id: number;
  name: string;
  models: CatalogModel[];
}

export interface Catalog {
  makes: CatalogMake[];
}

export interface AnalyzeInput {
  make: string;
  model: string;
  year: number;
  trim?: string;
  mileage_km: number;
  price: number;
  transmission: string;
  fuel_type?: string;
  title_status?: TitleStatus;
  condition?: Condition;
  seller_rating: number;
  days_listed: number;
  location?: string;
  description_text?: string;
}

export interface ParsedListing {
  year?: number;
  make?: string;
  model?: string;
  price?: number;
  mileage_km?: number;
  title_status?: TitleStatus;
  transmission?: string;
  fuel_type?: string;
  location?: string;
}
