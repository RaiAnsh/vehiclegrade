"""A single used-phone listing."""

from datetime import datetime

from app.extensions import db

VALID_CONDITIONS = ("excellent", "good", "fair", "poor")


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)

    model_id = db.Column(db.Integer, db.ForeignKey("phone_models.id"), nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False, index=True)

    storage_gb = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False, index=True)
    battery_health = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(20), nullable=False)
    unlocked = db.Column(db.Boolean, nullable=False)
    seller_rating = db.Column(db.Float, nullable=False)
    days_listed = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Future-proofs a real scraper: where the listing came from, and a link
    # back to the original post. Both unused while data is mock.
    source = db.Column(db.String(30), nullable=False, default="mock")
    external_url = db.Column(db.String(255), nullable=True)

    model = db.relationship("PhoneModel", back_populates="listings")
    location = db.relationship("Location", back_populates="listings")

    def __repr__(self):
        return f"<Listing #{self.id} {self.model.name if self.model else self.model_id}>"
