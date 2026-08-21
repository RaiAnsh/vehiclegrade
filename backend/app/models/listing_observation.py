"""Silver layer: a normalized, validated candidate listing derived from one
RawListingSubmission, pending admin review before it can influence any
user-facing market estimate.

review_status is the single state machine gating everything downstream:
  pending      - passed validation, no duplicate/ambiguity concerns, awaiting review
  needs_review - validation gap, unresolved reference match, or suspected duplicate
  approved     - admin approved; materialized as a real Listing (Gold) via
                 approved_listing_id, and its MarketSegmentSummary recalculated
  rejected     - admin rejected; never becomes a Listing, rejection_reason required

Nothing outside app.routes.admin_review may change review_status - keeping
that written in exactly one place is what makes "unreviewed data can never
influence market estimates" an enforceable invariant rather than a
convention every call site has to remember.
"""

from datetime import datetime

from app.extensions import db

VALID_REVIEW_STATUSES = ("pending", "needs_review", "approved", "rejected")


class ListingObservation(db.Model):
    __tablename__ = "listing_observations"

    id = db.Column(db.Integer, primary_key=True)
    import_batch_id = db.Column(db.Integer, db.ForeignKey("import_batches.id"), nullable=False, index=True)
    raw_submission_id = db.Column(
        db.Integer, db.ForeignKey("raw_listing_submissions.id"), nullable=False, unique=True, index=True
    )

    # Resolved reference-data FKs. Nullable until (and unless) the
    # normalizer can confidently resolve them - an unresolved generation_id
    # is exactly what routes it to needs_review instead of pending.
    generation_id = db.Column(db.Integer, db.ForeignKey("generations.id"), nullable=True, index=True)
    trim_id = db.Column(db.Integer, db.ForeignKey("trims.id"), nullable=True)
    engine_id = db.Column(db.Integer, db.ForeignKey("engines.id"), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=True)

    # Normalized listing fields (same shape/validation as Listing).
    make_raw = db.Column(db.String(50), nullable=True)
    model_raw = db.Column(db.String(50), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    mileage_km = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Float, nullable=True)
    province = db.Column(db.String(30), nullable=True)
    title_status = db.Column(db.String(10), nullable=True)
    condition = db.Column(db.String(10), nullable=True)
    transmission = db.Column(db.String(50), nullable=True)
    fuel_type = db.Column(db.String(20), nullable=True)

    source_identifier = db.Column(db.String(120), nullable=True)  # opaque ID from source site, if any
    external_url = db.Column(db.String(500), nullable=True)
    url_hash = db.Column(db.String(64), nullable=True, index=True)  # sha256 of normalized external_url
    date_observed = db.Column(db.Date, nullable=True)

    review_status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    quality_score = db.Column(db.Integer, nullable=True)  # 0-100
    quality_factors = db.Column(db.JSON, nullable=True)  # [{"reason": str, "points": int}, ...]

    duplicate_of_observation_id = db.Column(db.Integer, db.ForeignKey("listing_observations.id"), nullable=True)

    validation_errors = db.Column(db.JSON, nullable=True)  # hard problems - field is present but invalid
    unresolved_fields = db.Column(db.JSON, nullable=True)  # soft gaps - field is missing/couldn't be matched

    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    # Free-text note a reviewer can attach on either outcome (approve or
    # reject) - separate from rejection_reason, which stays specific to
    # "why this was rejected" and is required by app.routes.admin_review's
    # reject endpoint. reviewer_note is optional context on any decision.
    reviewer_note = db.Column(db.Text, nullable=True)

    # Set on approval; this is the Silver -> Gold link. The materialized
    # Listing row is what market_comparables.py/stats_service.py/confidence.py
    # already query, so approval requires zero changes to those services.
    approved_listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    import_batch = db.relationship("ImportBatch", back_populates="observations")
    raw_submission = db.relationship("RawListingSubmission", back_populates="observation")
    generation = db.relationship("Generation")
    trim = db.relationship("Trim")
    engine = db.relationship("Engine")
    location = db.relationship("Location")
    reviewed_by = db.relationship("AdminUser")
    approved_listing = db.relationship("Listing")
    duplicate_of = db.relationship("ListingObservation", remote_side=[id])

    def __repr__(self):
        return f"<ListingObservation #{self.id} status={self.review_status}>"
