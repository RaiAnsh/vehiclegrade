"""POST /analyze - score an arbitrary listing that was never saved to the
database. This powers manual entry: a user can type in the attributes of a
vehicle from any marketplace and get the same full vehicle intelligence
report as a stored listing.
"""

from flask import Blueprint, jsonify, request

from app.models import Generation, Listing, Location, Trim, VehicleMake, VehicleModel
from app.services.serializers import listing_detail

analyze_bp = Blueprint("analyze", __name__)

REQUIRED_FIELDS = [
    "make",
    "model",
    "year",
    "mileage_km",
    "price",
    "transmission",
    "seller_rating",
    "days_listed",
]


@analyze_bp.route("/analyze", methods=["POST"])
def analyze_listing():
    payload = request.get_json(silent=True) or {}

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    make = VehicleMake.query.filter(VehicleMake.name.ilike(payload["make"])).first()
    if make is None:
        supported = [m.name for m in VehicleMake.query.all()]
        return jsonify({"error": f"Unsupported make '{payload['make']}'. Supported: {supported}"}), 400

    model = VehicleModel.query.filter(
        VehicleModel.make_id == make.id, VehicleModel.name.ilike(payload["model"])
    ).first()
    if model is None:
        supported = [m.name for m in VehicleModel.query.filter(VehicleModel.make_id == make.id).all()]
        return jsonify({"error": f"Unsupported model '{payload['model']}' for {make.name}. Supported: {supported}"}), 400

    year = int(payload["year"])
    generation = Generation.query.filter(
        Generation.model_id == model.id,
        Generation.start_year <= year,
        Generation.end_year >= year,
    ).first()
    if generation is None:
        return jsonify({"error": f"No generation of {make.name} {model.name} covers model year {year}."}), 400

    trim = None
    if payload.get("trim"):
        trim = Trim.query.filter(
            Trim.generation_id == generation.id, Trim.name.ilike(payload["trim"])
        ).first()

    location = None
    if payload.get("location"):
        location = Location.query.filter(Location.city.ilike(payload["location"])).first()

    # A transient (never-persisted) Listing - reuses every service exactly
    # the way a real, saved listing would.
    listing = Listing(
        year=year,
        mileage_km=int(payload["mileage_km"]),
        price=float(payload["price"]),
        transmission=payload["transmission"],
        fuel_type=payload.get("fuel_type", "Gasoline"),
        title_status=payload.get("title_status", "clean"),
        condition=payload.get("condition", "good"),
        seller_rating=float(payload["seller_rating"]),
        days_listed=int(payload["days_listed"]),
        description_text=payload.get("description_text"),
        image_url=payload.get("image_url"),
    )
    listing.generation = generation
    listing.trim = trim
    listing.location = location

    # Track which optional fields the user actually left blank, so
    # confidence.py can penalize incomplete manual entries honestly instead
    # of silently defaulting them and pretending the report is fully certain.
    # Trim is scored separately by confidence.py, so it's excluded here.
    completeness_checks = {
        "fuel_type": payload.get("fuel_type"),
        "title_status": payload.get("title_status"),
        "condition": payload.get("condition"),
        "location": payload.get("location"),
        "description_text": payload.get("description_text"),
    }
    missing_optional = [field for field, value in completeness_checks.items() if not value]
    listing._input_completeness_missing = missing_optional
    listing._input_completeness_penalty = min(20, 5 * len(missing_optional))

    return jsonify(listing_detail(listing))
