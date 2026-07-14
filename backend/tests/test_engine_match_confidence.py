"""Covers the engine-identification confidence layer end to end:

- exact generation+engine match (listing.engine_id set directly)
- shared engine across different generations (delegated to
  test_engine_component_match.py, which already proves this)
- multiple possible engines recorded on a trim (ambiguous - not guessed)
- unknown engine fallback (no engine data at all for the generation)
- confidence score downgrade specifically when the engine can't be
  identified, both for "no trim at all" and "trim recorded but ambiguous"

Each test builds and tears down its own rows so it doesn't depend on (or
pollute) the shared seeded mock dataset used by the snapshot test.
"""

from app.extensions import db
from app.models import Engine, Generation, Listing, Location, Trim, VehicleMake, VehicleModel
from app.services.engine_match import AMBIGUOUS, EXACT, UNIDENTIFIED, compute_engine_match
from app.services.market_comparables import find_comparables, summarize_comparables
from app.services.confidence import AMBIGUOUS_ENGINE_PENALTY, NO_TRIM_PENALTY, compute_confidence


def _make_catalog_row(db_session):
    make = VehicleMake(name="TestMake")
    db_session.add(make)
    db_session.flush()

    model = VehicleModel(make_id=make.id, name="TestModel")
    db_session.add(model)
    db_session.flush()

    generation = Generation(
        model_id=model.id, label="Gen X", start_year=2015, end_year=2020,
        body_type="sedan", drivetrain="FWD", base_horsepower=150,
        fuel_economy_l_per_100km=8.0, reliability_stars=4.0,
        typical_lifespan_km=300000, parts_availability="good",
        insurance_category="medium", expected_annual_maintenance_cost=800.0,
        base_value=10000.0, reference_mileage_km=100000,
    )
    db_session.add(generation)
    db_session.flush()

    location = Location(city="TestCity", region="TestRegion", rust_belt_risk="low")
    db_session.add(location)
    db_session.flush()

    return make, model, generation, location


def _make_listing(generation, location, trim=None, engine_id=None):
    return Listing(
        generation_id=generation.id,
        trim_id=trim.id if trim else None,
        location_id=location.id,
        engine_id=engine_id,
        year=2018,
        mileage_km=100000,
        price=15000.0,
        transmission="Automatic",
        seller_rating=4.5,
        days_listed=10,
    )


def _cleanup(*rows):
    for row in rows:
        if row is not None:
            db.session.delete(row)
    db.session.commit()


def test_exact_engine_match_when_listing_engine_id_set(app):
    with app.app_context():
        make, model, generation, location = _make_catalog_row(db.session)
        engine = Engine(name="TestEngine 2.0T")
        db.session.add(engine)
        db.session.flush()

        listing = _make_listing(generation, location, engine_id=engine.id)
        db.session.add(listing)
        db.session.commit()

        try:
            assert compute_engine_match(listing) == EXACT
        finally:
            _cleanup(listing, engine, generation, model, make, location)


def test_exact_engine_match_via_trim_engine_id(app):
    with app.app_context():
        make, model, generation, location = _make_catalog_row(db.session)
        engine = Engine(name="TestEngine 2.0T")
        db.session.add(engine)
        db.session.flush()

        trim = Trim(generation_id=generation.id, name="EX", engine_id=engine.id, engine_options="2.0L I4")
        db.session.add(trim)
        db.session.flush()

        listing = _make_listing(generation, location, trim=trim)
        db.session.add(listing)
        db.session.commit()

        try:
            assert compute_engine_match(listing) == EXACT
        finally:
            _cleanup(listing, trim, engine, generation, model, make, location)


def test_ambiguous_when_trim_lists_multiple_engine_options(app):
    """A trim whose own engine_options string lists more than one engine
    (e.g. a Ford F-150 XL trim listing both a 3.3L and 3.5L V6) must not be
    force-matched to either - the ambiguity should be preserved.
    """
    with app.app_context():
        make, model, generation, location = _make_catalog_row(db.session)

        trim = Trim(generation_id=generation.id, name="XL", engine_options="3.3L V6, 3.5L V6")
        db.session.add(trim)
        db.session.flush()

        listing = _make_listing(generation, location, trim=trim)
        db.session.add(listing)
        db.session.commit()

        try:
            assert compute_engine_match(listing) == AMBIGUOUS
        finally:
            _cleanup(listing, trim, generation, model, make, location)


def test_unidentified_when_no_engine_data_at_all(app):
    with app.app_context():
        make, model, generation, location = _make_catalog_row(db.session)

        listing = _make_listing(generation, location)
        db.session.add(listing)
        db.session.commit()

        try:
            assert compute_engine_match(listing) == UNIDENTIFIED
        finally:
            _cleanup(listing, generation, model, make, location)


def test_confidence_downgrades_when_trim_missing(app):
    with app.app_context():
        make, model, generation, location = _make_catalog_row(db.session)
        listing = _make_listing(generation, location)
        db.session.add(listing)
        db.session.commit()

        try:
            comparables, band_applied = find_comparables(listing)
            summary = summarize_comparables(listing, comparables, band_applied)
            confidence = compute_confidence(listing, summary)

            reasons = [f["reason"] for f in confidence["factors"]]
            assert any("Trim/engine not identified" in r for r in reasons)
            assert -NO_TRIM_PENALTY in [f["points"] for f in confidence["factors"]]
        finally:
            _cleanup(listing, generation, model, make, location)


def test_confidence_downgrades_when_engine_ambiguous_despite_known_trim(app):
    """A trim IS identified, but its recorded engine_options are ambiguous -
    this should cost points distinctly from (and smaller than) the
    no-trim-at-all case, and should not double up with NO_TRIM_PENALTY since
    a trim was in fact found.
    """
    with app.app_context():
        make, model, generation, location = _make_catalog_row(db.session)
        trim = Trim(generation_id=generation.id, name="XL", engine_options="3.3L V6, 3.5L V6")
        db.session.add(trim)
        db.session.flush()

        listing = _make_listing(generation, location, trim=trim)
        db.session.add(listing)
        db.session.commit()

        try:
            comparables, band_applied = find_comparables(listing)
            summary = summarize_comparables(listing, comparables, band_applied)
            confidence = compute_confidence(listing, summary)

            reasons = [f["reason"] for f in confidence["factors"]]
            assert any("more than one possible engine" in r for r in reasons)
            assert not any("Trim/engine not identified" in r for r in reasons)
            assert -AMBIGUOUS_ENGINE_PENALTY in [f["points"] for f in confidence["factors"]]
        finally:
            _cleanup(listing, trim, generation, model, make, location)
