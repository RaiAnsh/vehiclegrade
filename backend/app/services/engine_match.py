"""Shared helper for finding other generations that share a listing's engine.

Used by both known_issues.py and maintenance_timeline.py to surface
engine-linked reference data (see app.models.engine.Engine and
app.models.generation_engine.GenerationEngine) - i.e. an issue or
maintenance item authored against generation A can surface for a listing
of generation B when both share the same Engine record, instead of only
ever matching the exact generation it was entered against.

Returns [] whenever the listing's engine can't be identified, or when it
isn't linked to any other generation yet - both are expected until Engine/
GenerationEngine rows are actually populated for a given engine family.
"""


def _engine_for_listing(listing):
    if listing.engine_id:
        return listing.engine
    if listing.trim_id and listing.trim is not None and listing.trim.engine_id:
        return listing.trim.engine
    return None


def find_engine_linked_generations(listing):
    """Other generations (excluding the listing's own) that share an engine
    with this listing.
    """
    engine = _engine_for_listing(listing)
    if engine is None:
        return []
    return [ge.generation for ge in engine.generations if ge.generation_id != listing.generation_id]
