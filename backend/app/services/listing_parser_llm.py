"""LLM fallback for /parse-listing.

The rule-based parser (listing_parser.py) always runs first and always wins
on any field it managed to extract - this module is only ever asked about
fields that are still missing after that, and only runs at all if an LLM
provider is configured (see llm_client.py). Every field is optional; the
model is explicitly told never to estimate or guess a field it can't find,
and every extracted make/model/title_status/transmission/fuel_type is
validated server-side against the same candidate lists the rule-based parser
uses, so a hallucinated value can never leak into the response.
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.models.listing import VALID_TITLE_STATUSES
from app.services.llm_client import get_llm
from app.services.llm_timeout import run_with_timeout

SYSTEM_PROMPT = """You extract structured fields from a pasted used-vehicle listing description.

You will be told which specific fields are still missing after a rule-based
parser already extracted what it could from the same text. Extract ONLY
those missing fields, and ONLY if the value is explicitly stated or
unambiguously implied in the text.

Strict rules:
- Never estimate, guess, or infer a field that isn't actually supported by the text.
- If a field cannot be confidently determined, leave it as null - do not guess.
- Only choose `make` and `model` from the candidate lists provided - never invent one that isn't listed.
- Only choose `location` from the candidate list provided - never invent one that isn't listed.
- title_status must be one of: clean, rebuilt, salvage, unknown.
"""


class ParsedListingLLM(BaseModel):
    year: Optional[int] = Field(default=None)
    make: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    price: Optional[float] = Field(default=None)
    mileage_km: Optional[int] = Field(default=None)
    title_status: Optional[str] = Field(default=None)
    transmission: Optional[str] = Field(default=None)
    fuel_type: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)


def _validated(field, value, makes, models_by_make, location_names):
    if value is None:
        return None
    if field == "make":
        return value if value in makes else None
    if field == "model":
        # Model is only meaningful alongside a make; validated against the
        # union of all candidate models since we don't know here which make
        # (if any) the LLM also returned.
        all_models = {m for models in models_by_make.values() for m in models}
        return value if value in all_models else None
    if field == "location":
        return value if value in location_names else None
    if field == "title_status":
        return value if value in VALID_TITLE_STATUSES else None
    return value


def parse_missing_fields(text, missing_fields, makes, models_by_make, location_names):
    """Returns a dict of {field: value} for only the fields in
    `missing_fields` the LLM confidently extracted and that passed server-
    side validation - {} if no LLM is configured, the call fails/times out,
    or nothing missing was found.
    """
    if not missing_fields:
        return {}

    llm = get_llm()
    if llm is None:
        return {}

    def _call():
        structured_llm = llm.with_structured_output(ParsedListingLLM)
        return structured_llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Missing fields to extract (only these, all others already known): {missing_fields}\n\n"
                    f"Candidate makes: {makes}\n"
                    f"Candidate models by make: {models_by_make}\n"
                    f"Candidate locations: {location_names}\n\n"
                    f"Listing description text:\n{text}"
                ),
            },
        ])

    result = run_with_timeout(_call)
    if result is None:
        return {}

    extracted = {}
    for field in missing_fields:
        value = _validated(field, getattr(result, field, None), makes, models_by_make, location_names)
        if value is not None:
            extracted[field] = value

    return extracted
