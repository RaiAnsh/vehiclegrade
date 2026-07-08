"""Locations where listings are posted."""

from app.extensions import db


class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(80), nullable=False)
    region = db.Column(db.String(20))

    # Not used yet - future-proofs a map view of nearby deals.
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)

    listings = db.relationship("Listing", back_populates="location")

    def __repr__(self):
        return f"<Location {self.city}>"
