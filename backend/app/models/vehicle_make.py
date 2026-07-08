"""The catalog of supported vehicle manufacturers (Honda, Toyota, etc.)."""

from app.extensions import db


class VehicleMake(db.Model):
    __tablename__ = "vehicle_makes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    models = db.relationship("VehicleModel", back_populates="make")

    def __repr__(self):
        return f"<VehicleMake {self.name}>"
