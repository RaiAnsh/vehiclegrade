"""Silver -> Gold: the ONLY place a ListingObservation's review_status may
change, and the ONLY place a ListingObservation is ever materialized into a
real Listing row (which is what market_comparables.py, stats_service.py,
and confidence.py already query - approval requires zero changes to any of
those services).

PATCH lets a reviewer correct/fill in a gap (wrong make match, missing
trim, mistyped price, etc.) - after any edit the row is fully re-validated
and re-checked for duplicates using the exact same rules ingestion_normalizer
used at parse time, so a manual fix can't accidentally skip a check a pasted
listing would have been held to.

Approval is blocked on ANY remaining unresolved_fields/validation_errors, and
on an unacknowledged duplicate flag - this is what makes "unreviewed or
incomplete data can never influence a user-facing market estimate" an
enforced invariant instead of a convention. Rollback never hard-deletes a
materialized Listing (which could already have been read into a historical
report) - it archives it (is_archived=True), reusing the exact mechanism
Listing already has for "sold/removed, exclude from comparables math".
"""

from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.extensions import db
from app.models import ImportBatch, Listing, ListingObservation
from app.models.listing import VALID_TITLE_STATUSES
from app.services import audit_log
from app.services.duplicate_detection import find_duplicate
from app.services.ingestion_normalizer import MAX_MILEAGE_KM, MAX_PRICE, MIN_YEAR, VALID_CONDITIONS
from app.services.quality_scoring import score_observation
from app.utils.auth_decorators import require_permission

admin_review_bp = Blueprint("admin_review", __name__, url_prefix="/admin")

EDITABLE_FIELDS = (
    "generation_id", "trim_id", "location_id", "year", "mileage_km", "price",
    "title_status", "condition", "transmission", "fuel_type", "source_identifier", "external_url",
)


def _observation_public(observation):
    return {
        "id": observation.id,
        "import_batch_id": observation.import_batch_id,
        "raw_submission_id": observation.raw_submission_id,
        "review_status": observation.review_status,
        "make_raw": observation.make_raw,
        "model_raw": observation.model_raw,
        "generation_id": observation.generation_id,
        "trim_id": observation.trim_id,
        "location_id": observation.location_id,
        "year": observation.year,
        "mileage_km": observation.mileage_km,
        "price": observation.price,
        "title_status": observation.title_status,
        "condition": observation.condition,
        "transmission": observation.transmission,
        "fuel_type": observation.fuel_type,
        "external_url": observation.external_url,
        "duplicate_of_observation_id": observation.duplicate_of_observation_id,
        "quality_score": observation.quality_score,
        "quality_factors": observation.quality_factors,
        "validation_errors": observation.validation_errors,
        "unresolved_fields": observation.unresolved_fields,
        "reviewed_by_id": observation.reviewed_by_id,
        "reviewed_at": observation.reviewed_at.isoformat() if observation.reviewed_at else None,
        "rejection_reason": observation.rejection_reason,
        "approved_listing_id": observation.approved_listing_id,
    }


def _revalidate(observation):
    """Re-runs the same presence/range/duplicate checks ingestion_normalizer
    applies at parse time, against an observation's CURRENT (possibly just
    manually-edited) resolved fields. Trim/location are still optional (many
    real listings never mention either) - only the fields that make a
    vehicle/price identifiable at all are required for `pending`.
    """
    unresolved_fields = []
    validation_errors = []

    if observation.generation_id is None:
        unresolved_fields.append("generation")

    if observation.year is None:
        unresolved_fields.append("year")
    elif not (MIN_YEAR <= observation.year <= datetime.utcnow().year + 1):
        validation_errors.append("year")

    if observation.price is None:
        unresolved_fields.append("price")
    elif not (0 < observation.price <= MAX_PRICE):
        validation_errors.append("price")

    if observation.mileage_km is None:
        unresolved_fields.append("mileage_km")
    elif not (0 <= observation.mileage_km <= MAX_MILEAGE_KM):
        validation_errors.append("mileage_km")

    if observation.title_status is None:
        unresolved_fields.append("title_status")
    elif observation.title_status not in VALID_TITLE_STATUSES:
        validation_errors.append("title_status")

    if observation.transmission is None:
        unresolved_fields.append("transmission")

    if observation.fuel_type is None:
        unresolved_fields.append("fuel_type")

    if observation.condition is not None and observation.condition not in VALID_CONDITIONS:
        validation_errors.append("condition")

    duplicate, duplicate_reason = find_duplicate(
        {"generation_id": observation.generation_id, "year": observation.year,
         "price": observation.price, "mileage_km": observation.mileage_km},
        url_hash=observation.url_hash, source_identifier=observation.source_identifier,
        exclude_observation_id=observation.id,
    )
    observation.duplicate_of_observation_id = duplicate.id if duplicate else None

    observation.quality_score, observation.quality_factors = score_observation(
        validation_errors, unresolved_fields, duplicate is not None, duplicate_reason
    )
    observation.quality_factors = observation.quality_factors or None
    observation.validation_errors = validation_errors or None
    observation.unresolved_fields = unresolved_fields or None
    observation.review_status = "needs_review" if (validation_errors or unresolved_fields or duplicate) else "pending"


@admin_review_bp.route("/observations/<int:observation_id>", methods=["PATCH"])
@require_permission("review")
def update_observation(observation_id):
    observation = ListingObservation.query.get(observation_id)
    if observation is None:
        return jsonify({"error": "Observation not found"}), 404
    if observation.review_status in ("approved", "rejected"):
        return jsonify({"error": f"Observation is already '{observation.review_status}' and can no longer be edited"}), 400

    payload = request.get_json(silent=True) or {}
    previous_values = {}
    for field in EDITABLE_FIELDS:
        if field in payload:
            previous_values[field] = getattr(observation, field)
            setattr(observation, field, payload[field])

    _revalidate(observation)
    db.session.flush()

    audit_log.record(
        "observation.update", actor=g.current_user, target_type="ListingObservation", target_id=observation.id,
        previous_values=previous_values or None, request=request,
    )
    db.session.commit()

    return jsonify(_observation_public(observation)), 200


@admin_review_bp.route("/observations/<int:observation_id>/approve", methods=["POST"])
@require_permission("review")
def approve_observation(observation_id):
    observation = ListingObservation.query.get(observation_id)
    if observation is None:
        return jsonify({"error": "Observation not found"}), 404
    if observation.review_status in ("approved", "rejected"):
        return jsonify({"error": f"Observation is already '{observation.review_status}'"}), 400
    if observation.unresolved_fields or observation.validation_errors:
        return jsonify({
            "error": "Cannot approve - unresolved gaps or validation errors remain",
            "unresolved_fields": observation.unresolved_fields,
            "validation_errors": observation.validation_errors,
        }), 400

    payload = request.get_json(silent=True) or {}
    if observation.duplicate_of_observation_id and not payload.get("override_duplicate"):
        return jsonify({
            "error": f"Flagged as a likely duplicate of observation #{observation.duplicate_of_observation_id} - "
                     f"pass override_duplicate: true to approve anyway",
            "duplicate_of_observation_id": observation.duplicate_of_observation_id,
        }), 400

    listing = Listing(
        generation_id=observation.generation_id,
        trim_id=observation.trim_id,
        location_id=observation.location_id,
        year=observation.year,
        mileage_km=observation.mileage_km,
        price=observation.price,
        transmission=observation.transmission,
        fuel_type=observation.fuel_type or "Gasoline",
        title_status=observation.title_status or "clean",
        condition=observation.condition or "good",
        # Market-observation rows carry no live seller/listing-age signal the
        # way a manually-analyzed listing does - these are neutral
        # placeholders, never read by comparables/scoring math itself.
        seller_rating=4.0,
        days_listed=0,
        description_text=observation.raw_submission.raw_text if observation.raw_submission else None,
        source="admin_ingested",
        external_url=observation.external_url,
    )
    db.session.add(listing)
    db.session.flush()

    previous_values = {"review_status": observation.review_status}
    observation.review_status = "approved"
    observation.approved_listing_id = listing.id
    observation.reviewed_by_id = g.current_user.id
    observation.reviewed_at = datetime.utcnow()
    db.session.flush()

    audit_log.record(
        "observation.approve", actor=g.current_user, target_type="ListingObservation", target_id=observation.id,
        previous_values=previous_values, affected_record_ids=[listing.id], request=request,
    )
    db.session.commit()

    return jsonify(_observation_public(observation)), 200


@admin_review_bp.route("/observations/<int:observation_id>/reject", methods=["POST"])
@require_permission("review")
def reject_observation(observation_id):
    observation = ListingObservation.query.get(observation_id)
    if observation is None:
        return jsonify({"error": "Observation not found"}), 404
    if observation.review_status in ("approved", "rejected"):
        return jsonify({"error": f"Observation is already '{observation.review_status}'"}), 400

    payload = request.get_json(silent=True) or {}
    rejection_reason = str(payload.get("rejection_reason") or "").strip()
    if not rejection_reason:
        return jsonify({"error": "rejection_reason is required"}), 400

    previous_values = {"review_status": observation.review_status}
    observation.review_status = "rejected"
    observation.rejection_reason = rejection_reason[:2000]
    observation.reviewed_by_id = g.current_user.id
    observation.reviewed_at = datetime.utcnow()
    db.session.flush()

    audit_log.record(
        "observation.reject", actor=g.current_user, target_type="ListingObservation", target_id=observation.id,
        previous_values=previous_values, request=request,
    )
    db.session.commit()

    return jsonify(_observation_public(observation)), 200


@admin_review_bp.route("/import-batches/<int:batch_id>/rollback", methods=["POST"])
@require_permission("rollback")
def rollback_batch(batch_id):
    batch = ImportBatch.query.get(batch_id)
    if batch is None:
        return jsonify({"error": "Import batch not found"}), 404
    if batch.status == "rolled_back":
        return jsonify({"error": "Batch has already been rolled back"}), 400

    affected_observation_ids = []
    archived_listing_ids = []

    for observation in ListingObservation.query.filter_by(import_batch_id=batch.id).all():
        if observation.review_status == "rejected":
            continue

        if observation.review_status == "approved" and observation.approved_listing_id:
            listing = Listing.query.get(observation.approved_listing_id)
            if listing is not None and not listing.is_archived:
                listing.is_archived = True
                archived_listing_ids.append(listing.id)

        observation.review_status = "rejected"
        observation.rejection_reason = "Import batch rolled back by admin"
        observation.reviewed_by_id = g.current_user.id
        observation.reviewed_at = datetime.utcnow()
        affected_observation_ids.append(observation.id)

    previous_values = {"status": batch.status}
    batch.status = "rolled_back"
    db.session.flush()

    audit_log.record(
        "import_batch.rollback", actor=g.current_user, target_type="ImportBatch", target_id=batch.id,
        previous_values=previous_values, affected_record_ids=affected_observation_ids, request=request,
    )
    db.session.commit()

    return jsonify({
        "batch_id": batch.id,
        "status": batch.status,
        "observations_rejected": len(affected_observation_ids),
        "listings_archived": archived_listing_ids,
    }), 200
