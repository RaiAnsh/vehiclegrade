"""Admin-facing pipeline health: Bronze/Silver/Gold record counts, funnel
rates (approval/rejection/duplicate), and a manual full Gold-layer
recompute trigger.

Read-only endpoints require only "view" (analyst included, by design -
seeing pipeline health shouldn't require edit rights). The manual recompute
trigger is scoped to "rollback" - the same tier as the other bulk,
system-wide data-affecting action in this app - since normal operation
never needs it (approve/reject/rollback already recompute the one
generation they touch; this exists for "I changed the aggregation rules,
refresh everything" or a first-time backfill).
"""

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import ImportBatch, Listing, ListingObservation, MarketAggregate, RawListingSubmission
from app.services.market_aggregation import recompute_all_generations, recompute_generation
from app.utils.auth_decorators import require_permission

admin_analytics_bp = Blueprint("admin_analytics", __name__, url_prefix="/admin/analytics")


@admin_analytics_bp.route("/overview", methods=["GET"])
@require_permission("view")
def analytics_overview():
    bronze_batch_count = db.session.query(db.func.count(ImportBatch.id)).scalar()
    bronze_row_count = db.session.query(db.func.count(RawListingSubmission.id)).scalar()

    silver_total = db.session.query(db.func.count(ListingObservation.id)).scalar()
    silver_by_status = dict(
        db.session.query(ListingObservation.review_status, db.func.count(ListingObservation.id))
        .group_by(ListingObservation.review_status)
        .all()
    )

    gold_total = db.session.query(db.func.count(Listing.id)).scalar()
    gold_ingested = db.session.query(db.func.count(Listing.id)).filter(
        Listing.source == "admin_ingested", Listing.is_archived.is_(False),
    ).scalar()
    gold_archived = db.session.query(db.func.count(Listing.id)).filter(Listing.is_archived.is_(True)).scalar()

    duplicate_flagged = db.session.query(db.func.count(ListingObservation.id)).filter(
        ListingObservation.duplicate_of_observation_id.isnot(None)
    ).scalar()

    approved = silver_by_status.get("approved", 0)
    rejected = silver_by_status.get("rejected", 0)
    reviewed = approved + rejected
    approval_rate = round(approved / reviewed * 100, 1) if reviewed else None
    duplicate_rate = round(duplicate_flagged / silver_total * 100, 1) if silver_total else None

    coverage = (
        db.session.query(db.func.count(db.func.distinct(MarketAggregate.generation_id))).scalar()
    )

    return jsonify({
        "bronze": {"import_batches": bronze_batch_count, "raw_submissions": bronze_row_count},
        "silver": {"total_observations": silver_total, "by_review_status": silver_by_status,
                    "duplicate_flagged": duplicate_flagged, "duplicate_rate_pct": duplicate_rate},
        "gold": {"total_listings": gold_total, "admin_ingested_listings": gold_ingested,
                  "archived_listings": gold_archived, "generations_with_market_aggregates": coverage},
        "funnel": {"approved": approved, "rejected": rejected, "approval_rate_pct": approval_rate},
    }), 200


@admin_analytics_bp.route("/recompute", methods=["POST"])
@require_permission("rollback")
def trigger_recompute():
    payload = request.get_json(silent=True) or {}
    generation_id = payload.get("generation_id")

    if generation_id is not None:
        rows_written = recompute_generation(generation_id)
        return jsonify({"generation_id": generation_id, "rows_written": rows_written}), 200

    results = recompute_all_generations()
    return jsonify({
        "generations_recomputed": len(results),
        "total_rows_written": sum(results.values()),
    }), 200
