"""POST /parse-listing - best-effort extraction of structured fields from a
pasted marketplace description, to prefill the manual analyze form. Never
persists anything.
"""

from flask import Blueprint, jsonify, request

from app.models import Location, VehicleMake, VehicleModel
from app.services.listing_parser import parse_listing_text

parse_listing_bp = Blueprint("parse_listing", __name__)


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

    parsed = parse_listing_text(text, makes, models_by_make, location_names)
    return jsonify(parsed)
