"""A user-submitted comparable listing, contributed anonymously.

Deliberately whitelist-only: every column is a plain structured field
(year/make/model/etc.) and there is no free-text column at all anywhere on
this table - no description, no seller notes, nothing a contributor could
accidentally paste PII into. Write-only for now (see
app.routes.community) - not yet surfaced as reliable market data anywhere
in the app until a large enough reviewed sample exists.
"""

from datetime import datetime

from app.extensions import db


class CommunityComparable(db.Model):
    __tablename__ = "community_comparables"

    id = db.Column(db.Integer, primary_key=True)

    year = db.Column(db.Integer, nullable=False)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    trim = db.Column(db.String(30), nullable=True)
    price = db.Column(db.Float, nullable=False)
    mileage_km = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(10), nullable=False)  # excellent | good | fair | poor
    title_status = db.Column(db.String(10), nullable=False)  # clean | rebuilt | salvage | unknown
    province = db.Column(db.String(30), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    date_observed = db.Column(db.Date, nullable=True)
    # Where the contributor saw this listing - a fixed category, never a URL
    # or free text, so this can't be used to smuggle a link/PII through.
    source_category = db.Column(db.String(30), nullable=True)  # marketplace | dealer | auction | other

    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # Manual review flag - contributed data isn't used anywhere until a
    # person has reviewed it for plausibility.
    is_reviewed = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<CommunityComparable {self.year} {self.make} {self.model}>"
