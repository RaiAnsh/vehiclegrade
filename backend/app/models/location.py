"""Locations where listings are posted."""

from app.extensions import db


class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(80), nullable=False)
    region = db.Column(db.String(20))

    # Drives the "rust risk" red flag - salt-heavy winter regions accelerate
    # frame/rocker/subframe corrosion regardless of the vehicle itself.
    rust_belt_risk = db.Column(db.String(10), nullable=False, default="low")  # low | medium | high

    listings = db.relationship("Listing", back_populates="location")

    def __repr__(self):
        return f"<Location {self.city}>"
