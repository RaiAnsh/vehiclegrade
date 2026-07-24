"""Quality score (0-100): a single, explainable number summarizing how much
an admin should trust a ListingObservation before approving it - built from
the same additive-rules convention as app.services.confidence (VehicleGrade's
user-facing report confidence score), not a second scoring philosophy.

Deliberately harsher than confidence.py: this runs before any human has
looked at the row, so gaps and a duplicate flag cost more here than the
equivalent gap costs on an already-analyzed, already-approved listing.
"""

QUALITY_START = 100

UNRESOLVED_CORE_PENALTY = 18   # make, model, generation, year, price, mileage_km
UNRESOLVED_MINOR_PENALTY = 6   # trim, location, title_status, transmission, fuel_type, condition
VALIDATION_ERROR_PENALTY = 25
DUPLICATE_PENALTY = 40

CORE_FIELDS = {"make", "model", "generation", "year", "price", "mileage_km"}


def score_observation(validation_errors, unresolved_fields, is_duplicate, duplicate_reason=None):
    """Returns (score: int, factors: [{"reason": str, "points": int}, ...])."""
    factors = []
    score = QUALITY_START

    for field in unresolved_fields or []:
        penalty = UNRESOLVED_CORE_PENALTY if field in CORE_FIELDS else UNRESOLVED_MINOR_PENALTY
        factors.append({"reason": f"Missing/unresolved: {field}", "points": -penalty})
        score -= penalty

    for field in validation_errors or []:
        factors.append({"reason": f"Invalid value: {field}", "points": -VALIDATION_ERROR_PENALTY})
        score -= VALIDATION_ERROR_PENALTY

    if is_duplicate:
        factors.append({
            "reason": duplicate_reason or "Likely duplicate of an existing observation",
            "points": -DUPLICATE_PENALTY,
        })
        score -= DUPLICATE_PENALTY

    score = max(0, min(100, score))
    return score, factors
