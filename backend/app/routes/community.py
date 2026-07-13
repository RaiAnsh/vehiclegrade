"""POST /community/comparables - anonymous, opt-in contribution of a
comparable listing a user observed elsewhere (not one they're analyzing).

Write-only for now: there is no GET/list endpoint yet, and contributed rows
aren't read by any scoring/comparables logic until a person has reviewed a
sufficient sample - see CommunityComparable.is_reviewed. Every incoming key
is manually whitelisted against a fixed set of structured fields; anything
else in the payload is silently ignored rather than stored, since the whole
point of this table is that it has no free-text/PII-capable column at all.
"""

from datetime import date, datetime

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import CommunityComparable
from app.models.listing import VALID_TITLE_STATUSES

community_bp = Blueprint("community", __name__)

VALID_CONDITIONS = {"excellent", "good", "fair", "poor"}
VALID_SOURCE_CATEGORIES = {"marketplace", "dealer", "auction", "other"}

REQUIRED_FIELDS = ("year", "make", "model", "price", "mileage_km")


@community_bp.route("/community/comparables", methods=["POST"])
def submit_community_comparable():
    payload = request.get_json(silent=True) or {}

    missing = [field for field in REQUIRED_FIELDS if payload.get(field) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}), 400

    try:
        year = int(payload["year"])
        price = float(payload["price"])
        mileage_km = int(payload["mileage_km"])
    except (TypeError, ValueError):
        return jsonify({"error": "year, price, and mileage_km must be numeric"}), 400

    condition = payload.get("condition") or "good"
    if condition not in VALID_CONDITIONS:
        return jsonify({"error": f"condition must be one of: {', '.join(sorted(VALID_CONDITIONS))}"}), 400

    title_status = payload.get("title_status") or "unknown"
    if title_status not in VALID_TITLE_STATUSES:
        return jsonify({"error": f"title_status must be one of: {', '.join(VALID_TITLE_STATUSES)}"}), 400

    source_category = payload.get("source_category")
    if source_category is not None and source_category not in VALID_SOURCE_CATEGORIES:
        source_category = "other"

    date_observed = None
    raw_date = payload.get("date_observed")
    if raw_date:
        try:
            date_observed = date.fromisoformat(raw_date)
        except ValueError:
            return jsonify({"error": "date_observed must be an ISO date (YYYY-MM-DD)"}), 400

    comparable = CommunityComparable(
        year=year,
        make=str(payload["make"]).strip()[:50],
        model=str(payload["model"]).strip()[:50],
        trim=(str(payload.get("trim") or "").strip()[:30] or None),
        price=price,
        mileage_km=mileage_km,
        condition=condition,
        title_status=title_status,
        province=(str(payload.get("province") or "").strip()[:30] or None),
        city=(str(payload.get("city") or "").strip()[:80] or None),
        date_observed=date_observed,
        source_category=source_category,
        submitted_at=datetime.utcnow(),
    )
    db.session.add(comparable)
    db.session.commit()

    return jsonify({"status": "received"}), 201
