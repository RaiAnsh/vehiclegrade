// Mirrors the JSON shapes returned by the FlipIQ Flask API.
// See backend/app/services/serializers.py and stats_service.py.

export type Condition = "excellent" | "good" | "fair" | "poor";

export type DealLabel =
  | "Excellent Buy"
  | "Good Value"
  | "Fair Market"
  | "Slightly Overpriced"
  | "Avoid";

export interface ListingSummary {
  id: number | null;
  model: string;
  storage_gb: number;
  price: number;
  battery_health: number;
  condition: Condition;
  unlocked: boolean;
  location: string | null;
  seller_rating: number;
  days_listed: number;
  market_value: number;
  flipiq_score: number;
  deal_label: DealLabel;
  suggested_offer: number;
  estimated_profit: number;
}

export interface ValueBreakdown {
  base_value: number;
  storage_adjustment: number;
  condition_adjustment: number;
  battery_adjustment: number;
  unlocked_adjustment: number;
  final: number;
}

export interface PriceVsMarket {
  difference: number;
  percent: number;
}

export interface ListingDetail extends ListingSummary {
  score_reasons: string[];
  value_breakdown: ValueBreakdown;
  price_vs_market: PriceVsMarket;
}

export interface ListingsResponse {
  listings: ListingSummary[];
  count: number;
}

export interface DashboardStats {
  listings_analyzed: number;
  average_market_value: number;
  deals_found_today: number;
  average_seller_rating: number;
  price_by_model: { model: string; average_price: number }[];
  battery_by_model: { model: string; average_battery: number }[];
  listings_by_location: { location: string; count: number }[];
  condition_distribution: { condition: Condition; count: number }[];
  storage_distribution: { storage_gb: number; count: number }[];
  score_distribution: { band: DealLabel; count: number }[];
}

export interface ListingFilters {
  model?: string;
  max_price?: number;
  storage?: number;
  battery_min?: number;
  condition?: Condition | "";
  unlocked?: boolean;
  location?: string;
}

export interface AnalyzeInput {
  model: string;
  storage_gb: number;
  price: number;
  battery_health: number;
  condition: Condition;
  unlocked: boolean;
  seller_rating: number;
  days_listed: number;
  location?: string;
}
