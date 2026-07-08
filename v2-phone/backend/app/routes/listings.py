"""GET /listings and GET /listing/<id>."""

from flask import Blueprint, jsonify, request

from app.models import Listing, PhoneModel, Location
from app.services.serializers import listing_detail, listing_summary

listings_bp = Blueprint("listings", __name__)


def apply_filters(query, filters):
    """Shared by GET /listings (query string) and POST /search (JSON body)."""
    if filters.get("model"):
        query = query.join(PhoneModel).filter(PhoneModel.name.ilike(filters["model"]))

    if filters.get("max_price") is not None:
        query = query.filter(Listing.price <= float(filters["max_price"]))

    if filters.get("storage") is not None:
        query = query.filter(Listing.storage_gb == int(filters["storage"]))

    if filters.get("battery_min") is not None:
        query = query.filter(Listing.battery_health >= int(filters["battery_min"]))

    if filters.get("condition"):
        query = query.filter(Listing.condition.ilike(filters["condition"]))

    if filters.get("unlocked") is not None:
        unlocked = str(filters["unlocked"]).lower() == "true"
        query = query.filter(Listing.unlocked == unlocked)

    if filters.get("location"):
        query = query.join(Location).filter(Location.city.ilike(filters["location"]))

    return query


def filters_from_request_args(args):
    return {
        "model": args.get("model"),
        "max_price": args.get("max_price"),
        "storage": args.get("storage"),
        "battery_min": args.get("battery_min"),
        "condition": args.get("condition"),
        "unlocked": args.get("unlocked"),
        "location": args.get("location"),
    }


@listings_bp.route("/listings", methods=["GET"])
def get_listings():
    filters = filters_from_request_args(request.args)
    query = apply_filters(Listing.query, filters)
    listings = query.all()

    return jsonify({"listings": [listing_summary(listing) for listing in listings], "count": len(listings)})


@listings_bp.route("/listing/<int:listing_id>", methods=["GET"])
def get_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    return jsonify(listing_detail(listing))
