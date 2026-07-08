"""Free-text listing parser.

Best-effort regex/heuristic extraction of structured fields from a pasted
marketplace description, e.g.:

    "2014 Honda Civic EX, $6,500, 248,000 km, Automatic, 1.8L, Scarborough, Clean title"

This is explicitly heuristic, not ML - every extraction rule below is a
one-line regex or substring match. It never persists anything and never
guesses fields it can't find; the frontend prefills the manual form with
whatever it recovers and lets the user correct the rest.
"""

import re

YEAR_PATTERN = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")
PRICE_PATTERN = re.compile(r"\$\s?([\d,]+(?:\.\d{1,2})?)")
MILEAGE_PATTERN = re.compile(r"([\d,]+)\s?(?:km|kms|kilometers|miles|mi)\b", re.IGNORECASE)

TITLE_STATUS_KEYWORDS = [
    ("salvage", "salvage"),
    ("rebuilt", "rebuilt"),
    ("reconstructed", "rebuilt"),
    ("clean title", "clean"),
    ("clean", "clean"),
]

TRANSMISSION_KEYWORDS = [
    ("automatic", "Automatic"),
    ("auto", "Automatic"),
    ("cvt", "CVT"),
    ("manual", "Manual"),
    ("stick shift", "Manual"),
]

FUEL_TYPE_KEYWORDS = [
    ("diesel", "Diesel"),
    ("hybrid", "Hybrid"),
    ("electric", "Electric"),
    ("gas", "Gasoline"),
    ("gasoline", "Gasoline"),
]


def parse_listing_text(text, makes, models_by_make, location_names):
    """Best-effort extraction of listing fields from free text.

    `makes` is a list of make names, `models_by_make` maps make name -> list
    of model names, and `location_names` is a list of known city names -
    all loaded from the current catalog/locations so matching stays in sync
    with whatever the knowledge base actually contains.

    Returns a dict with only the keys it was able to confidently extract.
    """
    result = {}
    lower_text = text.lower()

    year_match = YEAR_PATTERN.search(text)
    if year_match:
        result["year"] = int(year_match.group(1))

    price_match = PRICE_PATTERN.search(text)
    if price_match:
        result["price"] = float(price_match.group(1).replace(",", ""))

    mileage_match = MILEAGE_PATTERN.search(text)
    if mileage_match:
        mileage_km = int(mileage_match.group(1).replace(",", ""))
        if "mile" in mileage_match.group(0).lower():
            mileage_km = round(mileage_km * 1.60934)
        result["mileage_km"] = mileage_km

    matched_make = next((make for make in makes if make.lower() in lower_text), None)
    if matched_make:
        result["make"] = matched_make
        candidate_models = models_by_make.get(matched_make, [])
        matched_model = next((model for model in candidate_models if model.lower() in lower_text), None)
        if matched_model:
            result["model"] = matched_model

    for keyword, status in TITLE_STATUS_KEYWORDS:
        if keyword in lower_text:
            result["title_status"] = status
            break

    for keyword, transmission in TRANSMISSION_KEYWORDS:
        if keyword in lower_text:
            result["transmission"] = transmission
            break

    for keyword, fuel_type in FUEL_TYPE_KEYWORDS:
        if keyword in lower_text:
            result["fuel_type"] = fuel_type
            break

    matched_location = next((city for city in location_names if city.lower() in lower_text), None)
    if matched_location:
        result["location"] = matched_location

    return result
