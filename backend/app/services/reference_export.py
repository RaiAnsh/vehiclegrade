"""Admin/import-ready reference-data exports.

Each function returns a flat list of plain dicts pulled straight from the
ORM - no computed/estimated values, only structured reference data (plus
the mock market_comparables table, which is explicitly labeled as sample
data). This is what lets `flask export-reference-data` produce files a real
data-import pipeline could eventually replace or merge with, without
touching any application code.
"""

from app.models import Generation, KnownIssue, Listing, MaintenanceItem, Trim

VEHICLE_SPECS_FIELDS = [
    "make", "model", "generation_label", "start_year", "end_year", "trim",
    "engine", "transmission_options", "drivetrain", "body_style", "horsepower",
    "fuel_economy_l_per_100km", "msrp_adjustment_pct",
]

KNOWN_ISSUES_FIELDS = [
    "make", "model", "generation_label", "start_year", "end_year", "title",
    "description", "symptoms", "severity", "typical_mileage_km",
    "estimated_repair_cost_min", "estimated_repair_cost_max", "recommendation",
]

MAINTENANCE_INTERVALS_FIELDS = [
    "make", "model", "generation_label", "name", "interval_km",
    "estimated_cost_min", "estimated_cost_max",
]

MARKET_COMPARABLES_FIELDS = [
    "id", "make", "model", "generation_label", "trim", "year", "mileage_km",
    "price", "condition", "title_status", "transmission", "fuel_type",
    "location", "days_listed", "source", "first_seen_at", "last_seen_at", "is_archived",
]


def export_vehicle_specs():
    """One row per generation, or per (generation, trim) if trims exist.

    Deliberately does not include a fuel_type field - this schema tracks
    fuel type per-listing, not per-generation, and inventing one here would
    be exactly the "pretend fake data is real" behavior the reference layer
    exists to avoid.
    """
    rows = []
    for generation in Generation.query.all():
        model = generation.model
        make = model.make
        base = {
            "make": make.name,
            "model": model.name,
            "generation_label": generation.label,
            "start_year": generation.start_year,
            "end_year": generation.end_year,
            "drivetrain": generation.drivetrain,
            "body_style": generation.body_type,
            "horsepower": generation.base_horsepower,
            "fuel_economy_l_per_100km": generation.fuel_economy_l_per_100km,
        }
        trims = Trim.query.filter(Trim.generation_id == generation.id).all()
        if not trims:
            rows.append({**base, "trim": None, "engine": None, "transmission_options": None, "msrp_adjustment_pct": 0.0})
            continue
        for trim in trims:
            rows.append({
                **base,
                "trim": trim.name,
                "engine": trim.engine_options,
                "transmission_options": trim.transmission_options,
                "msrp_adjustment_pct": trim.msrp_adjustment_pct,
            })
    return rows


def export_known_issues():
    rows = []
    for issue in KnownIssue.query.all():
        generation = issue.generation
        model = generation.model
        make = model.make
        rows.append({
            "make": make.name,
            "model": model.name,
            "generation_label": generation.label,
            "start_year": generation.start_year,
            "end_year": generation.end_year,
            "title": issue.title,
            "description": issue.description,
            "symptoms": issue.symptoms,
            "severity": issue.severity,
            "typical_mileage_km": issue.typical_mileage_km,
            "estimated_repair_cost_min": issue.estimated_repair_cost_min,
            "estimated_repair_cost_max": issue.estimated_repair_cost_max,
            "recommendation": issue.recommendation,
        })
    return rows


def export_maintenance_intervals():
    rows = []
    for item in MaintenanceItem.query.all():
        generation = item.generation
        model = generation.model
        make = model.make
        rows.append({
            "make": make.name,
            "model": model.name,
            "generation_label": generation.label,
            "name": item.name,
            "interval_km": item.interval_km,
            "estimated_cost_min": item.estimated_cost_min,
            "estimated_cost_max": item.estimated_cost_max,
        })
    return rows


def export_market_comparables():
    """Exports the mock Listing table as-is. Every row here is VehicleGrade's
    seeded beta sample data, not a real marketplace feed - callers of this
    export must preserve that distinction rather than treating it as
    reference data.
    """
    rows = []
    for listing in Listing.query.all():
        generation = listing.generation
        model = generation.model
        make = model.make
        rows.append({
            "id": listing.id,
            "make": make.name,
            "model": model.name,
            "generation_label": generation.label,
            "trim": listing.trim.name if listing.trim else None,
            "year": listing.year,
            "mileage_km": listing.mileage_km,
            "price": listing.price,
            "condition": listing.condition,
            "title_status": listing.title_status,
            "transmission": listing.transmission,
            "fuel_type": listing.fuel_type,
            "location": listing.location.city if listing.location else None,
            "days_listed": listing.days_listed,
            "source": listing.source,
            "first_seen_at": listing.first_seen_at.isoformat(),
            "last_seen_at": listing.last_seen_at.isoformat(),
            "is_archived": listing.is_archived,
        })
    return rows
