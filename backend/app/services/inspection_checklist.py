"""Inspection Checklist: a vehicle-specific pre-purchase checklist built
from data already on the listing and its generation - known issues due
soon, maintenance items coming up, drivetrain-specific wear points, and
regional rust risk. No new knowledge-base fields required.
"""

RELEVANT_ISSUE_STATUSES = {"common_now", "overdue"}


def build_inspection_checklist(listing, known_issues, maintenance_timeline):
    items = []

    for issue in known_issues:
        if issue["status"] in RELEVANT_ISSUE_STATUSES:
            line = f"Check for {issue['title'].lower()}"
            if issue.get("symptoms"):
                line += f" - look/listen for: {issue['symptoms']}"
            items.append(line)

    for maintenance_item in maintenance_timeline["immediate"] + maintenance_timeline["soon"]:
        items.append(
            f"Confirm {maintenance_item['name'].lower()} has been serviced "
            f"(due every {maintenance_item['interval_km']:,} km)"
        )

    if listing.generation.drivetrain in ("AWD", "4WD"):
        items.append("Inspect the transfer case and differential fluid - AWD/4WD adds extra wear points")

    if listing.location and listing.location.rust_belt_risk == "high":
        items.append("Inspect frame rails, rocker panels, and subframe closely for rust")

    items.append("Test drive on both highway and stop-and-go city streets")
    if listing.title_status != "clean":
        items.append("Run a VIN/title history check given the non-clean title status")

    # Dedupe while preserving order (a known-issue line and a maintenance
    # line can occasionally overlap in wording).
    seen = set()
    deduped = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped
