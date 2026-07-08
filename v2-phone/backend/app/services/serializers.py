"""Turns a Listing (persisted or not) plus computed deal data into the plain
dicts returned by the API. Kept separate from the routes so every endpoint
that returns a listing - GET /listings, GET /listing/:id, POST /analyze,
POST /search - produces an identical, consistent shape.
"""

from app.services.deal_engine import classify_deal, estimate_profit, score_listing, suggest_offer


def _base_fields(listing, score, market_value, offer):
    return {
        "id": listing.id,
        "model": listing.model.name,
        "storage_gb": listing.storage_gb,
        "price": listing.price,
        "battery_health": listing.battery_health,
        "condition": listing.condition,
        "unlocked": listing.unlocked,
        "location": listing.location.city if listing.location else None,
        "seller_rating": listing.seller_rating,
        "days_listed": listing.days_listed,
        "market_value": market_value,
        "flipiq_score": score,
        "deal_label": classify_deal(score),
        "suggested_offer": offer,
        "estimated_profit": estimate_profit(offer, market_value),
    }


def listing_summary(listing):
    """The fields shown on a listing card / list row."""
    score, _reasons, market_value, _breakdown = score_listing(listing)
    offer = suggest_offer(listing, market_value)
    return _base_fields(listing, score, market_value, offer)


def listing_detail(listing):
    """The full detail shown in the listing modal / analyze result."""
    score, reasons, market_value, breakdown = score_listing(listing)
    offer = suggest_offer(listing, market_value)

    detail = _base_fields(listing, score, market_value, offer)
    detail["score_reasons"] = reasons
    detail["value_breakdown"] = breakdown
    detail["price_vs_market"] = {
        "difference": round(listing.price - market_value, 2),
        "percent": round((listing.price - market_value) / market_value * 100, 1),
    }
    return detail
