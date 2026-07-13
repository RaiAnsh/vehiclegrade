"""A commonly-reported mechanical issue for a generation, keyed to onset mileage.

This is the most important table in the knowledge base - it's what lets the
same issue read as "unlikely yet" on a 40,000 km Civic and "overdue - budget
for this" on a 250,000 km Civic of the same generation.
"""

from app.extensions import db


class KnownIssue(db.Model):
    __tablename__ = "known_issues"

    id = db.Column(db.Integer, primary_key=True)
    generation_id = db.Column(db.Integer, db.ForeignKey("generations.id"), nullable=False, index=True)
    # Optional: which engine this issue is actually caused by, if known. Lets
    # the same issue surface for other generations sharing that engine
    # (see app.services.match_type) instead of only ever matching the exact
    # generation it was authored against. Nullable - most existing rows won't
    # have this until reviewed.
    engine_id = db.Column(db.Integer, db.ForeignKey("engines.id"), nullable=True, index=True)

    title = db.Column(db.String(100), nullable=False)  # "AC compressor failure"
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(10), nullable=False)  # minor | moderate | severe
    typical_mileage_km = db.Column(db.Integer, nullable=False)  # onset mileage commonly seen
    estimated_repair_cost_min = db.Column(db.Float, nullable=False)
    estimated_repair_cost_max = db.Column(db.Float, nullable=False)
    # What a buyer would actually notice - sound, smell, warning light, behavior.
    symptoms = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=False)

    generation = db.relationship("Generation", back_populates="known_issues")
    engine = db.relationship("Engine")

    def __repr__(self):
        return f"<KnownIssue {self.title}>"
