"""A recurring maintenance item for a generation (e.g. transmission fluid every 100,000 km)."""

from app.extensions import db


class MaintenanceItem(db.Model):
    __tablename__ = "maintenance_items"

    id = db.Column(db.Integer, primary_key=True)
    generation_id = db.Column(db.Integer, db.ForeignKey("generations.id"), nullable=False, index=True)
    # Optional: which engine this maintenance item is actually tied to, if
    # known (e.g. a turbo-specific interval). Nullable - see KnownIssue.engine_id.
    engine_id = db.Column(db.Integer, db.ForeignKey("engines.id"), nullable=True, index=True)

    name = db.Column(db.String(100), nullable=False)  # "Transmission fluid"
    interval_km = db.Column(db.Integer, nullable=False)
    estimated_cost_min = db.Column(db.Float, nullable=True)
    estimated_cost_max = db.Column(db.Float, nullable=True)

    generation = db.relationship("Generation", back_populates="maintenance_items")
    engine = db.relationship("Engine")

    def __repr__(self):
        return f"<MaintenanceItem {self.name}>"
