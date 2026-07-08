"""The catalog of supported iPhone models."""

from app.extensions import db


class PhoneModel(db.Model):
    __tablename__ = "phone_models"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    release_year = db.Column(db.Integer, nullable=False)

    # Reference used-market value at the baseline spec: 128GB, good condition,
    # 85% battery health. The Market Value Engine adjusts up/down from here.
    base_value = db.Column(db.Float, nullable=False)

    listings = db.relationship("Listing", back_populates="model")

    def __repr__(self):
        return f"<PhoneModel {self.name}>"
