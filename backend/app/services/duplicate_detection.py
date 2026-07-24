"""Bronze -> Silver duplicate detection: catches the same real-world listing
being submitted more than once, so it can never be double-counted as two
separate market observations after approval.

Three signals, checked in order of certainty - the first one that fires
wins, since a stronger signal makes a weaker one redundant to check:
  1. Same source_identifier (an opaque ID a source site/CSV export exposes)
  2. Same url_hash (the exact same external listing URL was pasted/imported
     twice - url_hash is computed here from any URL found inside the raw
     pasted text, since paste submissions rarely have a separate URL field)
  3. Vehicle-field similarity: same resolved generation + same year, with
     price and mileage within a small tolerance band - catches copy-pasted
     listings that carry no URL/ID at all (the common "just the text" case)

Never merges or discards a record - only *flags* it (duplicate_of_observation_id
set, review_status forced to needs_review by the caller) so a human makes
the final call, matching this system's "nothing gets assumed on an admin's
behalf" rule from ingestion_normalizer.
"""

import hashlib
import re

from app.models import ListingObservation

URL_PATTERN = re.compile(r"https?://[^\s)>\]]+", re.IGNORECASE)

PRICE_TOLERANCE = 0.03  # +/- 3%
MILEAGE_TOLERANCE_KM = 1500

# A rejected observation was already judged not to matter, so new
# submissions are never flagged as a duplicate of one.
COMPARISON_STATUSES = ("pending", "needs_review", "approved")


def extract_url(raw_text):
    if not raw_text:
        return None
    match = URL_PATTERN.search(raw_text)
    return match.group(0).rstrip(").,]>") if match else None


def hash_url(url):
    if not url:
        return None
    normalized = url.strip().lower().rstrip("/")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_duplicate(fields, url_hash=None, source_identifier=None, exclude_observation_id=None):
    """Returns (duplicate_observation_or_None, reason_or_None)."""
    base_query = ListingObservation.query.filter(ListingObservation.review_status.in_(COMPARISON_STATUSES))
    if exclude_observation_id is not None:
        base_query = base_query.filter(ListingObservation.id != exclude_observation_id)

    if source_identifier:
        match = base_query.filter(ListingObservation.source_identifier == source_identifier).first()
        if match is not None:
            return match, "Same source_identifier as an existing observation"

    if url_hash:
        match = base_query.filter(ListingObservation.url_hash == url_hash).first()
        if match is not None:
            return match, "Same listing URL as an existing observation"

    generation_id = fields.get("generation_id")
    year = fields.get("year")
    price = fields.get("price")
    mileage_km = fields.get("mileage_km")

    if generation_id is not None and year is not None and price is not None and mileage_km is not None:
        price_low, price_high = price * (1 - PRICE_TOLERANCE), price * (1 + PRICE_TOLERANCE)
        candidates = base_query.filter(
            ListingObservation.generation_id == generation_id,
            ListingObservation.year == year,
            ListingObservation.price.isnot(None),
            ListingObservation.price.between(price_low, price_high),
            ListingObservation.mileage_km.isnot(None),
        ).all()
        for candidate in candidates:
            if abs(candidate.mileage_km - mileage_km) <= MILEAGE_TOLERANCE_KM:
                return candidate, "Same generation/year with matching price and mileage - likely the same vehicle"

    return None, None
