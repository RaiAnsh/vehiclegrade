"""Match Type: how specifically the known-issue/reliability data attached to
a report actually matches the vehicle being analyzed, as opposed to being
borrowed from a broader category.

Distinguishes whether the listing's specific trim/engine was identified
(`exact_vehicle`), whether we only know the generation as a whole
(`generation`), whether the only available data was borrowed from a
different generation sharing the same engine (`engine_component`, see
Engine/GenerationEngine models and app.services.engine_match), whether
nothing vehicle-specific exists at all so only generic heuristic guidance is
shown (`general_guidance`, see app.services.general_guidance), or - as a
defensive fallback that shouldn't normally be reachable, since
general_guidance is always non-empty - `unsupported`.
"""

from app.services.engine_match import find_engine_linked_generations
from app.services.general_guidance import build_general_guidance

EXACT_VEHICLE = "exact_vehicle"
GENERATION = "generation"
ENGINE_COMPONENT = "engine_component"
GENERAL_GUIDANCE = "general_guidance"
UNSUPPORTED = "unsupported"

MATCH_TYPE_LABELS = {
    EXACT_VEHICLE: "Matched to this exact trim/engine",
    GENERATION: "Matched to this generation (trim/engine not identified)",
    ENGINE_COMPONENT: "Matched via a shared engine/component with another generation",
    GENERAL_GUIDANCE: "No vehicle-specific data yet - showing general guidance",
    UNSUPPORTED: "No known-issue data recorded for this vehicle yet",
}


def compute_match_type(listing):
    """Return the match type string for a listing's known-issue/reliability data."""
    if listing.generation.known_issues:
        return EXACT_VEHICLE if listing.trim is not None else GENERATION

    for generation in find_engine_linked_generations(listing):
        if generation.known_issues:
            return ENGINE_COMPONENT

    if build_general_guidance(listing):
        return GENERAL_GUIDANCE

    return UNSUPPORTED
