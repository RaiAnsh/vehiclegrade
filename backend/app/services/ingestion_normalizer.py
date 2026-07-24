"""Bronze -> Silver: turns one RawListingSubmission (pasted text OR one CSV
row) into a normalized, validated set of ListingObservation fields.

Two entry points, one shared tail:
  - normalize_submission(raw_text)          - pasted-text listings
  - normalize_csv_row(raw_row, column_mapping) - one CSV row
Both funnel into `_finalize`, so resolution/validation/dedup/quality-scoring
is written exactly once regardless of how a listing arrived. Text parsing
reuses the exact same cascade as POST /parse-listing (regex parser always
wins, LLM only fills gaps it's asked about); CSV rows are already
structured so they skip straight to reference-data resolution (see
reference_resolver.py, the same resolver POST /analyze uses).

Produces `pending` or `needs_review` only - never `approved`/`rejected`.
Deliberately conservative about what counts as "pending": ANY gap (a
missing title_status, an unmatched trim, etc.) routes to `needs_review`
rather than silently defaulting it, because - unlike /analyze, where a
human is actively filling in a form and can be trusted to pick sensible
values - this data may end up as a real comparable an admin never
personally re-typed, so nothing gets assumed on its behalf. Dedup and
quality scoring only ever add MORE reasons to flag `needs_review`, never
remove one found here.
"""

from datetime import datetime

from app.models import Location, VehicleMake, VehicleModel
from app.models.listing import VALID_TITLE_STATUSES
from app.services.duplicate_detection import extract_url, find_duplicate, hash_url
from app.services.listing_parser import parse_listing_text
from app.services.listing_parser_llm import parse_missing_fields
from app.services.market_value import CONDITION_ADJUSTMENTS
from app.services.quality_scoring import score_observation
from app.services.reference_resolver import resolve_location, resolve_vehicle

ALL_PARSEABLE_FIELDS = [
    "year", "make", "model", "price", "mileage_km",
    "title_status", "transmission", "fuel_type", "location",
]

VALID_CONDITIONS = tuple(CONDITION_ADJUSTMENTS.keys())

MIN_YEAR = 1980
MAX_PRICE = 500_000
MAX_MILEAGE_KM = 500_000

# CSV headers are matched against these (case-insensitive, exact) to
# suggest a column_mapping in the /csv-preview endpoint. Not fuzzy-matched
# on purpose - a wrong auto-guess silently mapping the wrong column is
# worse than asking the admin to confirm a column /csv-preview couldn't
# recognize.
CANONICAL_FIELD_SYNONYMS = {
    "year": ["year", "model year", "modelyear"],
    "make": ["make", "brand", "manufacturer"],
    "model": ["model"],
    "trim": ["trim", "trim level"],
    "price": ["price", "asking price", "list price", "listing price"],
    "mileage_km": ["mileage", "mileage_km", "odometer", "odometer (km)", "km", "kilometers"],
    "title_status": ["title", "title_status", "title status"],
    "condition": ["condition"],
    "transmission": ["transmission", "trans"],
    "fuel_type": ["fuel_type", "fuel type", "fuel"],
    "location": ["location", "city"],
    "source_identifier": ["id", "listing id", "source_id", "listing_id"],
    "external_url": ["url", "link", "listing url", "external_url"],
}

CSV_TEMPLATE_COLUMNS = [
    "year", "make", "model", "trim", "price", "mileage_km",
    "title_status", "condition", "transmission", "fuel_type", "location",
    "source_identifier", "external_url",
]

_CSV_NUMERIC_FIELDS = {"year": int, "price": float, "mileage_km": int}


def _load_catalog_candidates():
    make_rows = VehicleMake.query.all()
    makes = [m.name for m in make_rows]
    models_by_make = {
        make.name: [m.name for m in VehicleModel.query.filter(VehicleModel.make_id == make.id).all()]
        for make in make_rows
    }
    location_names = [loc.city for loc in Location.query.all()]
    return makes, models_by_make, location_names


def suggest_column_mapping(headers):
    """Returns {csv_header: canonical_field_or_None} - a starting point for
    an admin to confirm/correct in the CSV preview step, never applied
    automatically to an actual import.
    """
    reverse_lookup = {}
    for canonical, synonyms in CANONICAL_FIELD_SYNONYMS.items():
        for synonym in synonyms:
            reverse_lookup[synonym] = canonical
    return {header: reverse_lookup.get(header.strip().lower()) for header in headers}


def _map_csv_row(raw_row, column_mapping):
    """Turns one {csv_header: raw_string} row into a {canonical_field: value}
    dict shaped like what parse_listing_text would have extracted, using an
    admin-confirmed column_mapping instead of regex/LLM extraction.
    """
    parsed = {}
    for csv_header, canonical_field in (column_mapping or {}).items():
        if not canonical_field:
            continue
        raw_value = raw_row.get(csv_header)
        if raw_value is None or str(raw_value).strip() == "":
            continue
        value = str(raw_value).strip()

        if canonical_field in _CSV_NUMERIC_FIELDS:
            cleaned = value.replace(",", "").replace("$", "").lower().replace("km", "").strip()
            try:
                parsed[canonical_field] = _CSV_NUMERIC_FIELDS[canonical_field](float(cleaned))
            except ValueError:
                continue  # left unset -> reported as unresolved, never guessed
        elif canonical_field in ("title_status", "condition"):
            parsed[canonical_field] = value.lower()
        else:
            parsed[canonical_field] = value

    return parsed


def _finalize(parsed, raw_text_for_url_extraction=None):
    """Shared resolve -> validate -> dedup -> score tail for both a parsed
    paste and a mapped CSV row. `parsed` is a flat dict using the same key
    names as ALL_PARSEABLE_FIELDS plus optional trim/source_identifier/
    external_url.
    """
    make, model, generation, trim = resolve_vehicle(
        parsed.get("make"), parsed.get("model"), parsed.get("year"), parsed.get("trim")
    )
    location = resolve_location(parsed.get("location"))

    unresolved_fields = []
    validation_errors = []

    if parsed.get("make") is None:
        unresolved_fields.append("make")
    elif make is None:
        unresolved_fields.append("make")

    if parsed.get("model") is None:
        unresolved_fields.append("model")

    year = parsed.get("year")
    if year is None:
        unresolved_fields.append("year")
    elif not (MIN_YEAR <= year <= datetime.utcnow().year + 1):
        validation_errors.append("year")

    if make is not None and model is not None and generation is None:
        unresolved_fields.append("generation")

    if parsed.get("trim") and trim is None:
        unresolved_fields.append("trim")

    if parsed.get("location") and location is None:
        unresolved_fields.append("location")

    price = parsed.get("price")
    if price is None:
        unresolved_fields.append("price")
    elif not (0 < price <= MAX_PRICE):
        validation_errors.append("price")

    mileage_km = parsed.get("mileage_km")
    if mileage_km is None:
        unresolved_fields.append("mileage_km")
    elif not (0 <= mileage_km <= MAX_MILEAGE_KM):
        validation_errors.append("mileage_km")

    title_status = parsed.get("title_status")
    if title_status is None:
        unresolved_fields.append("title_status")
    elif title_status not in VALID_TITLE_STATUSES:
        validation_errors.append("title_status")

    fuel_type = parsed.get("fuel_type")
    if fuel_type is None:
        unresolved_fields.append("fuel_type")

    transmission = parsed.get("transmission")
    if transmission is None:
        unresolved_fields.append("transmission")

    condition = parsed.get("condition")
    if condition is not None and condition not in VALID_CONDITIONS:
        validation_errors.append("condition")

    # Dedup runs after every other check so it can only ever push a
    # would-be `pending` row to `needs_review`, never override a validation
    # problem found above.
    external_url = parsed.get("external_url") or extract_url(raw_text_for_url_extraction)
    url_hash = hash_url(external_url)
    source_identifier = parsed.get("source_identifier")
    resolvable_fields = {"generation_id": generation.id if generation else None, "year": year, "price": price, "mileage_km": mileage_km}
    duplicate, duplicate_reason = find_duplicate(resolvable_fields, url_hash=url_hash, source_identifier=source_identifier)
    is_duplicate = duplicate is not None

    review_status = "needs_review" if (validation_errors or unresolved_fields or is_duplicate) else "pending"

    quality_score, quality_factors = score_observation(
        validation_errors, unresolved_fields, is_duplicate, duplicate_reason
    )

    return {
        "generation_id": generation.id if generation else None,
        "trim_id": trim.id if trim else None,
        "location_id": location.id if location else None,
        "make_raw": parsed.get("make"),
        "model_raw": parsed.get("model"),
        "year": year,
        "mileage_km": mileage_km,
        "price": price,
        "title_status": title_status,
        "condition": condition,
        "transmission": transmission,
        "fuel_type": fuel_type,
        "source_identifier": source_identifier,
        "external_url": external_url,
        "url_hash": url_hash,
        "duplicate_of_observation_id": duplicate.id if duplicate else None,
        "quality_score": quality_score,
        "quality_factors": quality_factors or None,
        "review_status": review_status,
        "validation_errors": validation_errors or None,
        "unresolved_fields": unresolved_fields or None,
    }


def normalize_submission(raw_text: str) -> dict:
    """Returns a dict of ListingObservation-shaped fields, ready for a
    route to construct the row from. Never touches the database beyond the
    read-only catalog lookups needed for parsing/resolution/validation.
    """
    makes, models_by_make, location_names = _load_catalog_candidates()

    parsed = parse_listing_text(raw_text, makes, models_by_make, location_names)
    missing_fields = [field for field in ALL_PARSEABLE_FIELDS if field not in parsed]
    ai_fields = parse_missing_fields(raw_text, missing_fields, makes, models_by_make, location_names)
    parsed.update(ai_fields)

    return _finalize(parsed, raw_text_for_url_extraction=raw_text)


def normalize_csv_row(raw_row: dict, column_mapping: dict) -> dict:
    """Same output shape as normalize_submission, for one CSV row mapped
    through an admin-confirmed column_mapping (see suggest_column_mapping).
    """
    parsed = _map_csv_row(raw_row, column_mapping)
    return _finalize(parsed, raw_text_for_url_extraction=None)
