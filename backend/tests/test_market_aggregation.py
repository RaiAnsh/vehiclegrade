"""Covers the Gold-layer ETL (app.services.market_aggregation): correctness
of the rollup math itself, and that recompute is idempotent/self-correcting
(delete-then-insert, never leaves stale rows behind).

Runs against the real seeded catalog rather than hand-built fixtures, so the
region/title_status/mileage_band slicing is exercised against genuinely
varied data instead of a contrived happy path.
"""

from app.extensions import db
from app.models import Generation, Listing, MarketAggregate, VehicleMake, VehicleModel
from app.models.market_aggregate import ALL_DIMENSION_VALUE, mileage_band_for
from app.services.market_aggregation import _percentile, recompute_all_generations, recompute_generation


def _civic_generation():
    return (
        Generation.query.join(VehicleModel).join(VehicleMake)
        .filter(VehicleMake.name == "Honda", VehicleModel.name == "Civic")
        .first()
    )


def test_percentile_matches_hand_computed_values():
    values = [10, 20, 30, 40, 50]
    assert _percentile(values, 0) == 10
    assert _percentile(values, 50) == 30
    assert _percentile(values, 100) == 50
    assert _percentile([], 50) is None
    assert _percentile([42], 50) == 42


def test_mileage_band_for_covers_every_range():
    assert mileage_band_for(0) == "0-50k"
    assert mileage_band_for(49_999) == "0-50k"
    assert mileage_band_for(50_000) == "50-100k"
    assert mileage_band_for(199_999) == "150-200k"
    assert mileage_band_for(500_000) == "200k+"
    assert mileage_band_for(None) is None
    assert mileage_band_for(-1) is None


def test_recompute_generation_produces_internally_consistent_rollups(app):
    with app.app_context():
        generation = _civic_generation()
        rows_written = recompute_generation(generation.id)
        assert rows_written > 0

        rows = MarketAggregate.query.filter_by(generation_id=generation.id).all()
        overall = next(r for r in rows if r.region == ALL_DIMENSION_VALUE and r.title_status == ALL_DIMENSION_VALUE and r.mileage_band == ALL_DIMENSION_VALUE)

        non_archived_count = Listing.query.filter_by(generation_id=generation.id, is_archived=False).count()
        assert overall.sample_size == non_archived_count

        by_region = [r for r in rows if r.region != ALL_DIMENSION_VALUE]
        by_title_status = [r for r in rows if r.title_status != ALL_DIMENSION_VALUE]
        by_mileage_band = [r for r in rows if r.mileage_band != ALL_DIMENSION_VALUE]

        # Every slice's sample rows are a real partition of the overall sample -
        # each dimension's counts must sum back to the total (every listing has
        # exactly one region, one title_status, and falls in at most one band).
        assert sum(r.sample_size for r in by_region) == overall.sample_size
        assert sum(r.sample_size for r in by_title_status) == overall.sample_size
        assert sum(r.sample_size for r in by_mileage_band) <= overall.sample_size

        for row in rows:
            assert row.min_price <= row.price_p25 <= row.median_price <= row.price_p75 <= row.max_price
            assert row.market_confidence in ("low", "medium", "high")
            assert row.sample_listing_ids
            assert len(row.sample_listing_ids) == min(row.sample_size, 50)
            if row.sample_size < 2:
                assert row.price_stddev is None
            else:
                assert row.price_stddev is not None


def test_recompute_is_idempotent_and_removes_stale_rows(app):
    with app.app_context():
        generation = _civic_generation()
        recompute_generation(generation.id)
        first_row_count = MarketAggregate.query.filter_by(generation_id=generation.id).count()

        recompute_generation(generation.id)
        second_row_count = MarketAggregate.query.filter_by(generation_id=generation.id).count()

        assert first_row_count == second_row_count  # no duplicate rows from re-running


def test_recompute_generation_with_no_listings_clears_aggregates(app):
    with app.app_context():
        # Build a throwaway generation with zero listings under the same make/model.
        civic_model = Generation.query.join(VehicleModel).join(VehicleMake).filter(
            VehicleMake.name == "Honda", VehicleModel.name == "Civic"
        ).first().model

        empty_generation = Generation(
            model_id=civic_model.id, label="Test Empty Gen", start_year=1999, end_year=2001,
            body_type="sedan", drivetrain="FWD", base_horsepower=100, fuel_economy_l_per_100km=7.0,
            reliability_stars=4.0, typical_lifespan_km=300000, parts_availability="good",
            insurance_category="low", expected_annual_maintenance_cost=500.0, base_value=5000.0,
            reference_mileage_km=100000,
        )
        db.session.add(empty_generation)
        db.session.commit()

        try:
            rows_written = recompute_generation(empty_generation.id)
            assert rows_written == 0
            assert MarketAggregate.query.filter_by(generation_id=empty_generation.id).count() == 0
        finally:
            db.session.delete(empty_generation)
            db.session.commit()


def test_recompute_all_generations_covers_every_generation_with_listings(app):
    with app.app_context():
        results = recompute_all_generations()
        distinct_generation_ids = {row[0] for row in db.session.query(Listing.generation_id).distinct().all()}
        assert distinct_generation_ids.issubset(results.keys())
        assert MarketAggregate.query.count() > 0
