"""The Market Value Engine.

Estimates what a vehicle is objectively worth based on its generation's
knowledge-base entry, trim, mileage, and title status. It deliberately
ignores asking price, seller rating, and days listed, because those describe
the *listing*, not the *vehicle*. That separation is what lets the VehicleGrade
Score (see deal_engine.py) compare an asking price against a genuinely
independent baseline instead of circularly comparing price to price.

All adjustments are plain percentages - no machine learning, every dollar
traces back to one of the rules below.
"""

TITLE_STATUS_ADJUSTMENTS = {
    "clean": 0.0,
    "unknown": -0.10,
    "rebuilt": -0.20,
    "salvage": -0.45,
}

CONDITION_ADJUSTMENTS = {
    "excellent": 0.05,
    "good": 0.0,
    "fair": -0.08,
    "poor": -0.20,
}

MILEAGE_ADJUSTMENT_RATE = 0.000004  # pct value change per km away from reference
MILEAGE_ADJUSTMENT_CAP = (-0.35, 0.15)


def estimate_market_value(listing):
    """Return (market_value, breakdown) for a listing.

    `listing` only needs `.generation` (with `.base_value` and
    `.reference_mileage_km`), `.trim` (optional), `.mileage_km`,
    `.title_status`, and `.condition` (optional, defaults to "good") - it
    does not need to be persisted, which is what lets POST /analyze reuse
    this on listings that were never saved to the database.
    """
    generation = listing.generation
    base_value = generation.base_value

    mileage_delta = generation.reference_mileage_km - listing.mileage_km  # + if lower mileage than reference
    mileage_adjustment = mileage_delta * MILEAGE_ADJUSTMENT_RATE
    mileage_adjustment = max(MILEAGE_ADJUSTMENT_CAP[0], min(MILEAGE_ADJUSTMENT_CAP[1], mileage_adjustment))

    trim_adjustment = listing.trim.msrp_adjustment_pct if listing.trim else 0.0
    title_adjustment = TITLE_STATUS_ADJUSTMENTS.get(listing.title_status, 0.0)
    condition_adjustment = CONDITION_ADJUSTMENTS.get(getattr(listing, "condition", "good"), 0.0)

    market_value = (
        base_value
        * (1 + trim_adjustment)
        * (1 + mileage_adjustment)
        * (1 + title_adjustment)
        * (1 + condition_adjustment)
    )

    breakdown = {
        "base_value": round(base_value, 2),
        "trim_adjustment": trim_adjustment,
        "mileage_adjustment": round(mileage_adjustment, 4),
        "title_adjustment": title_adjustment,
        "condition_adjustment": condition_adjustment,
        "final": round(market_value, 2),
    }

    return round(market_value, 2), breakdown
