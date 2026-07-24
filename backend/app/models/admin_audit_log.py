"""Append-only audit trail for every admin auth event and every ingestion
state change (batch create, process, approve, reject, rollback, user
management). Never updated or deleted after insert - if an action needs to
be undone, that's a new row (e.g. "rollback"), not an edit to this table.

Written via app.services.audit_log.record() so every call site captures the
same shape (actor, action, target, previous values, request metadata)
instead of each route hand-rolling its own logging.
"""

from datetime import datetime

from app.extensions import db


class AdminAuditLog(db.Model):
    __tablename__ = "admin_audit_logs"

    id = db.Column(db.Integer, primary_key=True)

    # Nullable: some events (e.g. a failed login with a bad email) have no
    # authenticated actor yet still need to be logged.
    actor_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=True, index=True)
    actor_email = db.Column(db.String(255), nullable=True)  # denormalized so log reads survive user deletion

    action = db.Column(db.String(60), nullable=False, index=True)  # e.g. "observation.approve"
    target_type = db.Column(db.String(60), nullable=True)  # e.g. "ListingObservation"
    target_id = db.Column(db.Integer, nullable=True)

    # What changed, and what else it affected - e.g. an approval's
    # previous_values might be {"review_status": "pending"} and
    # affected_record_ids might list the MarketSegmentSummary rows
    # recalculated as a result.
    previous_values = db.Column(db.JSON, nullable=True)
    affected_record_ids = db.Column(db.JSON, nullable=True)

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    actor = db.relationship("AdminUser")

    def __repr__(self):
        return f"<AdminAuditLog {self.action} by={self.actor_email}>"
