"""A specific generation of a model (e.g. Civic 10th Gen, 2016-2021).

This is the heart of the knowledge base: every objective spec, reliability
figure, and cost estimate lives here, keyed only by generation - never by a
specific listing. The Market Value / Known Issues / Ownership Cost engines
all read from this table and never look at price or mileage.
"""

from app.extensions import db


class Generation(db.Model):
    __tablename__ = "generations"

    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey("vehicle_models.id"), nullable=False, index=True)

    label = db.Column(db.String(50), nullable=False)  # "10th Gen"
    start_year = db.Column(db.Integer, nullable=False)
    end_year = db.Column(db.Integer, nullable=False)

    body_type = db.Column(db.String(20), nullable=False)  # sedan | suv | truck | hatchback
    drivetrain = db.Column(db.String(10), nullable=False)  # FWD | AWD | RWD | 4WD
    base_horsepower = db.Column(db.Integer, nullable=False)
    fuel_economy_l_per_100km = db.Column(db.Float, nullable=False)

    reliability_stars = db.Column(db.Float, nullable=False)  # 1.0-5.0
    typical_lifespan_km = db.Column(db.Integer, nullable=False)
    parts_availability = db.Column(db.String(20), nullable=False)  # excellent | good | fair | poor
    insurance_category = db.Column(db.String(10), nullable=False)  # low | medium | high
    expected_annual_maintenance_cost = db.Column(db.Float, nullable=False)

    # Comma-separated, display-only - not worth a join table for a static list.
    common_competitors = db.Column(db.String(200), nullable=True)

    # Objective used-market value anchored to reference_mileage_km, clean
    # title, base trim. The Market Value Engine adjusts up/down from here.
    base_value = db.Column(db.Float, nullable=False)
    reference_mileage_km = db.Column(db.Integer, nullable=False)

    model = db.relationship("VehicleModel", back_populates="generations")
    trims = db.relationship("Trim", back_populates="generation")
    known_issues = db.relationship("KnownIssue", back_populates="generation")
    maintenance_items = db.relationship("MaintenanceItem", back_populates="generation")
    listings = db.relationship("Listing", back_populates="generation")

    def __repr__(self):
        return f"<Generation {self.label} ({self.start_year}-{self.end_year})>"
