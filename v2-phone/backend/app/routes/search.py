"""POST /search - identical filtering to GET /listings, but via a JSON body.

Kept as its own endpoint (rather than just reusing GET) so a future "saved
searches" feature has a natural place to persist a filter payload.
"""

from flask import Blueprint, jsonify, request

from app.models import Listing
from app.routes.listings import apply_filters
from app.services.serializers import listing_summary

search_bp = Blueprint("search", __name__)


@search_bp.route("/search", methods=["POST"])
def search_listings():
    filters = request.get_json(silent=True) or {}
    query = apply_filters(Listing.query, filters)
    listings = query.all()

    return jsonify({"listings": [listing_summary(listing) for listing in listings], "count": len(listings)})
