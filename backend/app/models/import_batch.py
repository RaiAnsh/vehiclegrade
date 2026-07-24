"""Bronze layer: a single ingestion event - one paste, one multi-paste, or
one CSV upload. Groups RawListingSubmission rows so a whole submission can
be reviewed, summarized, or rolled back together.
"""

from datetime import datetime

from app.extensions import db

VALID_SOURCE_TYPES = ("paste_single", "paste_multi", "csv_upload")
VALID_BATCH_STATUSES = ("open", "processing", "completed", "rolled_back")


class ImportBatch(db.Model):
    __tablename__ = "import_batches"

    id = db.Column(db.Integer, primary_key=True)

    source_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open")

    original_filename = db.Column(db.String(255), nullable=True)  # CSV uploads only
    # CSV header -> canonical field name, e.g. {"Odometer (km)": "mileage_km"}.
    # Null for paste-based batches, which have no columns to map.
    column_mapping = db.Column(db.JSON, nullable=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)

    row_count = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.Text, nullable=True)

    created_by = db.relationship("AdminUser")
    raw_submissions = db.relationship(
        "RawListingSubmission", back_populates="import_batch", cascade="all, delete-orphan"
    )
    observations = db.relationship("ListingObservation", back_populates="import_batch")

    def __repr__(self):
        return f"<ImportBatch #{self.id} {self.source_type} status={self.status}>"
