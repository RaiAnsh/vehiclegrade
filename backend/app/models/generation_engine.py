"""Many-to-many link between a Generation and the Engine(s) it was offered
with. A generation can offer more than one engine option, and the same
engine family commonly spans several unrelated generations/models.
"""

from app.extensions import db


class GenerationEngine(db.Model):
    __tablename__ = "generation_engines"
    __table_args__ = (db.UniqueConstraint("generation_id", "engine_id", name="uq_generation_engine"),)

    id = db.Column(db.Integer, primary_key=True)
    generation_id = db.Column(db.Integer, db.ForeignKey("generations.id"), nullable=False, index=True)
    engine_id = db.Column(db.Integer, db.ForeignKey("engines.id"), nullable=False, index=True)

    generation = db.relationship("Generation", back_populates="engines")
    engine = db.relationship("Engine", back_populates="generations")

    def __repr__(self):
        return f"<GenerationEngine generation={self.generation_id} engine={self.engine_id}>"
