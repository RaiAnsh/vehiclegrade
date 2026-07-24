"""Shared make/model/generation/trim/location resolution against the
reference-data hierarchy (VehicleMake -> VehicleModel -> Generation -> Trim,
plus Location). Extracted from the inline queries POST /analyze already
used, so the new ingestion normalizer resolves listings exactly the same
way a manual /analyze submission does - same case-insensitive matching,
same "generation covers this model year" rule, no second implementation to
keep in sync.

Every function here is a pure lookup: it returns the matching row or None,
never raises, never guesses. Callers decide what "not found" means for
their context (a 400 error for /analyze, a `needs_review` flag for
ingestion).
"""

from app.models import Generation, Location, Trim, VehicleMake, VehicleModel


def resolve_make(make_name):
    if not make_name:
        return None
    return VehicleMake.query.filter(VehicleMake.name.ilike(make_name)).first()


def resolve_model(make, model_name):
    if make is None or not model_name:
        return None
    return VehicleModel.query.filter(VehicleModel.make_id == make.id, VehicleModel.name.ilike(model_name)).first()


def resolve_generation(model, year):
    if model is None or not year:
        return None
    return Generation.query.filter(
        Generation.model_id == model.id,
        Generation.start_year <= year,
        Generation.end_year >= year,
    ).first()


def resolve_trim(generation, trim_name):
    if generation is None or not trim_name:
        return None
    return Trim.query.filter(Trim.generation_id == generation.id, Trim.name.ilike(trim_name)).first()


def resolve_location(city_name):
    if not city_name:
        return None
    return Location.query.filter(Location.city.ilike(city_name)).first()


def resolve_vehicle(make_name, model_name, year, trim_name=None):
    """Convenience wrapper chaining make -> model -> generation -> trim,
    returning every intermediate result so callers can report exactly which
    step failed (e.g. "make matched but no model", vs "model matched but no
    generation covers this year").
    """
    make = resolve_make(make_name)
    model = resolve_model(make, model_name)
    generation = resolve_generation(model, year)
    trim = resolve_trim(generation, trim_name)
    return make, model, generation, trim
