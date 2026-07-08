"""Generates realistic mock data for FlipIQ.

Deterministic (fixed random seed) so the demo dataset - and the resulting
FlipIQ Score distribution - is reproducible across machines and runs.
"""

import random

from app.extensions import db
from app.models import PhoneModel, Location, Listing

# name, release_year, base_value (128GB / good condition / 85% battery)
PHONE_MODELS = [
    ("iPhone 11", 2019, 220),
    ("iPhone 12", 2020, 320),
    ("iPhone 13", 2021, 430),
    ("iPhone 14", 2022, 560),
    ("iPhone 15", 2023, 720),
]

LOCATIONS = [
    ("Toronto", "ON"),
    ("Mississauga", "ON"),
    ("Brampton", "ON"),
    ("Markham", "ON"),
    ("Vaughan", "ON"),
    ("Scarborough", "ON"),
    ("North York", "ON"),
    ("Etobicoke", "ON"),
    ("Oakville", "ON"),
    ("Hamilton", "ON"),
]

STORAGE_TIERS = [64, 128, 256, 512]
CONDITIONS = ["excellent", "good", "fair", "poor"]

# Rough weightings so the dataset looks like a real marketplace: mostly
# "good"/"fair" listings, with real (not staged) excellent and poor outliers.
CONDITION_WEIGHTS = [0.20, 0.40, 0.28, 0.12]
STORAGE_WEIGHTS = [0.30, 0.40, 0.22, 0.08]

LISTINGS_PER_MODEL = 13  # 5 models x 13 = 65 listings


def seed_database():
    """Drop and recreate all tables, then populate them with mock data."""
    db.drop_all()
    db.create_all()

    rng = random.Random(42)  # fixed seed -> reproducible dataset

    models = [PhoneModel(name=name, release_year=year, base_value=base) for name, year, base in PHONE_MODELS]
    locations = [Location(city=city, region=region) for city, region in LOCATIONS]
    db.session.add_all(models + locations)
    db.session.flush()  # assign ids without committing yet

    listings = []
    for phone_model in models:
        for _ in range(LISTINGS_PER_MODEL):
            listings.append(_build_random_listing(rng, phone_model, locations))

    db.session.add_all(listings)
    db.session.commit()

    return {"models": len(models), "locations": len(locations), "listings": len(listings)}


def _build_random_listing(rng, phone_model, locations):
    storage_gb = rng.choices(STORAGE_TIERS, weights=STORAGE_WEIGHTS)[0]
    condition = rng.choices(CONDITIONS, weights=CONDITION_WEIGHTS)[0]
    battery_health = _random_battery_for_condition(rng, condition)
    unlocked = rng.random() < 0.7
    seller_rating = round(rng.triangular(2.8, 5.0, 4.5), 1)
    days_listed = rng.choices(
        [rng.randint(0, 6), rng.randint(7, 13), rng.randint(14, 24), rng.randint(25, 45)],
        weights=[0.35, 0.3, 0.2, 0.15],
    )[0]

    # Price starts near the "fair" market value for these attributes, then a
    # random swing is applied so some listings land underpriced (deal) and
    # some land overpriced (avoid) - a real marketplace has both. A plain
    # SimpleNamespace (not a Listing) is enough here since estimate_market_value
    # only reads a few attributes - no need to touch the ORM session at all.
    from types import SimpleNamespace

    from app.services.market_value import estimate_market_value

    attrs = SimpleNamespace(
        model=phone_model,
        storage_gb=storage_gb,
        battery_health=battery_health,
        condition=condition,
        unlocked=unlocked,
    )
    fair_value, _ = estimate_market_value(attrs)

    price_swing = rng.triangular(-0.35, 0.35, 0)
    price = max(40, round((fair_value * (1 + price_swing)) / 5) * 5)

    location = rng.choice(locations)

    return Listing(
        model_id=phone_model.id,
        location_id=location.id,
        storage_gb=storage_gb,
        price=price,
        battery_health=battery_health,
        condition=condition,
        unlocked=unlocked,
        seller_rating=seller_rating,
        days_listed=days_listed,
        source="mock",
    )


def _random_battery_for_condition(rng, condition):
    ranges = {
        "excellent": (90, 100),
        "good": (80, 94),
        "fair": (70, 85),
        "poor": (55, 75),
    }
    low, high = ranges[condition]
    return rng.randint(low, high)
