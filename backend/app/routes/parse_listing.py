"""POST /parse-listing - best-effort extraction of structured fields from a
pasted marketplace description, to prefill the manual analyze form. Never
persists anything.
"""

from flask import Blueprint, jsonify, request

from app.models import Location, VehicleMake, VehicleModel
from app.services.listing_parser import parse_listing_text
from app.services.listing_parser_llm import parse_missing_fields

parse_listing_bp = Blueprint("parse_listing", __name__)

# All fields either parser can populate - used to figure out what's still
# missing after the rule-based pass, for the AI fallback to attempt.
ALL_PARSEABLE_FIELDS = [
    "year", "make", "model", "price", "mileage_km",
    "title_status", "transmission", "fuel_type", "location",
]


@parse_listing_bp.route("/parse-listing", methods=["POST"])
def parse_listing():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    if not text.strip():
        return jsonify({"error": "Missing required field: text"}), 400

    makes = [m.name for m in VehicleMake.query.all()]
    models_by_make = {}
    for make in VehicleMake.query.all():
        models_by_make[make.name] = [m.name for m in VehicleModel.query.filter(VehicleModel.make_id == make.id).all()]
    location_names = [loc.city for loc in Location.query.all()]

    # Rule-based parser always runs first and always wins - the AI fallback
    # (no-op if no LLM is configured) is only ever consulted about fields
    # that are still missing after this.
    parsed = parse_listing_text(text, makes, models_by_make, location_names)

    missing_fields = [field for field in ALL_PARSEABLE_FIELDS if field not in parsed]
    ai_fields = parse_missing_fields(text, missing_fields, makes, models_by_make, location_names)
    for field, value in ai_fields.items():
        parsed[field] = value

    if ai_fields:
        parsed["_fields_from_ai"] = list(ai_fields.keys())

    return jsonify(parsed)
