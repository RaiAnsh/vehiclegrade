"""Filters for narrowing down listings."""


def filter_by_budget(listings, budget):
    """Return only the listings priced at or under the given budget."""
    return [listing for listing in listings if listing["price"] <= budget]


def filter_by_model(listings, model):
    """Return only the listings that match the given model name."""
    return [listing for listing in listings if listing["model"].lower() == model.lower()]
