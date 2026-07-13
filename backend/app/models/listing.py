"""A single used-vehicle listing."""

from datetime import datetime

from app.extensions import db

VALID_TITLE_STATUSES = ("clean", "rebuilt", "salvage", "unknown")


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)

    generation_id = db.Column(db.Integer, db.ForeignKey("generations.id"), nullable=False, index=True)
    trim_id = db.Column(db.Integer, db.ForeignKey("trims.id"), nullable=True, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False, index=True)
    # Optional: the specific Engine this listing actually has, if known (e.g.
    # user-supplied or parsed from a description). Nullable - falls back to
    # trim.engine_id / generation-level matching when absent.
    engine_id = db.Column(db.Integer, db.ForeignKey("engines.id"), nullable=True, index=True)

    year = db.Column(db.Integer, nullable=False)
    mileage_km = db.Column(db.Integer, nullable=False, index=True)
    price = db.Column(db.Float, nullable=False, index=True)

    # Optional VIN, when the user has one - never required, never used for
    # scoring (VIN-decoded specs would just duplicate the reference data this
    # app already has). Purely a reference/lookup convenience.
    vin = db.Column(db.String(17), nullable=True)

    transmission = db.Column(db.String(50), nullable=False)  # e.g. "Automatic", "Manual", "8-speed Tiptronic Automatic"
    fuel_type = db.Column(db.String(20), nullable=False, default="Gasoline")
    title_status = db.Column(db.String(10), nullable=False, default="clean")
    condition = db.Column(db.String(10), nullable=False, default="good")  # excellent | good | fair | poor

    seller_rating = db.Column(db.Float, nullable=False)
    days_listed = db.Column(db.Integer, nullable=False)

    # Raw pasted text this listing was parsed from, if any - not used for
    # scoring, kept for reference/debugging the paste-parser.
    description_text = db.Column(db.Text, nullable=True)

    # Optional photo URL - either pasted in manually alongside a real listing
    # (Kijiji/AutoTrader/FB Marketplace/etc.), or left blank. Purely
    # cosmetic - never used by any scoring or valuation logic.
    image_url = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Future-proofs a real scraper: where the listing came from, and a link
    # back to the original post. Both unused while data is mock.
    source = db.Column(db.String(30), nullable=False, default="mock")
    external_url = db.Column(db.String(255), nullable=True)

    # Freshness/lifecycle tracking for a future real scraper - lets duplicate
    # postings be recognized and sold/removed listings archived out of
    # "comparable listings" math instead of deleted outright.
    first_seen_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)

    generation = db.relationship("Generation", back_populates="listings")
    trim = db.relationship("Trim", back_populates="listings")
    location = db.relationship("Location", back_populates="listings")
    engine = db.relationship("Engine")

    def __repr__(self):
        return f"<Listing #{self.id} gen={self.generation_id}>"
