"""POST /analyze - score an arbitrary listing that was never saved to the
database. This powers the "paste a listing you found elsewhere" feature:
a user can type in the attributes of a phone from any marketplace and get
the same market value / score / offer / reasoning as a stored listing.
"""

from flask import Blueprint, jsonify, request

from app.models import Listing, Location, PhoneModel
from app.services.serializers import listing_detail

analyze_bp = Blueprint("analyze", __name__)

REQUIRED_FIELDS = [
    "model",
    "storage_gb",
    "price",
    "battery_health",
    "condition",
    "unlocked",
    "seller_rating",
    "days_listed",
]


@analyze_bp.route("/analyze", methods=["POST"])
def analyze_listing():
    payload = request.get_json(silent=True) or {}

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    phone_model = PhoneModel.query.filter(PhoneModel.name.ilike(payload["model"])).first()
    if phone_model is None:
        supported = [m.name for m in PhoneModel.query.all()]
        return jsonify({"error": f"Unsupported model '{payload['model']}'. Supported: {supported}"}), 400

    # A transient (never-persisted) Listing - reuses every service exactly
    # the way a real, saved listing would.
    listing = Listing(
        storage_gb=payload["storage_gb"],
        price=payload["price"],
        battery_health=payload["battery_health"],
        condition=payload["condition"],
        unlocked=bool(payload["unlocked"]),
        seller_rating=payload["seller_rating"],
        days_listed=payload["days_listed"],
    )
    listing.model = phone_model
    listing.location = Location.query.filter(Location.city.ilike(payload.get("location", ""))).first()

    return jsonify(listing_detail(listing))
