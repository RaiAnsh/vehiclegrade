"""Simple, standalone endpoints for surfacing and reviewing low-confidence
candidate listings.

WHAT "LISTING" MEANS HERE - READ THIS FIRST: the `listings` table itself
has no status or confidence_score column. A row only exists in `listings`
once an admin has already approved it (see app.routes.admin_review) - at
that point it's trusted Gold-layer data with no further review state at
all. The status/confidence concept these two endpoints expose lives one
layer earlier, on `ListingObservation` (the Silver-layer candidate a
listing becomes before - and unless - it's approved):
  - `review_status`  (pending | needs_review | approved | rejected)
  - `quality_score`  (0-100, see app.services.quality_scoring)
are the two existing fields this file is built on - nothing new was
invented for "status" or "confidence", both already existed.

WHY THIS FILE IS SEPARATE FROM app.routes.admin_review: that file is the
richer, existing admin workflow (PATCH-then-approve, duplicate override,
per-field audit trail). This file is a minimal, easy-to-read pair of routes
over the same underlying data, added without changing a single line of
admin_review.py. It still requires the same @require_permission auth as
every other route that can touch review_status, on purpose - that's the one
existing invariant this file does NOT relax: "Nothing outside a
permission-checked admin route may change review_status" (see
ListingObservation's docstring). A note field, once approved does still
materialize a real `Listing` row (mirroring, not calling, admin_review.py's
approve logic, since that function is tightly coupled to its own request/
auth context) - approval is still approval, it still means "this is now
trustworthy enough to become real market data."
"""

from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.extensions import db
from app.models import Listing, ListingObservation
from app.services import audit_log
from app.utils.auth_decorators import require_permission

flagged_listings_bp = Blueprint("flagged_listings", __name__, url_prefix="/api")

DEFAULT_CONFIDENCE_THRESHOLD = 70


def _flagged_public(observation):
    return {
        "id": observation.id,
        "make": observation.make_raw,
        "model": observation.model_raw,
        "year": observation.year,
        "price": observation.price,
        "mileage_km": observation.mileage_km,
        "confidence_score": observation.quality_score,
        "status": observation.review_status,
    }


@flagged_listings_bp.route("/flagged-listings", methods=["GET"])
@require_permission("view")
def get_flagged_listings():
    """?threshold=<int> (default 70) - every observation with quality_score
    strictly below it, regardless of review_status (status is returned so
    the caller can see whether it's still awaiting a decision or already
    resolved), lowest score first.
    """
    threshold = request.args.get("threshold", default=DEFAULT_CONFIDENCE_THRESHOLD, type=int)

    observations = (
        ListingObservation.query
        .filter(ListingObservation.quality_score.isnot(None), ListingObservation.quality_score < threshold)
        .order_by(ListingObservation.quality_score.asc())
        .all()
    )

    return jsonify({
        "threshold": threshold,
        "count": len(observations),
        "flagged_listings": [_flagged_public(o) for o in observations],
    }), 200


@flagged_listings_bp.route("/listings/<int:observation_id>/review", methods=["POST"])
@require_permission("review")
def review_listing(observation_id):
    """{"status": "approved"|"rejected", "note": "..."} - same terminal-state
    and unresolved-gap/duplicate rules app.routes.admin_review enforces, so
    this simpler entry point can't produce a Listing (or a rejected row)
    the main admin workflow would have refused to create.
    """
    observation = ListingObservation.query.get(observation_id)
    if observation is None:
        return jsonify({"error": "Listing not found"}), 404
    if observation.review_status in ("approved", "rejected"):
        return jsonify({"error": f"Already '{observation.review_status}' - cannot review again"}), 400

    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    note = str(payload.get("note") or "").strip()[:2000] or None

    if status not in ("approved", "rejected"):
        return jsonify({"error": "status must be 'approved' or 'rejected'"}), 400

    previous_values = {"review_status": observation.review_status}
    approved_listing_id = None

    if status == "approved":
        if observation.unresolved_fields or observation.validation_errors:
            return jsonify({
                "error": "Cannot approve - unresolved gaps or validation errors remain",
                "unresolved_fields": observation.unresolved_fields,
                "validation_errors": observation.validation_errors,
            }), 400
        if observation.duplicate_of_observation_id:
            return jsonify({
                "error": f"Flagged as a likely duplicate of observation #{observation.duplicate_of_observation_id}",
                "duplicate_of_observation_id": observation.duplicate_of_observation_id,
            }), 400

        listing = Listing(
            generation_id=observation.generation_id, trim_id=observation.trim_id,
            location_id=observation.location_id, year=observation.year,
            mileage_km=observation.mileage_km, price=observation.price,
            transmission=observation.transmission, fuel_type=observation.fuel_type or "Gasoline",
            title_status=observation.title_status or "clean", condition=observation.condition or "good",
            seller_rating=4.0, days_listed=0, source="admin_ingested",
            external_url=observation.external_url,
        )
        db.session.add(listing)
        db.session.flush()
        observation.approved_listing_id = listing.id
        approved_listing_id = listing.id
    else:
        observation.rejection_reason = note or "Rejected via /api/listings/<id>/review"

    observation.review_status = status
    observation.reviewer_note = note
    observation.reviewed_by_id = g.current_user.id
    observation.reviewed_at = datetime.utcnow()
    db.session.flush()

    audit_log.record(
        f"observation.review_{status}", actor=g.current_user, target_type="ListingObservation",
        target_id=observation.id, previous_values=previous_values,
        affected_record_ids=[approved_listing_id] if approved_listing_id else None, request=request,
    )
    db.session.commit()

    return jsonify({
        "id": observation.id,
        "status": observation.review_status,
        "reviewer_note": observation.reviewer_note,
        "approved_listing_id": observation.approved_listing_id,
    }), 200
