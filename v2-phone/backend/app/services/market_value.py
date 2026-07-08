"""The Market Value Engine.

Estimates what a phone is objectively worth based on its attributes alone -
model, storage, condition, battery health, and lock status. It deliberately
ignores price, seller rating, and days listed, because those describe the
*listing*, not the *phone*. That separation is what lets the FlipIQ Score
(see deal_engine.py) compare an asking price against a genuinely independent
baseline instead of circularly comparing price to price.

All adjustments are plain percentages - no machine learning, every dollar
traces back to one of the rules below.
"""

STORAGE_ADJUSTMENTS = {
    64: -0.08,
    128: 0.0,
    256: 0.12,
    512: 0.25,
}

CONDITION_ADJUSTMENTS = {
    "excellent": 0.08,
    "good": 0.0,
    "fair": -0.12,
    "poor": -0.25,
}

BATTERY_BASELINE = 85
BATTERY_POINT_VALUE = 0.006  # 0.6% per point above/below baseline
BATTERY_ADJUSTMENT_CAP = 0.15

UNLOCKED_ADJUSTMENT = 0.05
LOCKED_ADJUSTMENT = -0.05


def estimate_market_value(listing):
    """Return (market_value, breakdown) for a listing.

    `listing` only needs `.model.base_value`, `.storage_gb`, `.condition`,
    `.battery_health`, and `.unlocked` - it does not need to be persisted,
    which is what lets POST /analyze reuse this on listings that were never
    saved to the database.
    """
    base_value = listing.model.base_value

    storage_adjustment = STORAGE_ADJUSTMENTS.get(listing.storage_gb, 0.0)
    condition_adjustment = CONDITION_ADJUSTMENTS.get(listing.condition, 0.0)

    battery_adjustment = (listing.battery_health - BATTERY_BASELINE) * BATTERY_POINT_VALUE
    battery_adjustment = max(-BATTERY_ADJUSTMENT_CAP, min(BATTERY_ADJUSTMENT_CAP, battery_adjustment))

    unlocked_adjustment = UNLOCKED_ADJUSTMENT if listing.unlocked else LOCKED_ADJUSTMENT

    market_value = (
        base_value
        * (1 + storage_adjustment)
        * (1 + condition_adjustment)
        * (1 + battery_adjustment)
        * (1 + unlocked_adjustment)
    )

    breakdown = {
        "base_value": round(base_value, 2),
        "storage_adjustment": storage_adjustment,
        "condition_adjustment": condition_adjustment,
        "battery_adjustment": round(battery_adjustment, 4),
        "unlocked_adjustment": unlocked_adjustment,
        "final": round(market_value, 2),
    }

    return round(market_value, 2), breakdown
