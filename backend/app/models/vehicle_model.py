"""A model line within a make (e.g. Honda -> Civic)."""

from app.extensions import db


class VehicleModel(db.Model):
    __tablename__ = "vehicle_models"

    id = db.Column(db.Integer, primary_key=True)
    make_id = db.Column(db.Integer, db.ForeignKey("vehicle_makes.id"), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)

    make = db.relationship("VehicleMake", back_populates="models")
    generations = db.relationship("Generation", back_populates="model")

    def __repr__(self):
        return f"<VehicleModel {self.name}>"
