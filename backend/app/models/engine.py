"""An engine/powertrain family shared across generations (e.g. Volkswagen
Group's "EA888 Gen 3" 2.0T, used across several unrelated model generations).

This is what lets a known issue authored against one generation (where it was
actually reported) surface as relevant guidance for a *different* generation
that happens to share the same engine, instead of only ever matching the
exact generation it was entered against. See GenerationEngine for the
many-to-many link, and app.services.match_type for how this is surfaced.

Every row here is meant to be a real, identifiable engine family (a
manufacturer's actual internal code, e.g. "L15B7", "N20", "EA888 Gen 3") -
never a guess or a stand-in for "whatever this trim probably has". The
source_name/source_url/reviewed_at/confidence fields exist so each row's
provenance is auditable instead of being an opaque fact asserted by the app;
see app/utils/engine_data/ for the reviewed source data this table is
populated from.
"""

from app.extensions import db


class Engine(db.Model):
    __tablename__ = "engines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # "EA888 Gen 3 2.0T"
    description = db.Column(db.Text, nullable=True)

    # Structured identification - all nullable since older/incomplete rows
    # may not have every field reviewed yet.
    manufacturer = db.Column(db.String(50), nullable=True)  # "Honda", "Volkswagen Group"
    code = db.Column(db.String(30), nullable=True, index=True)  # "L15B7", "N20", "EA888 Gen 3"
    displacement_l = db.Column(db.Float, nullable=True)
    cylinders = db.Column(db.Integer, nullable=True)
    configuration = db.Column(db.String(10), nullable=True)  # I3 | I4 | I6 | V6 | V8
    aspiration = db.Column(db.String(20), nullable=True)  # naturally_aspirated | turbocharged
    fuel_type = db.Column(db.String(20), nullable=True)  # gasoline | diesel | hybrid
    production_start_year = db.Column(db.Integer, nullable=True)
    production_end_year = db.Column(db.Integer, nullable=True)

    # Provenance - who/what says this engine's data is correct, and how sure
    # we are. `confidence` is "verified" (widely documented, high certainty)
    # or "probable" (reasonable but not independently confirmed) - never
    # surfaced as fact-checked beyond what it actually is.
    source_name = db.Column(db.String(200), nullable=True)
    source_url = db.Column(db.String(500), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    confidence = db.Column(db.String(20), nullable=True)  # verified | probable

    generations = db.relationship("GenerationEngine", back_populates="engine")

    def __repr__(self):
        return f"<Engine {self.name}>"
