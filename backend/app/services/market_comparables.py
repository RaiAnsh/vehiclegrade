"""Comparable Listings: the first real "market sample" data source in
VehicleGrade, built from the mock Listing table that already exists for
dashboard/analytics demos.

This is explicitly separate from the Market Value Engine (market_value.py),
which prices a vehicle from pure reference data (generation.base_value) and
never looks at other listings. Comparables answer a different question -
"what are similar vehicles actually asking right now, in this sample?" - and
every result carries an explicit disclosure that the underlying data is
VehicleGrade's seeded demo dataset, not a live marketplace feed.
"""

from statistics import median

from app.models import Listing

MILEAGE_BAND_RATIO = 0.30
MIN_BANDED_ROWS = 3


def find_comparables(listing, limit=12):
    """Return (comparables, band_applied) - up to `limit` listings from the
    same generation, sorted by mileage closeness to `listing`.

    band_applied is True if the ±30% mileage band around this listing had
    enough rows to use as-is, False if it had to widen to the whole
    generation (a signal the sample is thin, surfaced by confidence.py).
    """
    query = Listing.query.filter(
        Listing.generation_id == listing.generation.id,
        Listing.is_archived.is_(False),
    )
    if listing.id is not None:
        query = query.filter(Listing.id != listing.id)

    all_rows = query.all()

    low = listing.mileage_km * (1 - MILEAGE_BAND_RATIO)
    high = listing.mileage_km * (1 + MILEAGE_BAND_RATIO)
    banded = [row for row in all_rows if low <= row.mileage_km <= high]

    band_applied = len(banded) >= MIN_BANDED_ROWS
    pool = banded if band_applied else all_rows

    pool = sorted(pool, key=lambda row: abs(row.mileage_km - listing.mileage_km))
    return pool[:limit], band_applied


def summarize_comparables(listing, comparables, band_applied):
    """Return a JSON-ready summary dict, always tagged with an explicit
    market_sample disclosure so this can never be mistaken for real data.
    """
    if not comparables:
        return {
            "count": 0,
            "avg_price": None,
            "median_price": None,
            "min_price": None,
            "max_price": None,
            "price_percentile": None,
            "band_applied": band_applied,
            "comparables": [],
            "source": "market_sample",
            "disclosure": (
                "No comparable listings were found in VehicleGrade's seeded demo dataset for this "
                "generation - this is sample data for the beta, not a live marketplace feed."
            ),
        }

    prices = sorted(row.price for row in comparables)
    below_or_equal = sum(1 for price in prices if price <= listing.price)
    percentile = round(below_or_equal / len(prices) * 100)

    return {
        "count": len(comparables),
        "avg_price": round(sum(prices) / len(prices), 2),
        "median_price": median(prices),
        "min_price": min(prices),
        "max_price": max(prices),
        "price_percentile": percentile,
        "band_applied": band_applied,
        "comparables": [
            {
                "price": row.price,
                "mileage_km": row.mileage_km,
                "title_status": row.title_status,
                "condition": row.condition,
                "location": row.location.city if row.location else None,
                "days_listed": row.days_listed,
            }
            for row in comparables
        ],
        "source": "market_sample",
        "disclosure": (
            "Based on VehicleGrade's seeded demo marketplace data for beta purposes - not live "
            "real-world listings."
        ),
    }
