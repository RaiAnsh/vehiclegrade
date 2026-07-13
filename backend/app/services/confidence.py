"""Confidence Score: how much a specific report should be trusted, made of
the same kind of one-line, additive rules as the VehicleGrade Score itself - no
black box, no vague "AI confidence."

Starts at 100 and deducts for concrete, checkable gaps: a thin or missing
comparable-listings sample, an unidentified trim, a generation with no
known-issue data recorded yet, missing mileage, and (for manually-entered
listings only) optional fields the user left blank. Every deduction carries
its own reason string, and every reason that represents a real gap is also
surfaced separately as `missing_data` so the report can ask for it instead
of silently guessing.
"""

CONFIDENCE_START = 100

HIGH_THRESHOLD = 80
MEDIUM_THRESHOLD = 55

NO_COMPARABLES_PENALTY = 35
THIN_COMPARABLES_PENALTY = 20
LIMITED_COMPARABLES_PENALTY = 8
NO_TRIM_PENALTY = 12
NO_KNOWN_ISSUE_DATA_PENALTY = 10
NO_MILEAGE_PENALTY = 25
UNBANDED_COMPARABLES_PENALTY = 6


def compute_confidence(listing, comparables_summary, match_type=None):
    """Return {score, level, factors, missing_data, match_type} for a listing.

    `match_type` (see app.services.match_type) is attached as-is for display -
    it doesn't affect the score itself, since a missing/generation-level match
    already lowers the score via the known-issue-data and trim penalties below.
    """
    factors = []
    missing_data = []

    count = comparables_summary["count"]
    if count == 0:
        factors.append({"reason": "No comparable listings found for this generation", "points": -NO_COMPARABLES_PENALTY})
        missing_data.append("comparable market listings")
    elif count < 5:
        factors.append({
            "reason": f"Only {count} comparable listing(s) available - small sample",
            "points": -THIN_COMPARABLES_PENALTY,
        })
        missing_data.append("more comparable market listings")
    elif count < 10:
        factors.append({
            "reason": f"Limited comparable sample ({count} listings)",
            "points": -LIMITED_COMPARABLES_PENALTY,
        })
    elif not comparables_summary.get("band_applied", True):
        factors.append({
            "reason": "Comparable listings had to be widened beyond this listing's mileage range",
            "points": -UNBANDED_COMPARABLES_PENALTY,
        })

    if listing.trim is None:
        factors.append({
            "reason": "Trim/engine not identified - using generation-level base value only",
            "points": -NO_TRIM_PENALTY,
        })
        missing_data.append("trim or engine identification")

    if not listing.generation.known_issues:
        factors.append({
            "reason": "No known-issue data recorded for this generation yet",
            "points": -NO_KNOWN_ISSUE_DATA_PENALTY,
        })
        missing_data.append("known-issue history for this generation")

    if not listing.mileage_km or listing.mileage_km <= 0:
        factors.append({"reason": "Mileage not provided", "points": -NO_MILEAGE_PENALTY})
        missing_data.append("mileage")

    input_penalty = getattr(listing, "_input_completeness_penalty", 0)
    input_missing = getattr(listing, "_input_completeness_missing", [])
    if input_penalty:
        factors.append({
            "reason": f"Listing details left blank: {', '.join(input_missing)}",
            "points": -input_penalty,
        })
        missing_data.extend(input_missing)

    score = CONFIDENCE_START + sum(f["points"] for f in factors)
    score = max(0, min(100, score))

    if score >= HIGH_THRESHOLD:
        level = "high"
    elif score >= MEDIUM_THRESHOLD:
        level = "medium"
    else:
        level = "low"

    return {
        "score": score,
        "level": level,
        "factors": factors,
        "missing_data": missing_data,
        "match_type": match_type,
    }
