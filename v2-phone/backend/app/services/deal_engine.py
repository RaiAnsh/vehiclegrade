"""The FlipIQ Score: turns a listing's price (relative to its market value)
plus a handful of risk/negotiation factors into a 0-100 score, a plain-English
explanation, a suggested offer, and an estimated flip profit.

Every point is a rule with a one-line reason - there is no machine learning
here. `score_listing` returns the score alongside `reasons`, so the number
shown to a user can never drift out of sync with the explanation.
"""

from app.services.market_value import estimate_market_value

SCORE_BASE = 50
PRICE_FACTOR_WEIGHT = 1.1
PRICE_FACTOR_CAP = 45

BANDS = [
    (90, "Excellent Buy"),
    (75, "Good Value"),
    (60, "Fair Market"),
    (40, "Slightly Overpriced"),
    (0, "Avoid"),
]

RESALE_FEE_RATE = 0.08
FLIP_OVERHEAD = 10


def score_listing(listing):
    """Score a listing 0-100 and return (score, reasons, market_value, breakdown)."""
    market_value, breakdown = estimate_market_value(listing)

    score = SCORE_BASE
    reasons = []

    # 1. Price vs. market value - the dominant factor.
    percent_below_market = (market_value - listing.price) / market_value * 100
    price_points = max(-PRICE_FACTOR_CAP, min(PRICE_FACTOR_CAP, round(percent_below_market * PRICE_FACTOR_WEIGHT)))
    score += price_points

    if price_points > 0:
        reasons.append(
            f"Priced {abs(round(percent_below_market))}% below its estimated market "
            f"value of ${market_value:.0f} (+{price_points})"
        )
    elif price_points < 0:
        reasons.append(
            f"Priced {abs(round(percent_below_market))}% above its estimated market "
            f"value of ${market_value:.0f} ({price_points})"
        )
    else:
        reasons.append(f"Priced right at its estimated market value of ${market_value:.0f} (+0)")

    # 2. Battery health.
    battery = listing.battery_health
    if battery >= 90:
        score += 10
        reasons.append(f"Strong battery health at {battery}% (+10)")
    elif battery >= 80:
        score += 5
        reasons.append(f"Decent battery health at {battery}% (+5)")
    elif battery >= 70:
        reasons.append(f"Average battery health at {battery}% (+0)")
    else:
        score -= 8
        reasons.append(f"Weak battery health at {battery}%, may need replacement soon (-8)")

    # 3. Condition.
    condition_points = {"excellent": 8, "good": 3, "fair": -3, "poor": -10}.get(listing.condition, 0)
    score += condition_points
    sign = "+" if condition_points >= 0 else ""
    reasons.append(f"Condition is {listing.condition} ({sign}{condition_points})")

    # 4. Unlocked vs. carrier-locked.
    if listing.unlocked:
        score += 5
        reasons.append("Unlocked, works on any carrier (+5)")
    else:
        score -= 3
        reasons.append("Carrier-locked, harder to resell (-3)")

    # 5. Seller rating (risk).
    rating = listing.seller_rating
    if rating >= 4.7:
        score += 6
        reasons.append(f"Highly trusted seller rated {rating} (+6)")
    elif rating >= 4.0:
        score += 2
        reasons.append(f"Solid seller rating of {rating} (+2)")
    elif rating >= 3.0:
        score -= 5
        reasons.append(f"Below-average seller rating of {rating} (-5)")
    else:
        score -= 12
        reasons.append(f"Low seller rating of {rating}, risky purchase (-12)")

    # 6. Days listed - a stale listing means more room to negotiate.
    days = listing.days_listed
    if days >= 25:
        score += 6
        reasons.append(f"Listed for {days} days, seller likely very open to offers (+6)")
    elif days >= 14:
        score += 4
        reasons.append(f"Listed for {days} days, seller may accept a lower offer (+4)")
    elif days >= 7:
        score += 2
        reasons.append(f"Listed for {days} days, some room to negotiate (+2)")

    score = max(0, min(100, round(score)))
    return score, reasons, market_value, breakdown


def classify_deal(score):
    for threshold, label in BANDS:
        if score >= threshold:
            return label
    return "Avoid"


def suggest_offer(listing, market_value):
    """Suggest a reasonable opening offer.

    Fairly-priced listings get a small negotiating discount. Overpriced
    listings get anchored back toward market value, with extra room the
    longer the listing has been sitting.
    """
    if listing.price <= market_value:
        discount = 0.03 + min(0.01 * (listing.days_listed // 7), 0.05)
        offer = listing.price * (1 - discount)
    else:
        weight = 0.6 + min(0.02 * (listing.days_listed // 7), 0.10)
        offer = listing.price - (listing.price - market_value) * weight

    offer = max(50, offer)
    return int(round(offer / 5) * 5)


def estimate_profit(offer, market_value):
    """Estimated profit from buying at `offer` and reselling at market value,
    net of a typical marketplace fee and a flat overhead (packaging, gas,
    meetup time).
    """
    resale_value = market_value * (1 - RESALE_FEE_RATE)
    return round(resale_value - offer - FLIP_OVERHEAD, 2)
