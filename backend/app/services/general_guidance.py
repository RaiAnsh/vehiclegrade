"""Layer 4 fallback: generic, honestly-labeled heuristic guidance for vehicles
with zero known-issue/maintenance coverage in the reference data - either
because the generation hasn't been researched yet, or (rarely) because it has
no known issues on record and no engine-linked generation to borrow from.

This is deliberately NOT vehicle-specific. It never claims to know anything
about this particular car - it's mileage/age-based rules of thumb, always
paired with a reminder to get an independent pre-purchase inspection. Used by
match_type.py to decide when a report should show a "general_guidance" match
type instead of pretending non-existent data is a real match.
"""

from datetime import datetime

HIGH_MILEAGE_KM = 200_000
MODERATE_MILEAGE_KM = 120_000
OLD_VEHICLE_AGE_YEARS = 10


def build_general_guidance(listing):
    """Return a list of generic guidance strings for a listing with no
    known-issue data of its own, direct or engine-linked.
    """
    guidance = []

    if listing.mileage_km >= HIGH_MILEAGE_KM:
        guidance.append(
            "At this mileage, most vehicles (regardless of make/model) are due for closer "
            "inspection of suspension components, engine/transmission mounts, and cooling "
            "system hoses/seals - wear items that fail from age and mileage across the board."
        )
    elif listing.mileage_km >= MODERATE_MILEAGE_KM:
        guidance.append(
            "At this mileage, it's worth checking timing components (belt/chain, depending on "
            "engine), brake wear, and suspension bushings - common attention points for most "
            "vehicles by this point, independent of make/model."
        )
    else:
        guidance.append(
            "At this mileage, routine maintenance history (oil changes, fluid services) matters "
            "more than wear-item failures - ask for service records."
        )

    vehicle_age_years = datetime.utcnow().year - listing.year
    if vehicle_age_years >= OLD_VEHICLE_AGE_YEARS:
        guidance.append(
            f"This vehicle is {vehicle_age_years} years old - rubber and plastic components "
            "(seals, bushings, hoses) degrade with age even on low-mileage examples, so "
            "age-related wear is worth checking regardless of the odometer reading."
        )

    guidance.append(
        "No issue-specific data exists yet for this vehicle in our reference database - get an "
        "independent pre-purchase inspection before buying."
    )

    return guidance
