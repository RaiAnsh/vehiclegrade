"""GET /listings and GET /listing/<id>."""

from flask import Blueprint, jsonify, request

from app.models import Generation, Listing, Location, VehicleMake, VehicleModel
from app.services.serializers import listing_detail, listing_summary

listings_bp = Blueprint("listings", __name__)


def apply_filters(query, filters):
    """Shared by GET /listings (query string) and POST /search (JSON body)."""
    needs_generation_join = any(filters.get(key) for key in ("make", "model", "min_year", "max_year"))
    if needs_generation_join:
        query = query.join(Generation, Listing.generation_id == Generation.id)

    if filters.get("make"):
        query = query.join(VehicleModel, Generation.model_id == VehicleModel.id).join(
            VehicleMake, VehicleModel.make_id == VehicleMake.id
        ).filter(VehicleMake.name.ilike(filters["make"]))

    if filters.get("model"):
        if not filters.get("make"):
            query = query.join(VehicleModel, Generation.model_id == VehicleModel.id)
        query = query.filter(VehicleModel.name.ilike(filters["model"]))

    if filters.get("max_price") is not None:
        query = query.filter(Listing.price <= float(filters["max_price"]))

    if filters.get("max_mileage") is not None:
        query = query.filter(Listing.mileage_km <= int(filters["max_mileage"]))

    if filters.get("min_year") is not None:
        query = query.filter(Listing.year >= int(filters["min_year"]))

    if filters.get("max_year") is not None:
        query = query.filter(Listing.year <= int(filters["max_year"]))

    if filters.get("title_status"):
        query = query.filter(Listing.title_status.ilike(filters["title_status"]))

    if filters.get("transmission"):
        query = query.filter(Listing.transmission.ilike(filters["transmission"]))

    if filters.get("fuel_type"):
        query = query.filter(Listing.fuel_type.ilike(filters["fuel_type"]))

    if filters.get("location"):
        query = query.join(Location, Listing.location_id == Location.id).filter(
            Location.city.ilike(filters["location"])
        )

    return query


def filters_from_request_args(args):
    return {
        "make": args.get("make"),
        "model": args.get("model"),
        "max_price": args.get("max_price"),
        "max_mileage": args.get("max_mileage"),
        "min_year": args.get("min_year"),
        "max_year": args.get("max_year"),
        "title_status": args.get("title_status"),
        "transmission": args.get("transmission"),
        "fuel_type": args.get("fuel_type"),
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
