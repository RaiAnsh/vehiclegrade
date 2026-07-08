"""Deal scoring, offer suggestions, and plain-English explanations.

The score starts at a neutral 50 and moves up or down based on simple,
explainable rules. It is always clamped to the 0-100 range.
"""

# Points awarded for each condition level.
CONDITION_POINTS = {
    "excellent": 10,
    "good": 5,
    "fair": 0,
    "poor": -10,
}


def score_listing(listing, model_averages):
    """Score a listing out of 100 and return (score, list_of_reasons)."""
    score = 50
    reasons = []

    # 1. Price vs. the average for the same model (the biggest factor).
    average = model_averages[listing["model"]]
    percent_below_average = (average - listing["price"]) / average * 100
    # 1 point per percent below average, capped at +/-25.
    price_points = max(-25, min(25, round(percent_below_average)))
    score += price_points

    if price_points > 0:
        reasons.append(
            f"Priced {abs(round(percent_below_average))}% below the "
            f"{listing['model']} average of ${average:.0f} (+{price_points})"
        )
    elif price_points < 0:
        reasons.append(
            f"Priced {abs(round(percent_below_average))}% above the "
            f"{listing['model']} average of ${average:.0f} ({price_points})"
        )
    else:
        reasons.append(f"Priced right at the {listing['model']} average (+0)")

    # 2. Battery health.
    battery = listing["battery_health"]
    if battery >= 90:
        score += 10
        reasons.append(f"Strong battery health at {battery}% (+10)")
    elif battery >= 80:
        score += 5
        reasons.append(f"Decent battery health at {battery}% (+5)")
    else:
        score -= 5
        reasons.append(f"Weak battery health at {battery}%, may need replacement (-5)")

    # 3. Unlocked phones are worth more and easier to resell.
    if listing["unlocked"]:
        score += 10
        reasons.append("Unlocked, works on any carrier (+10)")
    else:
        reasons.append("Carrier-locked, harder to resell (+0)")

    # 4. Physical condition.
    condition_points = CONDITION_POINTS.get(listing["condition"], 0)
    score += condition_points
    sign = "+" if condition_points >= 0 else ""
    reasons.append(f"Condition is {listing['condition']} ({sign}{condition_points})")

    # 5. Listings sitting for 2+ weeks mean the seller may accept a lower offer.
    if listing["days_listed"] >= 14:
        score += 5
        reasons.append(
            f"Listed for {listing['days_listed']} days, seller likely open to offers (+5)"
        )

    # 6. Seller trustworthiness.
    rating = listing["seller_rating"]
    if rating >= 4.5:
        score += 5
        reasons.append(f"Trusted seller rated {rating} (+5)")
    elif rating < 3.5:
        score -= 10
        reasons.append(f"Low seller rating of {rating}, risky purchase (-10)")

    # Keep the final score within 0-100.
    score = max(0, min(100, score))
    return score, reasons


def classify_deal(score):
    """Turn a numeric score into a simple verdict."""
    if score >= 70:
        return "GOOD DEAL"
    if score >= 45:
        return "FAIR DEAL"
    return "OVERPRICED"


def suggest_offer(listing, model_averages):
    """Suggest a reasonable offer price for a listing.

    Start with a 5% discount, add 1% for every week the listing has been up
    (stale listings have more room to negotiate), and never offer more than
    the model's average price.
    """
    discount = 0.05 + 0.01 * (listing["days_listed"] // 7)
    discount = min(discount, 0.15)  # never lowball more than 15%

    offer = listing["price"] * (1 - discount)
    offer = min(offer, model_averages[listing["model"]])

    # Round to the nearest $5 so the offer looks natural in a message.
    return int(round(offer / 5) * 5)
