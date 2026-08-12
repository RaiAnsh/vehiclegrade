"""Public, read-only access to the Gold layer (app.models.market_aggregate).

This is deliberately separate from the Market Value Engine
(app.services.market_value, which prices from pure reference data and never
looks at other listings) and from market_comparables.py (which lists
individual comparable listings live, per request). This endpoint answers a
third, distinct question - "what does the real distribution of asking
prices for this generation actually look like, sliced by region/title/
mileage" - from precomputed statistics instead of a live per-request scan.

No auth required: this is the same kind of aggregate market information a
public listing site shows on every search results page, and it never
exposes a raw Listing row or anything PII-adjacent - only counts and
statistics.
"""

from flask import Blueprint, jsonify, request

from app.models import Generation, MarketAggregate
from app.models.market_aggregate import ALL_DIMENSION_VALUE

market_analytics_bp = Blueprint("market_analytics", __name__, url_prefix="/market")


def _aggregate_public(row):
    return {
        "region": None if row.region == ALL_DIMENSION_VALUE else row.region,
        "title_status": None if row.title_status == ALL_DIMENSION_VALUE else row.title_status,
        "mileage_band": None if row.mileage_band == ALL_DIMENSION_VALUE else row.mileage_band,
        "sample_size": row.sample_size,
        "min_price": row.min_price,
        "max_price": row.max_price,
        "avg_price": row.avg_price,
        "median_price": row.median_price,
        "price_p25": row.price_p25,
        "price_p75": row.price_p75,
        "price_stddev": row.price_stddev,
        "avg_mileage_km": row.avg_mileage_km,
        "market_confidence": row.market_confidence,
        "sample_listing_ids": row.sample_listing_ids,
        "computed_at": row.computed_at.isoformat(),
    }


@market_analytics_bp.route("/aggregates", methods=["GET"])
def get_market_aggregates():
    """?generation_id=<id> -> {overall, by_region, by_title_status, by_mileage_band}.

    Every list is empty (not fabricated) when there isn't yet enough
    real market data for that generation - see recompute_generation in
    app.services.market_aggregation, which only ever writes rows it can
    actually support with real Listing rows.
    """
    generation_id = request.args.get("generation_id", type=int)
    if generation_id is None:
        return jsonify({"error": "generation_id query parameter is required"}), 400

    generation = Generation.query.get(generation_id)
    if generation is None:
        return jsonify({"error": "Generation not found"}), 404

    rows = MarketAggregate.query.filter_by(generation_id=generation_id).all()

    overall = None
    by_region, by_title_status, by_mileage_band = [], [], []
    for row in rows:
        if row.region == ALL_DIMENSION_VALUE and row.title_status == ALL_DIMENSION_VALUE and row.mileage_band == ALL_DIMENSION_VALUE:
            overall = _aggregate_public(row)
        elif row.region != ALL_DIMENSION_VALUE:
            by_region.append(_aggregate_public(row))
        elif row.title_status != ALL_DIMENSION_VALUE:
            by_title_status.append(_aggregate_public(row))
        elif row.mileage_band != ALL_DIMENSION_VALUE:
            by_mileage_band.append(_aggregate_public(row))

    return jsonify({
        "generation_id": generation_id,
        "generation_label": f"{generation.model.make.name} {generation.model.name} {generation.label}",
        "overall": overall,
        "by_region": sorted(by_region, key=lambda r: r["region"]),
        "by_title_status": sorted(by_title_status, key=lambda r: r["title_status"]),
        "by_mileage_band": sorted(by_mileage_band, key=lambda r: r["mileage_band"]),
        "disclosure": (
            "Computed from VehicleGrade's admin-approved market observations - refreshed whenever "
            "a listing is approved, rejected, or a batch is rolled back."
        ) if overall else (
            "No approved market observations exist yet for this generation - these statistics "
            "are not fabricated when the sample is empty."
        ),
    }), 200
