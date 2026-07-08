"""The VehicleGrade Score: turns a listing's price (relative to its market value)
plus title status, known-issue risk, mileage-for-age, seller rating, and
days listed into a 0-100 score, a plain-English explanation, and a suggested
opening offer.

Every point is a rule with a one-line reason - there is no machine learning
here. `score_listing` returns the score alongside `reasons`, so the number
shown to a user can never drift out of sync with the explanation.

Unlike the phone version, there's no "estimated flip profit" concept here -
vehicles aren't flipped the same way, so the only value metric beyond the
score is `potential_savings` (market_value - price), computed directly by
the serializer.
"""

from app.services.known_issues import evaluate_known_issues
from app.services.market_value import estimate_market_value
from app.services.mileage_analysis import classify_mileage

SCORE_BASE = 50
PRICE_FACTOR_WEIGHT = 1.1
PRICE_FACTOR_CAP = 45

BANDS = [
    (90, "Exceptional Buy"),
    (75, "Good Buy"),
    (60, "Fair Deal"),
    (40, "Overpriced"),
    (0, "Avoid"),
]

TITLE_POINTS = {"clean": 5, "unknown": -5, "rebuilt": -15, "salvage": -30}
ISSUE_SEVERITY_PENALTY = {"severe": 2, "moderate": 1, "minor": 1}
ISSUE_POINTS_CAP = -15


def _clamp(value, low, high):
    return max(low, min(high, value))


def score_listing(listing):
    """Score a listing 0-100 and return (score, reasons, market_value, breakdown)."""
    market_value, breakdown = estimate_market_value(listing)

    score = SCORE_BASE
    reasons = []

    # 1. Price vs. market value - the dominant factor.
    price_factor = (market_value - listing.price) / market_value
    price_points = _clamp(round(price_factor * 100 * PRICE_FACTOR_WEIGHT), -PRICE_FACTOR_CAP, PRICE_FACTOR_CAP)
    score += price_points

    percent_diff = abs(round(price_factor * 100))
    if price_points > 0:
        reasons.append(f"Priced {percent_diff}% below its estimated market value of ${market_value:.0f} (+{price_points})")
    elif price_points < 0:
        reasons.append(f"Priced {percent_diff}% above its estimated market value of ${market_value:.0f} ({price_points})")
    else:
        reasons.append(f"Priced right at its estimated market value of ${market_value:.0f} (+0)")

    # 2. Title status.
    title_points = TITLE_POINTS.get(listing.title_status, 0)
    score += title_points
    sign = "+" if title_points >= 0 else ""
    reasons.append(f"Title status is {listing.title_status} ({sign}{title_points})")

    # 3. Known-issue risk - penalize issues that are already overdue for this mileage.
    issues = evaluate_known_issues(listing)
    overdue_penalty = -sum(ISSUE_SEVERITY_PENALTY.get(i["severity"], 1) for i in issues if i["status"] == "overdue")
    issue_points = _clamp(overdue_penalty, ISSUE_POINTS_CAP, 0)
    score += issue_points
    overdue_count = sum(1 for i in issues if i["status"] == "overdue")
    if overdue_count:
        reasons.append(f"{overdue_count} known issue(s) past typical onset mileage ({issue_points})")
    else:
        reasons.append("No known issues past typical onset mileage yet (+0)")

    # 4. Mileage relative to expected mileage for the vehicle's age.
    mileage = classify_mileage(listing)
    if mileage["classification"] == "low":
        mileage_points = 8
        reasons.append(f"Lower mileage than typical for its age ({listing.mileage_km:,} km) (+8)")
    elif mileage["classification"] == "high":
        mileage_points = -10
        reasons.append(f"Higher mileage than typical for its age ({listing.mileage_km:,} km) (-10)")
    else:
        mileage_points = 0
        reasons.append(f"Mileage is typical for its age ({listing.mileage_km:,} km) (+0)")
    score += mileage_points

    # 5. Seller rating (risk).
    rating = listing.seller_rating
    if rating >= 4.5:
        rating_points = 6
    elif rating >= 4.0:
        rating_points = 2
    elif rating >= 3.0:
        rating_points = -5
    else:
        rating_points = -12
    score += rating_points
    sign = "+" if rating_points >= 0 else ""
    reasons.append(f"Seller rated {rating} ({sign}{rating_points})")

    # 6. Days listed - a stale listing means more room to negotiate.
    days = listing.days_listed
    if days >= 14:
        days_points = 6
    elif days >= 7:
        days_points = 4
    elif days >= 3:
        days_points = 2
    else:
        days_points = 0
    score += days_points
    if days_points:
        reasons.append(f"Listed for {days} days, room to negotiate (+{days_points})")

    score = _clamp(round(score), 0, 100)
    return score, reasons, market_value, breakdown


def classify_deal(score):
    for threshold, label in BANDS:
        if score >= threshold:
            return label
    return "Avoid"


def suggest_offer(listing, market_value):
    """Suggest a reasonable opening offer.

    Fairly-priced listings get a small negotiating discount. Overpriced
    listings get anchored back toward market value.
    """
    if listing.price <= market_value:
        offer = listing.price - min(listing.price * 0.03, 200)
    else:
        overage = listing.price - market_value
        offer = listing.price - overage * 0.65

    offer = max(500, offer)
    return int(round(offer / 50) * 50)
