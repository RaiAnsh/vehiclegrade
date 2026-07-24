"""Bronze layer: the exact, unmodified thing an admin submitted - one pasted
block of text, or one CSV row. Never updated after insert; if parsing was
wrong, that's fixed by editing the resulting ListingObservation (Silver),
not this row. Keeping the original around is what lets a batch be
re-processed or audited against what was actually submitted.
"""

from datetime import datetime

from app.extensions import db


class RawListingSubmission(db.Model):
    __tablename__ = "raw_listing_submissions"

    id = db.Column(db.Integer, primary_key=True)
    import_batch_id = db.Column(db.Integer, db.ForeignKey("import_batches.id"), nullable=False, index=True)

    sequence_in_batch = db.Column(db.Integer, nullable=False)

    raw_text = db.Column(db.Text, nullable=True)  # pasted block (single or one chunk of a multi-paste)
    raw_row = db.Column(db.JSON, nullable=True)  # CSV row, verbatim original column values

    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    import_batch = db.relationship("ImportBatch", back_populates="raw_submissions")
    observation = db.relationship(
        "ListingObservation", back_populates="raw_submission", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<RawListingSubmission #{self.id} batch={self.import_batch_id}>"
