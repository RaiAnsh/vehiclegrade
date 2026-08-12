"""Gold layer: precomputed, explainable price statistics for one vehicle
generation, sliced along the dimensions a buyer or analyst actually asks
about - region, title status, mileage band - plus a grand-total rollup row.

This is a small, deliberately explicit data cube. SQLite (and, so far,
nothing this app runs on) has no `GROUPING SETS`, so instead of one giant
query this table is populated by app.services.market_aggregation running one
GROUP BY per dimension and writing one row per (generation, region,
title_status, mileage_band) combination it finds data for. Any dimension
not being sliced on a given row is stored as the ALL_DIMENSION_VALUE
sentinel rather than NULL - NULL isn't reliably unique-constrainable across
databases (SQLite treats every NULL as distinct), and a named "ALL" member
is exactly how a real OLAP rollup dimension is modeled anyway.

Rows are fully replaced (delete-then-insert) per generation on every
recompute, not incrementally updated. At this data volume a full recompute
is cheap and trivially correct; incremental percentile maintenance is a real
algorithm (e.g. t-digest) that would be solving a problem this dataset
doesn't have yet.
"""

from datetime import datetime

from app.extensions import db

ALL_DIMENSION_VALUE = "ALL"

MILEAGE_BANDS = [
    ("0-50k", 0, 50_000),
    ("50-100k", 50_000, 100_000),
    ("100-150k", 100_000, 150_000),
    ("150-200k", 150_000, 200_000),
    ("200k+", 200_000, None),
]


def mileage_band_for(mileage_km):
    """Return the band label a given mileage falls into, or None if mileage
    is missing/negative (such rows are excluded from mileage-band slices,
    not silently bucketed).
    """
    if mileage_km is None or mileage_km < 0:
        return None
    for label, low, high in MILEAGE_BANDS:
        if mileage_km >= low and (high is None or mileage_km < high):
            return label
    return None


class MarketAggregate(db.Model):
    __tablename__ = "market_aggregates"
    __table_args__ = (
        db.UniqueConstraint(
            "generation_id", "region", "title_status", "mileage_band",
            name="uq_market_aggregate_segment",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    generation_id = db.Column(db.Integer, db.ForeignKey("generations.id"), nullable=False, index=True)

    # Each defaults to ALL_DIMENSION_VALUE for a rollup row that doesn't
    # slice on that dimension - see module docstring.
    region = db.Column(db.String(20), nullable=False, default=ALL_DIMENSION_VALUE)
    title_status = db.Column(db.String(10), nullable=False, default=ALL_DIMENSION_VALUE)
    mileage_band = db.Column(db.String(10), nullable=False, default=ALL_DIMENSION_VALUE)

    sample_size = db.Column(db.Integer, nullable=False)
    min_price = db.Column(db.Float, nullable=False)
    max_price = db.Column(db.Float, nullable=False)
    avg_price = db.Column(db.Float, nullable=False)
    median_price = db.Column(db.Float, nullable=False)
    price_p25 = db.Column(db.Float, nullable=False)
    price_p75 = db.Column(db.Float, nullable=False)
    price_stddev = db.Column(db.Float, nullable=True)  # null when sample_size < 2 - stddev is undefined for n<2
    avg_mileage_km = db.Column(db.Integer, nullable=False)

    # Same tiering convention as app.services.confidence: <5 low, <10
    # medium, >=10 high. Kept here (not recomputed by the API) so a report
    # can show "why" without re-deriving it from sample_size at read time.
    market_confidence = db.Column(db.String(10), nullable=False)  # low | medium | high

    # Explicit data lineage: which Listing rows this aggregate was computed
    # from, capped so a very popular generation doesn't grow this unbounded.
    # This is what makes "explain your math" possible after the fact.
    sample_listing_ids = db.Column(db.JSON, nullable=True)

    computed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    generation = db.relationship("Generation")

    def __repr__(self):
        return (
            f"<MarketAggregate gen={self.generation_id} region={self.region} "
            f"title={self.title_status} mileage={self.mileage_band} n={self.sample_size}>"
        )
