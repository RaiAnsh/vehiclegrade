"""Maintenance Timeline engine.

Buckets a generation's recurring maintenance items into Immediate / Soon /
Future based on how close the listing's current mileage is to each item's
next due point - the same "ratio to a mileage threshold" idea used in
known_issues.py, applied to scheduled service instead of failures.

Each entry is tagged with a `match_tier` the same way known_issues.py does -
items authored against the listing's own generation vs. items borrowed from a
different generation that shares the same engine (see
app.services.engine_match).
"""

from app.services.engine_match import find_engine_linked_generations

SOON_THRESHOLD_RATIO = 0.85
IMMEDIATE_THRESHOLD_RATIO = 0.97


def _next_due_km(mileage_km, interval_km):
    """Distance (in km) until this item's next service point. 0 means due now."""
    km_into_interval = mileage_km % interval_km
    if km_into_interval == 0:
        return 0
    return interval_km - km_into_interval


def _bucket_for(item, listing):
    due_in_km = _next_due_km(listing.mileage_km, item.interval_km)
    progress_ratio = 1 - (due_in_km / item.interval_km)  # how far into this cycle we are

    if progress_ratio >= IMMEDIATE_THRESHOLD_RATIO:
        bucket = "immediate"
    elif progress_ratio >= SOON_THRESHOLD_RATIO:
        bucket = "soon"
    else:
        bucket = "future"

    return bucket, due_in_km


def build_timeline(listing):
    """Return {"immediate": [...], "soon": [...], "future": [...]} for a listing."""
    timeline = {"immediate": [], "soon": [], "future": []}
    seen_names = set()

    def add(item, listing, match_tier):
        if item.name in seen_names:
            return
        seen_names.add(item.name)

        bucket, due_in_km = _bucket_for(item, listing)
        timeline[bucket].append({
            "name": item.name,
            "interval_km": item.interval_km,
            "due_in_km": due_in_km,
            "estimated_cost_min": item.estimated_cost_min,
            "estimated_cost_max": item.estimated_cost_max,
            "match_tier": match_tier,
        })

    own_tier = "exact_vehicle" if listing.trim is not None else "generation"
    for item in listing.generation.maintenance_items:
        add(item, listing, own_tier)

    for generation in find_engine_linked_generations(listing):
        for item in generation.maintenance_items:
            add(item, listing, "engine_component")

    return timeline
