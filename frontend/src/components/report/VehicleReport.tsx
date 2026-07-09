import { ListingDetail } from "@/lib/types";
import { ScoreHeader } from "./ScoreHeader";
import { VerdictCard } from "./VerdictCard";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { ValueComparison } from "./ValueComparison";
import { RepairEstimateCard } from "./RepairEstimateCard";
import { AIExplanationCard } from "./AIExplanationCard";
import { ComparableListingsCard } from "./ComparableListingsCard";
import { VehicleSummaryCard } from "./VehicleSummaryCard";
import { ReliabilityCard } from "./ReliabilityCard";
import { KnownIssuesList } from "./KnownIssuesList";
import { MaintenanceTimeline } from "./MaintenanceTimeline";
import { InspectionChecklistCard } from "./InspectionChecklistCard";
import { SellerQuestionsList } from "./SellerQuestionsList";
import { NegotiationAssistant } from "./NegotiationAssistant";
import { RedFlagsList } from "./RedFlagsList";
import { OwnershipCostCard } from "./OwnershipCostCard";
import { ComparableVehiclesCard } from "./ComparableVehiclesCard";

interface VehicleReportProps {
  listing: ListingDetail;
}

// Composes the full vehicle intelligence report. Shared by the listing
// detail page and the analyze result panel so both surfaces render an
// identical report shape. Order runs verdict/confidence up front (is this
// worth it, and how sure are we?), then market pricing + comparables, then
// the supporting reference-data sections, then action items.
export function VehicleReport({ listing }: VehicleReportProps) {
  const { data_sources: sources } = listing;

  return (
    <div className="space-y-6">
      <ScoreHeader listing={listing} />
      <VerdictCard verdict={listing.verdict} source={sources.verdict} />
      {listing.ai_explanation && sources.ai_explanation && (
        <AIExplanationCard explanation={listing.ai_explanation} source={sources.ai_explanation} />
      )}
      <ConfidenceBadge confidence={listing.confidence} source={sources.confidence} />
      <ValueComparison listing={listing} />
      {listing.repair_estimate && sources.repair_estimate && (
        <RepairEstimateCard estimate={listing.repair_estimate} source={sources.repair_estimate} />
      )}
      <ComparableListingsCard comparables={listing.comparable_listings} source={sources.comparable_listings} />

      <div className="grid gap-6 lg:grid-cols-2">
        <VehicleSummaryCard listing={listing} />
        <ReliabilityCard listing={listing} />
      </div>

      <KnownIssuesList issues={listing.known_issues} source={sources.known_issues} />
      <MaintenanceTimeline timeline={listing.maintenance_timeline} source={sources.maintenance_timeline} />
      <InspectionChecklistCard checklist={listing.inspection_checklist} />

      <div className="grid gap-6 lg:grid-cols-2">
        <SellerQuestionsList questions={listing.seller_questions} />
        <NegotiationAssistant negotiation={listing.negotiation} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <RedFlagsList flags={listing.red_flags} />
        <OwnershipCostCard cost={listing.ownership_cost} source={sources.ownership_cost} />
      </div>

      <ComparableVehiclesCard vehicles={listing.comparable_vehicles} source={sources.comparable_vehicles} />
    </div>
  );
}
