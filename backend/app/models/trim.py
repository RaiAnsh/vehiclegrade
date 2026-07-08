"""A trim level within a generation (e.g. Civic 10th Gen -> EX)."""

from app.extensions import db


class Trim(db.Model):
    __tablename__ = "trims"

    id = db.Column(db.Integer, primary_key=True)
    generation_id = db.Column(db.Integer, db.ForeignKey("generations.id"), nullable=False, index=True)

    name = db.Column(db.String(30), nullable=False)  # "EX"
    msrp_adjustment_pct = db.Column(db.Float, nullable=False, default=0.0)  # -0.06 base ... +0.15 performance
    engine_options = db.Column(db.String(100), nullable=True)
    transmission_options = db.Column(db.String(100), nullable=True)

    generation = db.relationship("Generation", back_populates="trims")
    listings = db.relationship("Listing", back_populates="trim")

    def __repr__(self):
        return f"<Trim {self.name}>"
