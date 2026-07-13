"""Known Issues engine.

Turns a generation's static list of commonly-reported problems into
mileage-aware guidance for a *specific* listing. The same issue reads
differently depending on how far the listing's odometer is past the typical
onset mileage - a 40,000 km Civic and a 250,000 km Civic of the same
generation get very different copy for "AC compressor failure", even though
the underlying knowledge-base row never changes.

Each returned issue is also tagged with a `match_tier` describing how
directly it applies to this listing: `exact_vehicle`/`generation` for issues
authored against the listing's own generation, or `engine_component` for
issues borrowed from a different generation that shares the same engine (see
app.services.engine_match) - i.e. an issue reported against one car surfacing
as relevant guidance for another car that uses the same engine.
"""

from app.services.engine_match import find_engine_linked_generations

STATUS_COPY = {
    "not_yet_relevant": "Unlikely yet - typically appears around {typical_mileage_km:,} km",
    "approaching": "Worth watching for - commonly starts near {typical_mileage_km:,} km",
    "common_now": "Common at this mileage - inspect before buying",
    "overdue": "Past the typical onset mileage - budget for this repair",
}


def status_for_issue(mileage_km, typical_mileage_km):
    # A handful of knowledge-base entries are design quirks rather than
    # mileage-dependent wear items (e.g. "cramped rear seat"), and are
    # authored with typical_mileage_km=0 to mean "always applicable." Treat
    # that as always "common now" instead of dividing by zero.
    if typical_mileage_km <= 0:
        return "common_now"
    ratio = mileage_km / typical_mileage_km
    if ratio < 0.6:
        return "not_yet_relevant"
    if ratio < 0.9:
        return "approaching"
    if ratio < 1.3:
        return "common_now"
    return "overdue"


def _issue_entry(issue, listing, match_tier):
    status = status_for_issue(listing.mileage_km, issue.typical_mileage_km)
    status_copy = STATUS_COPY[status].format(typical_mileage_km=issue.typical_mileage_km)

    return {
        "title": issue.title,
        "description": issue.description,
        "severity": issue.severity,
        "status": status,
        "status_copy": status_copy,
        "typical_mileage_km": issue.typical_mileage_km,
        "estimated_repair_cost_min": issue.estimated_repair_cost_min,
        "estimated_repair_cost_max": issue.estimated_repair_cost_max,
        "symptoms": issue.symptoms,
        "recommendation": issue.recommendation,
        "match_tier": match_tier,
    }


def evaluate_known_issues(listing):
    """Return a list of known-issue dicts, each tagged with a mileage-aware
    status and a match_tier describing how directly the issue applies.
    """
    own_tier = "exact_vehicle" if listing.trim is not None else "generation"
    results = [_issue_entry(issue, listing, own_tier) for issue in listing.generation.known_issues]

    seen_titles = {issue.title for issue in listing.generation.known_issues}
    for generation in find_engine_linked_generations(listing):
        for issue in generation.known_issues:
            if issue.title in seen_titles:
                continue
            seen_titles.add(issue.title)
            results.append(_issue_entry(issue, listing, "engine_component"))

    return results
