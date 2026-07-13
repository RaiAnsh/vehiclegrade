"""User-submitted feedback from the beta feedback form."""

from datetime import datetime

from app.extensions import db


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(255), nullable=True)  # optional, for follow-up only
    category = db.Column(db.String(30), nullable=True)  # bug | inaccuracy | suggestion | other
    page_url = db.Column(db.String(500), nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Feedback {self.id}>"
