"""Maintenance Timeline engine.

Buckets a generation's recurring maintenance items into Immediate / Soon /
Future based on how close the listing's current mileage is to each item's
next due point - the same "ratio to a mileage threshold" idea used in
known_issues.py, applied to scheduled service instead of failures.
"""

SOON_THRESHOLD_RATIO = 0.85
IMMEDIATE_THRESHOLD_RATIO = 0.97


def _next_due_km(mileage_km, interval_km):
    """Distance (in km) until this item's next service point. 0 means due now."""
    km_into_interval = mileage_km % interval_km
    if km_into_interval == 0:
        return 0
    return interval_km - km_into_interval


def build_timeline(listing):
    """Return {"immediate": [...], "soon": [...], "future": [...]} for a listing."""
    timeline = {"immediate": [], "soon": [], "future": []}

    for item in listing.generation.maintenance_items:
        due_in_km = _next_due_km(listing.mileage_km, item.interval_km)
        progress_ratio = 1 - (due_in_km / item.interval_km)  # how far into this cycle we are

        entry = {
            "name": item.name,
            "interval_km": item.interval_km,
            "due_in_km": due_in_km,
            "estimated_cost_min": item.estimated_cost_min,
            "estimated_cost_max": item.estimated_cost_max,
        }

        if progress_ratio >= IMMEDIATE_THRESHOLD_RATIO:
            bucket = "immediate"
        elif progress_ratio >= SOON_THRESHOLD_RATIO:
            bucket = "soon"
        else:
            bucket = "future"

        timeline[bucket].append(entry)

    return timeline
