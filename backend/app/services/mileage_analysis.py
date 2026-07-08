"""Mileage-for-age analysis, shared by the VehicleGrade Score, red flags, seller
questions, and the report's "why" reasoning.

Everything here used to be computed independently (and identically) inside
deal_engine.py, red_flags.py, and seller_questions.py. Centralizing it means
the mileage number, the ratio, and the plain-English explanation can never
drift out of sync with each other across those three call sites.
"""

from datetime import datetime

EXPECTED_KM_PER_YEAR = 15000

LOW_MILEAGE_RATIO = 0.7
HIGH_MILEAGE_RATIO = 1.5


def classify_mileage(listing):
    """Return {vehicle_age_years, expected_km, ratio, classification, explanation} for a listing.

    classification is one of "low" | "typical" | "high", based on the same
    thresholds deal_engine.py already used for scoring.
    """
    vehicle_age_years = max(datetime.now().year - listing.year, 0)
    expected_km = vehicle_age_years * EXPECTED_KM_PER_YEAR
    ratio = listing.mileage_km / max(expected_km, 1)

    if ratio < LOW_MILEAGE_RATIO:
        classification = "low"
        explanation = (
            f"At {listing.mileage_km:,} km, this vehicle has covered about {round(ratio * 100)}% of the "
            f"~{expected_km:,} km typically expected for a {vehicle_age_years}-year-old vehicle "
            f"({EXPECTED_KM_PER_YEAR:,} km/year average) - meaningfully lower than average."
        )
    elif ratio > HIGH_MILEAGE_RATIO:
        classification = "high"
        explanation = (
            f"At {listing.mileage_km:,} km, this vehicle has covered about {round(ratio * 100)}% of the "
            f"~{expected_km:,} km typically expected for a {vehicle_age_years}-year-old vehicle "
            f"({EXPECTED_KM_PER_YEAR:,} km/year average) - meaningfully higher than average."
        )
    else:
        classification = "typical"
        explanation = (
            f"At {listing.mileage_km:,} km, this vehicle is within the ~{expected_km:,} km typically "
            f"expected for a {vehicle_age_years}-year-old vehicle ({EXPECTED_KM_PER_YEAR:,} km/year average)."
        )

    return {
        "vehicle_age_years": vehicle_age_years,
        "expected_km": expected_km,
        "ratio": round(ratio, 2),
        "classification": classification,
        "explanation": explanation,
    }
