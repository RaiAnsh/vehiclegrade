"""An engine/powertrain family shared across generations (e.g. Volkswagen
Group's "EA888 Gen 3" 2.0T, used across several unrelated model generations).

This is what lets a known issue authored against one generation (where it was
actually reported) surface as relevant guidance for a *different* generation
that happens to share the same engine, instead of only ever matching the
exact generation it was entered against. See GenerationEngine for the
many-to-many link, and app.services.match_type for how this is surfaced.
"""

from app.extensions import db


class Engine(db.Model):
    __tablename__ = "engines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # "EA888 Gen 3 2.0T"
    description = db.Column(db.Text, nullable=True)

    generations = db.relationship("GenerationEngine", back_populates="engine")

    def __repr__(self):
        return f"<Engine {self.name}>"
