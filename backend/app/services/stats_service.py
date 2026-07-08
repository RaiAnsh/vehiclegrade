"""Aggregate data for the dashboard stat cards and analytics charts.

Fields that are plain database columns (price, mileage, location, body
type) are computed with real SQL GROUP BY / AVG / COUNT queries - there's no
reason to pull rows into Python for those. Fields that depend on the VehicleGrade
Score (which is computed, not stored - see deal_engine.py) are aggregated in
Python after scoring each listing, since the rules that produce a score can
change without a schema migration.
"""

from app.extensions import db
from app.models import Generation, Listing, VehicleMake, VehicleModel
from app.services.deal_engine import classify_deal, score_listing
from app.services.serializers import listing_summary

SCORE_BANDS_ORDER = ["Exceptional Buy", "Good Buy", "Fair Deal", "Overpriced", "Avoid"]

# A listing counts toward "top deals today" if it scores well and was listed
# very recently. Mock data has no real "today," so this is documented here
# as "recently listed strong deals" rather than a literal calendar day.
DEAL_SCORE_THRESHOLD = 75
RECENTLY_LISTED_DAYS = 3
TOP_DEALS_LIMIT = 6


def get_dashboard_stats():
    listings = Listing.query.all()

    market_values = []
    scores = []
    score_counts = {band: 0 for band in SCORE_BANDS_ORDER}
    top_deals = []

    for listing in listings:
        score, _reasons, market_value, _breakdown = score_listing(listing)
        market_values.append(market_value)
        scores.append(score)
        score_counts[classify_deal(score)] += 1
        if score >= DEAL_SCORE_THRESHOLD and listing.days_listed <= RECENTLY_LISTED_DAYS:
            top_deals.append((score, listing))

    top_deals.sort(key=lambda pair: pair[0], reverse=True)
    top_deals_today = [listing_summary(listing) for _score, listing in top_deals[:TOP_DEALS_LIMIT]]

    average_market_value = round(sum(market_values) / len(market_values), 2) if market_values else 0
    average_vehiclegrade_score = round(sum(scores) / len(scores), 1) if scores else 0

    return {
        "listings_analyzed": len(listings),
        "average_market_value": average_market_value,
        "average_vehiclegrade_score": average_vehiclegrade_score,
        "average_mileage_km": _average_mileage(),
        "price_by_make": _price_by_make(),
        "price_by_model": _price_by_model(),
        "mileage_vs_price": _mileage_vs_price(),
        "vehicle_distribution": _vehicle_distribution(),
        "top_deals_today": top_deals_today,
        "score_distribution": [{"band": band, "count": score_counts[band]} for band in SCORE_BANDS_ORDER],
    }


def _average_mileage():
    result = db.session.query(db.func.avg(Listing.mileage_km)).scalar()
    return round(result) if result else 0


def _price_by_make():
    rows = (
        db.session.query(VehicleMake.name, db.func.avg(Listing.price))
        .join(VehicleModel, VehicleModel.make_id == VehicleMake.id)
        .join(Generation, Generation.model_id == VehicleModel.id)
        .join(Listing, Listing.generation_id == Generation.id)
        .group_by(VehicleMake.name)
        .order_by(VehicleMake.name)
        .all()
    )
    return [{"make": name, "average_price": round(avg_price, 2)} for name, avg_price in rows]


def _price_by_model():
    rows = (
        db.session.query(VehicleModel.name, db.func.avg(Listing.price))
        .join(Generation, Generation.model_id == VehicleModel.id)
        .join(Listing, Listing.generation_id == Generation.id)
        .group_by(VehicleModel.name)
        .order_by(VehicleModel.name)
        .all()
    )
    return [{"model": name, "average_price": round(avg_price, 2)} for name, avg_price in rows]


def _mileage_vs_price():
    rows = db.session.query(Listing.mileage_km, Listing.price).all()
    return [{"mileage_km": mileage_km, "price": price} for mileage_km, price in rows]


def _vehicle_distribution():
    rows = (
        db.session.query(Generation.body_type, db.func.count(Listing.id))
        .join(Listing, Listing.generation_id == Generation.id)
        .group_by(Generation.body_type)
        .order_by(db.func.count(Listing.id).desc())
        .all()
    )
    return [{"body_type": body_type, "count": count} for body_type, count in rows]
