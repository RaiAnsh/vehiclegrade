"""Comparable Vehicles: "instead of this X, consider..." - reuses the
existing generation.common_competitors reference field (already
hand-authored knowledge-base data) instead of inventing a new data source.
Each named competitor is checked against the catalog to report whether
VehicleGrade actually has reference data on it yet.
"""

from app.models import VehicleModel


def find_comparable_vehicles(generation):
    if not generation.common_competitors:
        return []

    names = [name.strip() for name in generation.common_competitors.split(",") if name.strip()]
    results = []
    for name in names:
        model = VehicleModel.query.filter(VehicleModel.name.ilike(name)).first()
        results.append({"name": name, "has_data": model is not None})
    return results
