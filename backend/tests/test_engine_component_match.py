"""Proves the cross-generation engine-linked matching mechanism actually
works end to end - i.e. a known issue and maintenance item authored against
generation A surface for a listing of generation B when both share the same
Engine record, tagged with match_tier="engine_component", and that
match_type resolves to "engine_component" for that listing.

The seeded mock dataset (flask seed-db / seed_database()) doesn't reference
any Engine/GenerationEngine rows, so the main snapshot test never exercises
this path at all - this test builds its own small, self-contained set of
rows (and cleans them up afterward) specifically to cover it.
"""

from app.extensions import db
from app.models import (
    Engine,
    GenerationEngine,
    Generation,
    KnownIssue,
    Listing,
    Location,
    MaintenanceItem,
    VehicleMake,
    VehicleModel,
)
from app.services.known_issues import evaluate_known_issues
from app.services.maintenance_timeline import build_timeline
from app.services.match_type import ENGINE_COMPONENT, compute_match_type


def test_engine_linked_generation_surfaces_issue_and_maintenance(app):
    with app.app_context():
        make = VehicleMake(name="TestMake")
        db.session.add(make)
        db.session.flush()

        model = VehicleModel(make_id=make.id, name="TestModel")
        db.session.add(model)
        db.session.flush()

        source_gen = Generation(
            model_id=model.id, label="Gen A", start_year=2010, end_year=2015,
            body_type="sedan", drivetrain="FWD", base_horsepower=150,
            fuel_economy_l_per_100km=8.0, reliability_stars=4.0,
            typical_lifespan_km=300000, parts_availability="good",
            insurance_category="medium", expected_annual_maintenance_cost=800.0,
            base_value=10000.0, reference_mileage_km=100000,
        )
        target_gen = Generation(
            model_id=model.id, label="Gen B", start_year=2016, end_year=2020,
            body_type="sedan", drivetrain="FWD", base_horsepower=160,
            fuel_economy_l_per_100km=7.8, reliability_stars=4.0,
            typical_lifespan_km=300000, parts_availability="good",
            insurance_category="medium", expected_annual_maintenance_cost=800.0,
            base_value=12000.0, reference_mileage_km=100000,
        )
        db.session.add_all([source_gen, target_gen])
        db.session.flush()

        engine = Engine(name="TestEngine 2.0T")
        db.session.add(engine)
        db.session.flush()

        db.session.add_all([
            GenerationEngine(generation_id=source_gen.id, engine_id=engine.id),
            GenerationEngine(generation_id=target_gen.id, engine_id=engine.id),
        ])

        issue = KnownIssue(
            generation_id=source_gen.id,
            engine_id=engine.id,
            title="Timing chain tensioner failure",
            description="Known engine-family issue.",
            severity="severe",
            typical_mileage_km=100000,
            estimated_repair_cost_min=1500.0,
            estimated_repair_cost_max=3000.0,
            recommendation="Inspect before buying.",
        )
        maintenance = MaintenanceItem(
            generation_id=source_gen.id,
            engine_id=engine.id,
            name="Timing chain inspection",
            interval_km=100000,
            estimated_cost_min=200.0,
            estimated_cost_max=400.0,
        )
        # Deliberately NOT tagged with engine_id - an unrelated issue that
        # happens to live on an engine-linked generation (e.g. an
        # infotainment complaint) must never leak through as if it were
        # shared-engine evidence.
        unrelated_issue = KnownIssue(
            generation_id=source_gen.id,
            title="Infotainment screen lag",
            description="Unrelated to the shared engine.",
            severity="minor",
            typical_mileage_km=50000,
            estimated_repair_cost_min=0.0,
            estimated_repair_cost_max=200.0,
            recommendation="Software update usually resolves this.",
        )
        db.session.add_all([issue, maintenance, unrelated_issue])

        location = Location(city="TestCity", region="TestRegion", rust_belt_risk="low")
        db.session.add(location)
        db.session.flush()

        listing = Listing(
            generation_id=target_gen.id,
            location_id=location.id,
            engine_id=engine.id,
            year=2018,
            mileage_km=100000,
            price=15000.0,
            transmission="Automatic",
            seller_rating=4.5,
            days_listed=10,
        )
        db.session.add(listing)
        db.session.commit()

        try:
            issues = evaluate_known_issues(listing)
            assert len(issues) == 1
            assert issues[0]["title"] == "Timing chain tensioner failure"
            assert issues[0]["match_tier"] == "engine_component"
            assert "Infotainment screen lag" not in [i["title"] for i in issues]

            timeline = build_timeline(listing)
            all_items = timeline["immediate"] + timeline["soon"] + timeline["future"]
            assert len(all_items) == 1
            assert all_items[0]["name"] == "Timing chain inspection"
            assert all_items[0]["match_tier"] == "engine_component"

            assert compute_match_type(listing) == ENGINE_COMPONENT
        finally:
            db.session.delete(listing)
            db.session.delete(location)
            db.session.delete(issue)
            db.session.delete(maintenance)
            db.session.delete(unrelated_issue)
            db.session.query(GenerationEngine).filter_by(engine_id=engine.id).delete()
            db.session.delete(engine)
            db.session.delete(source_gen)
            db.session.delete(target_gen)
            db.session.delete(model)
            db.session.delete(make)
            db.session.commit()
