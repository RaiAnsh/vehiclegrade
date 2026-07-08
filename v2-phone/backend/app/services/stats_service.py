"""Aggregate data for the dashboard stat cards and analytics charts.

Fields that are plain database columns (price, battery, condition, storage,
seller rating, location) are computed with real SQL GROUP BY / AVG / COUNT
queries - there's no reason to pull rows into Python for those. Fields that
depend on the FlipIQ Score (which is computed, not stored - see
deal_engine.py) are aggregated in Python after scoring each listing, since
the rules that produce a score can change without a schema migration.
"""

from app.extensions import db
from app.models import Listing, PhoneModel, Location
from app.services.deal_engine import classify_deal, score_listing
from app.services.market_value import estimate_market_value

SCORE_BANDS_ORDER = ["Excellent Buy", "Good Value", "Fair Market", "Slightly Overpriced", "Avoid"]

# A listing counts toward "deals found today" if it scores well and was
# listed very recently. Mock data has no real "today," so this is documented
# here as "recently listed strong deals" rather than a literal calendar day.
DEAL_SCORE_THRESHOLD = 75
RECENTLY_LISTED_DAYS = 3


def get_dashboard_stats():
    listings = Listing.query.all()

    market_values = []
    score_counts = {band: 0 for band in SCORE_BANDS_ORDER}
    deals_found_today = 0

    for listing in listings:
        score, _reasons, market_value, _breakdown = score_listing(listing)
        market_values.append(market_value)
        score_counts[classify_deal(score)] += 1
        if score >= DEAL_SCORE_THRESHOLD and listing.days_listed <= RECENTLY_LISTED_DAYS:
            deals_found_today += 1

    average_market_value = round(sum(market_values) / len(market_values), 2) if market_values else 0

    return {
        "listings_analyzed": len(listings),
        "average_market_value": average_market_value,
        "deals_found_today": deals_found_today,
        "average_seller_rating": _average_seller_rating(),
        "price_by_model": _price_by_model(),
        "battery_by_model": _battery_by_model(),
        "listings_by_location": _listings_by_location(),
        "condition_distribution": _condition_distribution(),
        "storage_distribution": _storage_distribution(),
        "score_distribution": [{"band": band, "count": score_counts[band]} for band in SCORE_BANDS_ORDER],
    }


def _average_seller_rating():
    result = db.session.query(db.func.avg(Listing.seller_rating)).scalar()
    return round(result, 2) if result else 0


def _price_by_model():
    rows = (
        db.session.query(PhoneModel.name, db.func.avg(Listing.price))
        .join(Listing, Listing.model_id == PhoneModel.id)
        .group_by(PhoneModel.name)
        .order_by(PhoneModel.name)
        .all()
    )
    return [{"model": name, "average_price": round(avg_price, 2)} for name, avg_price in rows]


def _battery_by_model():
    rows = (
        db.session.query(PhoneModel.name, db.func.avg(Listing.battery_health))
        .join(Listing, Listing.model_id == PhoneModel.id)
        .group_by(PhoneModel.name)
        .order_by(PhoneModel.name)
        .all()
    )
    return [{"model": name, "average_battery": round(avg_battery, 1)} for name, avg_battery in rows]


def _listings_by_location():
    rows = (
        db.session.query(Location.city, db.func.count(Listing.id))
        .join(Listing, Listing.location_id == Location.id)
        .group_by(Location.city)
        .order_by(db.func.count(Listing.id).desc())
        .all()
    )
    return [{"location": city, "count": count} for city, count in rows]


def _condition_distribution():
    rows = (
        db.session.query(Listing.condition, db.func.count(Listing.id))
        .group_by(Listing.condition)
        .all()
    )
    order = {"excellent": 0, "good": 1, "fair": 2, "poor": 3}
    rows = sorted(rows, key=lambda row: order.get(row[0], 99))
    return [{"condition": condition, "count": count} for condition, count in rows]


def _storage_distribution():
    rows = (
        db.session.query(Listing.storage_gb, db.func.count(Listing.id))
        .group_by(Listing.storage_gb)
        .order_by(Listing.storage_gb)
        .all()
    )
    return [{"storage_gb": storage_gb, "count": count} for storage_gb, count in rows]
