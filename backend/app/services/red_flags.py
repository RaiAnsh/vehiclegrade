"""Red Flags: a situational checklist of things that should make a buyer cautious.

Each rule is independent and additive - a listing can trigger any number of
these, from none to all of them.
"""

from app.services.known_issues import evaluate_known_issues
from app.services.mileage_analysis import classify_mileage

OVERPRICED_RATIO = 1.15
LOW_SELLER_RATING = 3.5
STALE_LISTING_DAYS = 30


def evaluate_red_flags(listing, market_value):
    flags = []

    if classify_mileage(listing)["classification"] == "high":
        flags.append(f"Very high mileage for its age ({listing.mileage_km:,} km)")

    if listing.price > market_value * OVERPRICED_RATIO:
        flags.append(f"Priced well above estimated market value (${market_value:,.0f})")

    if listing.title_status == "salvage":
        flags.append("Salvage title - the vehicle was declared a total loss at some point")
    elif listing.title_status == "rebuilt":
        flags.append("Rebuilt title - previously salvaged and repaired")
    elif listing.title_status == "unknown":
        flags.append("Title status not confirmed - ask the seller for documentation")

    if listing.seller_rating < LOW_SELLER_RATING:
        flags.append(f"Below-average seller rating ({listing.seller_rating})")

    if listing.location and listing.location.rust_belt_risk == "high":
        flags.append("High rust-belt region - inspect the frame and rocker panels closely")

    overdue_severe = [
        i for i in evaluate_known_issues(listing)
        if i["status"] == "overdue" and i["severity"] == "severe"
    ]
    if overdue_severe:
        titles = ", ".join(i["title"] for i in overdue_severe)
        flags.append(f"Severe known issue(s) past typical onset mileage: {titles}")

    return flags
