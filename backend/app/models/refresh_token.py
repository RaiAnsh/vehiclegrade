"""Server-side record of an issued refresh token.

The raw refresh token is only ever handed to the browser as an httpOnly
cookie - this table stores a SHA-256 hash of it (never the raw value), so a
database leak alone can't be used to mint sessions. Rotation-on-use
(replaced_by_id) plus revoked_at lets us detect and shut down a stolen
refresh token: if a hash is presented that's already revoked, every
descendant token in that chain is revoked too (see app.services.auth).

csrf_token_hash is a second, independent secret issued alongside the
refresh token and returned only in the login/refresh JSON body (never as a
cookie). Because the frontend and API are on different domains in
production, JS on the frontend can't read an API-domain cookie anyway - so
CSRF protection for the one cookie-authenticated endpoint (/auth/refresh)
works by requiring this value back as a custom header, proving the caller
is code that actually completed a prior login/refresh rather than a
cross-site form/script riding on the browser's auto-attached cookie.
"""

from datetime import datetime

from app.extensions import db


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=False, index=True)

    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)  # sha256 hex digest
    csrf_token_hash = db.Column(db.String(64), nullable=False)  # sha256 hex digest
    issued_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=True)
    # Set when this token is rotated out for a new one, so a reuse of a
    # revoked token can be traced forward and the whole chain killed.
    replaced_by_id = db.Column(db.Integer, db.ForeignKey("refresh_tokens.id"), nullable=True)

    ip_address = db.Column(db.String(45), nullable=True)  # IPv6-safe length
    user_agent = db.Column(db.String(255), nullable=True)

    user = db.relationship("AdminUser", back_populates="refresh_tokens")

    def is_valid(self) -> bool:
        return self.revoked_at is None and self.expires_at > datetime.utcnow()

    def __repr__(self):
        return f"<RefreshToken user={self.user_id} revoked={self.revoked_at is not None}>"
