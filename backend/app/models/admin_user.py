"""An administrator/staff account for the Market Data Administration system.

Only one user exists in practice today, but the architecture is built for
many: role is a plain string column (same convention as
Listing.title_status/condition) rather than a hardcoded single-admin check,
so adding a second Reviewer or Analyst later is just an INSERT - no schema
or code change. Passwords are never stored or logged in plaintext; only
hash() should ever write to password_hash (see app.services.auth).
"""

from datetime import datetime

from app.extensions import db

VALID_ROLES = ("admin", "reviewer", "analyst")

# What each role may do. Kept as a single source of truth here (not spread
# across route decorators) so the permission set for a role is visible in
# one place. "analyst" is deliberately read-only - it must never appear in
# any mutating action's allowed-roles list.
ROLE_PERMISSIONS = {
    "admin": {
        "ingest", "review", "rollback", "manage_users", "view",
    },
    "reviewer": {
        "ingest", "review", "view",
    },
    "analyst": {
        "view",
    },
}


class AdminUser(db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="analyst")
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    refresh_tokens = db.relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    def has_permission(self, permission: str) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, set())

    def __repr__(self):
        return f"<AdminUser {self.email} ({self.role})>"
