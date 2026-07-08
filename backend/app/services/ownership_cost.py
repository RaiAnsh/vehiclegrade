"""Ownership Cost engine.

Projects a rough annual cost of owning a vehicle - fuel, insurance, and
maintenance - purely from the generation's knowledge-base specs. Like
market_value.py, this never looks at the listing's price.
"""

EXPECTED_KM_PER_YEAR = 15000
FUEL_PRICE_PER_LITER = 1.60

INSURANCE_BY_CATEGORY = {
    "low": 1200,
    "medium": 1700,
    "high": 2400,
}


def estimate_ownership_cost(listing):
    """Return a dict of estimated annual ownership costs for a listing's generation."""
    generation = listing.generation

    liters_per_year = (EXPECTED_KM_PER_YEAR / 100) * generation.fuel_economy_l_per_100km
    fuel_annual = round(liters_per_year * FUEL_PRICE_PER_LITER, 2)

    insurance_annual = INSURANCE_BY_CATEGORY.get(generation.insurance_category, INSURANCE_BY_CATEGORY["medium"])
    maintenance_annual = generation.expected_annual_maintenance_cost

    return {
        "fuel_annual": fuel_annual,
        "insurance_annual": insurance_annual,
        "maintenance_annual": maintenance_annual,
        "total_annual": round(fuel_annual + insurance_annual + maintenance_annual, 2),
    }
