"""Loading and basic analysis of iPhone listings."""

import json


def load_listings(path):
    """Load listings from a JSON file and return them as a list of dicts."""
    with open(path, "r") as file:
        return json.load(file)


def average_price_by_model(listings):
    """Return a dict mapping each model to its average listing price."""
    totals = {}
    counts = {}

    for listing in listings:
        model = listing["model"]
        totals[model] = totals.get(model, 0) + listing["price"]
        counts[model] = counts.get(model, 0) + 1

    return {model: round(totals[model] / counts[model], 2) for model in totals}


def cheapest_listing(listings):
    """Return the listing with the lowest price."""
    return min(listings, key=lambda listing: listing["price"])
