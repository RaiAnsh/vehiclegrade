"""Generates realistic mock data for VehicleGrade.

Loads the vehicle knowledge base from JSON files (one per make) in
`vehicle_knowledge_base/`, then generates mock listings against it.
Deterministic (fixed random seed) so the demo dataset - and the resulting
VehicleGrade Score distribution - is reproducible across machines and runs.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from app.extensions import db
from app.models import Generation, KnownIssue, Listing, Location, MaintenanceItem, Trim, VehicleMake, VehicleModel

KNOWLEDGE_BASE_DIR = Path(__file__).parent / "vehicle_knowledge_base"

# city, region, rust_belt_risk
LOCATIONS = [
    ("Toronto", "ON", "medium"),
    ("Mississauga", "ON", "medium"),
    ("Ottawa", "ON", "medium"),
    ("Hamilton", "ON", "high"),
    ("Winnipeg", "MB", "high"),
    ("Calgary", "AB", "medium"),
    ("Vancouver", "BC", "low"),
    ("Phoenix", "AZ", "low"),
    ("Buffalo", "NY", "high"),
    ("Miami", "FL", "low"),
    ("Chicago", "IL", "high"),
    ("Denver", "CO", "medium"),
]

TRANSMISSION_FALLBACKS = ["Automatic", "CVT", "Manual"]
FUEL_TYPE_WEIGHTS = {"Gasoline": 0.85, "Hybrid": 0.1, "Diesel": 0.05}

# clean, unknown, rebuilt, salvage
TITLE_STATUS_WEIGHTS = [0.88, 0.06, 0.03, 0.03]

# excellent, good, fair, poor
CONDITION_WEIGHTS = [0.15, 0.5, 0.25, 0.1]

ARCHIVED_FRACTION = 0.08  # sold/removed listings, kept for comparables-history demo

LISTINGS_PER_MODEL = 14
EXPECTED_KM_PER_YEAR = 15000


def seed_database():
    """Drop and recreate all tables, then populate them with the knowledge base + mock listings."""
    db.drop_all()
    db.create_all()

    rng = random.Random(42)  # fixed seed -> reproducible dataset

    generations = _load_knowledge_base()
    locations = [Location(city=city, region=region, rust_belt_risk=risk) for city, region, risk in LOCATIONS]
    db.session.add_all(locations)
    db.session.flush()

    listings = []
    for generation in generations:
        for _ in range(LISTINGS_PER_MODEL):
            listings.append(_build_random_listing(rng, generation, locations))

    db.session.add_all(listings)
    db.session.commit()

    return {
        "makes": VehicleMake.query.count(),
        "models": VehicleModel.query.count(),
        "generations": len(generations),
        "locations": len(locations),
        "listings": len(listings),
    }


def _load_knowledge_base():
    """Read every make JSON file and build the ORM object graph. Returns a flat list of Generations."""
    all_generations = []

    for json_path in sorted(KNOWLEDGE_BASE_DIR.glob("*.json")):
        if json_path.stem == "common_repairs":
            continue

        with open(json_path) as f:
            data = json.load(f)

        make = VehicleMake(name=data["make"])
        db.session.add(make)
        db.session.flush()

        for model_data in data["models"]:
            model = VehicleModel(make_id=make.id, name=model_data["name"])
            db.session.add(model)
            db.session.flush()

            for gen_data in model_data["generations"]:
                generation = Generation(
                    model_id=model.id,
                    label=gen_data["label"],
                    start_year=gen_data["start_year"],
                    end_year=gen_data["end_year"],
                    body_type=gen_data["body_type"],
                    drivetrain=gen_data["drivetrain"],
                    base_horsepower=gen_data["base_horsepower"],
                    fuel_economy_l_per_100km=gen_data["fuel_economy_l_per_100km"],
                    reliability_stars=gen_data["reliability_stars"],
                    typical_lifespan_km=gen_data["typical_lifespan_km"],
                    parts_availability=gen_data["parts_availability"],
                    insurance_category=gen_data["insurance_category"],
                    expected_annual_maintenance_cost=gen_data["expected_annual_maintenance_cost"],
                    common_competitors=gen_data.get("common_competitors"),
                    base_value=gen_data["base_value"],
                    reference_mileage_km=gen_data["reference_mileage_km"],
                )
                db.session.add(generation)
                db.session.flush()

                for trim_data in gen_data.get("trims", []):
                    db.session.add(Trim(
                        generation_id=generation.id,
                        name=trim_data["name"],
                        msrp_adjustment_pct=trim_data.get("msrp_adjustment_pct", 0.0),
                        engine_options=trim_data.get("engine_options"),
                        transmission_options=trim_data.get("transmission_options"),
                    ))

                for issue_data in gen_data.get("known_issues", []):
                    db.session.add(KnownIssue(
                        generation_id=generation.id,
                        title=issue_data["title"],
                        description=issue_data["description"],
                        severity=issue_data["severity"],
                        typical_mileage_km=issue_data["typical_mileage_km"],
                        estimated_repair_cost_min=issue_data["estimated_repair_cost_min"],
                        estimated_repair_cost_max=issue_data["estimated_repair_cost_max"],
                        symptoms=issue_data.get("symptoms"),
                        recommendation=issue_data["recommendation"],
                    ))

                for item_data in gen_data.get("maintenance_items", []):
                    db.session.add(MaintenanceItem(
                        generation_id=generation.id,
                        name=item_data["name"],
                        interval_km=item_data["interval_km"],
                        estimated_cost_min=item_data.get("estimated_cost_min"),
                        estimated_cost_max=item_data.get("estimated_cost_max"),
                    ))

                db.session.flush()
                all_generations.append(generation)

    db.session.flush()
    return all_generations


def _build_random_listing(rng, generation, locations):
    year = rng.randint(generation.start_year, generation.end_year)
    vehicle_age_years = max(datetime.now().year - year, 0)
    expected_km = vehicle_age_years * EXPECTED_KM_PER_YEAR
    mileage_km = max(1000, round(rng.triangular(expected_km * 0.5, expected_km * 1.8, expected_km) / 500) * 500)

    trims = generation.trims
    trim = rng.choice(trims) if trims else None

    if trim and trim.transmission_options:
        transmission = rng.choice([t.strip() for t in trim.transmission_options.split(",")])
    else:
        transmission = rng.choice(TRANSMISSION_FALLBACKS)

    fuel_type = rng.choices(list(FUEL_TYPE_WEIGHTS), weights=list(FUEL_TYPE_WEIGHTS.values()))[0]
    title_status = rng.choices(["clean", "unknown", "rebuilt", "salvage"], weights=TITLE_STATUS_WEIGHTS)[0]
    condition = rng.choices(["excellent", "good", "fair", "poor"], weights=CONDITION_WEIGHTS)[0]
    seller_rating = round(rng.triangular(2.8, 5.0, 4.5), 1)
    days_listed = rng.choices(
        [rng.randint(0, 6), rng.randint(7, 13), rng.randint(14, 24), rng.randint(25, 45)],
        weights=[0.35, 0.3, 0.2, 0.15],
    )[0]

    # Price starts near the fair market value for these attributes, then a
    # random swing is applied so some listings land underpriced (deal) and
    # some land overpriced (avoid) - a real marketplace has both. A plain
    # SimpleNamespace (not a Listing) is enough here since estimate_market_value
    # only reads a few attributes - no need to touch the ORM session at all.
    from types import SimpleNamespace

    from app.services.market_value import estimate_market_value

    attrs = SimpleNamespace(
        generation=generation, trim=trim, mileage_km=mileage_km, title_status=title_status, condition=condition
    )
    fair_value, _ = estimate_market_value(attrs)

    price_swing = rng.triangular(-0.3, 0.3, 0)
    price = max(500, round((fair_value * (1 + price_swing)) / 50) * 50)

    location = rng.choice(locations)

    now = datetime.utcnow()
    is_archived = rng.random() < ARCHIVED_FRACTION
    first_seen_at = now - timedelta(days=days_listed)
    last_seen_at = now - timedelta(days=rng.randint(1, 60)) if is_archived else now

    return Listing(
        generation_id=generation.id,
        trim_id=trim.id if trim else None,
        location_id=location.id,
        year=year,
        mileage_km=mileage_km,
        price=price,
        transmission=transmission,
        fuel_type=fuel_type,
        title_status=title_status,
        condition=condition,
        seller_rating=seller_rating,
        days_listed=days_listed,
        source="mock",
        first_seen_at=first_seen_at,
        last_seen_at=last_seen_at,
        is_archived=is_archived,
    )
