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

EXACT = "exact"
AMBIGUOUS = "ambiguous"
UNIDENTIFIED = "unidentified"

ENGINE_MATCH_LABELS = {
    EXACT: "Exact engine identified for this listing",
    AMBIGUOUS: "This trim lists more than one possible engine - specific engine not confirmed",
    UNIDENTIFIED: "Engine not identified for this listing",
}


def engine_for_listing(listing):
    """The specific Engine identified for this listing, or None if it can't
    be identified (no engine_id on the listing or its trim). Public - callers
    that need to filter engine-linked data by *which* engine matched (not
    just *whether* one did) use this alongside find_engine_linked_generations.
    """
    if listing.engine_id:
        return listing.engine
    if listing.trim_id and listing.trim is not None and listing.trim.engine_id:
        return listing.trim.engine
    return None


def find_engine_linked_generations(listing):
    """Other generations (excluding the listing's own) that share an engine
    with this listing.
    """
    engine = engine_for_listing(listing)
    if engine is None:
        return []
    return [ge.generation for ge in engine.generations if ge.generation_id != listing.generation_id]


def compute_engine_match(listing):
    """Return "exact", "ambiguous", or "unidentified" describing how
    confidently this listing's specific engine is known.

    "ambiguous" means the trim itself records more than one possible engine
    option (a comma-separated `Trim.engine_options` string, e.g. a Ford F-150
    XL trim listing both a 3.3L and 3.5L V6) - we deliberately do NOT infer
    ambiguity from how many Engine rows happen to be linked to the
    generation, since that conflates "we haven't modeled every engine yet"
    with "this specific trim's engine can't be determined."
    """
    if engine_for_listing(listing) is not None:
        return EXACT
    if listing.trim is not None and listing.trim.engine_options and "," in listing.trim.engine_options:
        return AMBIGUOUS
    return UNIDENTIFIED
