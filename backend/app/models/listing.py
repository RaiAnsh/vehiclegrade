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

    year = db.Column(db.Integer, nullable=False)
    mileage_km = db.Column(db.Integer, nullable=False, index=True)
    price = db.Column(db.Float, nullable=False, index=True)

    transmission = db.Column(db.String(20), nullable=False)  # "Automatic" | "Manual" | "CVT"
    fuel_type = db.Column(db.String(20), nullable=False, default="Gasoline")
    title_status = db.Column(db.String(10), nullable=False, default="clean")
    condition = db.Column(db.String(10), nullable=False, default="good")  # excellent | good | fair | poor

    seller_rating = db.Column(db.Float, nullable=False)
    days_listed = db.Column(db.Integer, nullable=False)

    # Raw pasted text this listing was parsed from, if any - not used for
    # scoring, kept for reference/debugging the paste-parser.
    description_text = db.Column(db.Text, nullable=True)

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

    def __repr__(self):
        return f"<Listing #{self.id} gen={self.generation_id}>"
