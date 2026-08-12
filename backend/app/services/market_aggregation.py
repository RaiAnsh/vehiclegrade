"""Bronze/Silver -> Gold: turns the Listing table (Gold's own source of
truth - already the materialized output of admin approval, see
app.routes.admin_review) into MarketAggregate rows.

This is the ETL step of the medallion architecture: deterministic,
re-runnable, and fully explained by the source rows it names in
`sample_listing_ids`. It reads Listing directly rather than
ListingObservation, since an approved-but-since-archived Listing is exactly
the kind of "un-fresh" data a rollback should remove from market math - and
`Listing.is_archived` already encodes that.

`recompute_generation(generation_id)` is called synchronously wherever the
Listing table changes for that generation (an admin approval or a batch
rollback - see app.routes.admin_review) and by
`recompute_all_generations()`, exposed as both a CLI command
(`flask recompute-market-aggregates`) and an admin endpoint for a manual
full refresh.
"""

from collections import defaultdict
from datetime import datetime
from statistics import mean, median, pstdev

from app.extensions import db
from app.models import Generation, Listing
from app.models.market_aggregate import ALL_DIMENSION_VALUE, MarketAggregate, mileage_band_for

MAX_SAMPLE_LISTING_IDS = 50

THIN_SAMPLE_THRESHOLD = 5   # < this -> low confidence, matches confidence.py's THIN_COMPARABLES_PENALTY cutoff
FULL_SAMPLE_THRESHOLD = 10  # < this -> medium, >= this -> high, matches confidence.py's LIMITED_COMPARABLES_PENALTY cutoff


def _percentile(sorted_values, pct):
    """Nearest-rank percentile - no numpy dependency, and easy to hand-verify
    against a small sample, which matters for a number this module has to be
    able to explain.
    """
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = pct / 100 * (len(sorted_values) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = rank - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction


def _confidence_tier(sample_size):
    if sample_size < THIN_SAMPLE_THRESHOLD:
        return "low"
    if sample_size < FULL_SAMPLE_THRESHOLD:
        return "medium"
    return "high"


def _build_row(generation_id, region, title_status, mileage_band, listings):
    prices = sorted(listing.price for listing in listings)
    mileages = [listing.mileage_km for listing in listings]

    return MarketAggregate(
        generation_id=generation_id,
        region=region,
        title_status=title_status,
        mileage_band=mileage_band,
        sample_size=len(listings),
        min_price=min(prices),
        max_price=max(prices),
        avg_price=round(mean(prices), 2),
        median_price=round(median(prices), 2),
        price_p25=round(_percentile(prices, 25), 2),
        price_p75=round(_percentile(prices, 75), 2),
        price_stddev=round(pstdev(prices), 2) if len(prices) >= 2 else None,
        avg_mileage_km=round(mean(mileages)),
        market_confidence=_confidence_tier(len(listings)),
        sample_listing_ids=[listing.id for listing in listings[:MAX_SAMPLE_LISTING_IDS]],
        computed_at=datetime.utcnow(),
    )


def _grouped_rows(generation_id, listings):
    """Yield one MarketAggregate per rollup: the grand total, then one row
    per distinct value actually present in the data for each of region /
    title_status / mileage_band individually. This is a "one dimension at a
    time" cube, not a full cross-product cube (region x title x mileage) -
    at this data volume a full cross-product would mostly produce
    sample_size=1 rows with no statistical meaning, so it's deliberately
    left out rather than built and then hidden behind a confidence floor.
    """
    if not listings:
        return

    yield _build_row(generation_id, ALL_DIMENSION_VALUE, ALL_DIMENSION_VALUE, ALL_DIMENSION_VALUE, listings)

    by_region = defaultdict(list)
    by_title_status = defaultdict(list)
    by_mileage_band = defaultdict(list)
    for listing in listings:
        region = (listing.location.region if listing.location and listing.location.region else None)
        if region:
            by_region[region].append(listing)
        by_title_status[listing.title_status].append(listing)
        band = mileage_band_for(listing.mileage_km)
        if band:
            by_mileage_band[band].append(listing)

    for region, rows in by_region.items():
        yield _build_row(generation_id, region, ALL_DIMENSION_VALUE, ALL_DIMENSION_VALUE, rows)
    for title_status, rows in by_title_status.items():
        yield _build_row(generation_id, ALL_DIMENSION_VALUE, title_status, ALL_DIMENSION_VALUE, rows)
    for band, rows in by_mileage_band.items():
        yield _build_row(generation_id, ALL_DIMENSION_VALUE, ALL_DIMENSION_VALUE, band, rows)


def recompute_generation(generation_id, commit=True):
    """Full delete-then-insert refresh of every MarketAggregate row for one
    generation. Returns the number of rows written (0 if the generation now
    has no non-archived listings - its old aggregate rows are removed
    rather than left stale).
    """
    MarketAggregate.query.filter_by(generation_id=generation_id).delete()

    listings = Listing.query.filter(
        Listing.generation_id == generation_id, Listing.is_archived.is_(False),
    ).all()

    rows_written = 0
    for row in _grouped_rows(generation_id, listings):
        db.session.add(row)
        rows_written += 1

    if commit:
        db.session.commit()
    else:
        db.session.flush()

    return rows_written


def recompute_all_generations():
    """Full refresh across every generation that has at least one listing.
    Returns {generation_id: rows_written}. Used by the CLI command and the
    admin manual-recompute endpoint - not called on a hot request path.
    """
    generation_ids = [
        row[0] for row in db.session.query(Listing.generation_id).distinct().all()
    ]
    # A generation that used to have listings but no longer does (all
    # archived/rolled back) still needs its stale aggregates cleared.
    generation_ids_with_stale_aggregates = [
        row[0] for row in db.session.query(MarketAggregate.generation_id).distinct().all()
    ]
    all_ids = sorted(set(generation_ids) | set(generation_ids_with_stale_aggregates))

    results = {}
    for generation_id in all_ids:
        results[generation_id] = recompute_generation(generation_id, commit=False)
    db.session.commit()
    return results
