"""Match Type: how specifically the known-issue/reliability data attached to
a report actually matches the vehicle being analyzed, as opposed to being
borrowed from a broader category.

Today every generation's known-issue data is authored directly against that
exact generation, so the only real distinction is whether the listing's
specific trim/engine was identified (`exact_vehicle`), whether we only know
the generation as a whole (`generation`), or whether this generation has no
known-issue data recorded at all (`unsupported`). `engine_component` becomes
reachable once engine-family-linked issues exist (see Engine/GenerationEngine
models), letting an issue recorded against one generation surface for another
generation sharing the same engine.
"""

EXACT_VEHICLE = "exact_vehicle"
GENERATION = "generation"
ENGINE_COMPONENT = "engine_component"
UNSUPPORTED = "unsupported"

MATCH_TYPE_LABELS = {
    EXACT_VEHICLE: "Matched to this exact trim/engine",
    GENERATION: "Matched to this generation (trim/engine not identified)",
    ENGINE_COMPONENT: "Matched via a shared engine/component with another generation",
    UNSUPPORTED: "No known-issue data recorded for this vehicle yet",
}


def compute_match_type(listing):
    """Return the match type string for a listing's known-issue/reliability data."""
    if not listing.generation.known_issues:
        return UNSUPPORTED
    if listing.trim is not None:
        return EXACT_VEHICLE
    return GENERATION
