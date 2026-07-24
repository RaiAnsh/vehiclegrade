"""Admin authentication primitives: password hashing, JWT access tokens, and
rotating refresh tokens with CSRF binding + reuse detection.

Design:
  - Access token: short-lived JWT (default 15 min), returned in the login/
    refresh JSON body and sent by the frontend as `Authorization: Bearer`.
    Never stored server-side - a leaked one self-expires quickly. Because
    browsers never auto-attach Authorization headers the way they do
    cookies, every Bearer-authenticated route is inherently CSRF-safe.
  - Refresh token: opaque random string, long-lived (default 7 days), set
    only as an httpOnly+Secure cookie so JS can never read it (mitigates
    XSS token theft). Only its SHA-256 hash is stored in the DB - a DB leak
    alone can't be replayed.
  - CSRF token: a second opaque random string issued alongside the refresh
    token, returned ONLY in the login/refresh JSON response body (never as
    a cookie - frontend and API are on different domains in production, so
    JS on the frontend couldn't read an API-domain cookie anyway). The
    frontend must echo it back as an `X-CSRF-Token` header on /auth/refresh
    and /auth/logout. A cross-site attacker riding on the auto-attached
    refresh cookie has no way to know this value, so this is what actually
    prevents CSRF against those two cookie-authenticated endpoints.
  - Rotation on every refresh: the old RefreshToken row is marked revoked
    and linked (replaced_by_id) to the new one. If a *revoked* token's hash
    is ever presented again, that's a strong signal of theft (the
    legitimate client would hold the new token, not the old one) - every
    still-valid token in that user's account is revoked, forcing re-login.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import current_app

from app.extensions import db
from app.models import RefreshToken

_hasher = PasswordHasher()


class AuthenticationError(Exception):
    """Raised for any invalid-credentials/invalid-token/CSRF-mismatch
    condition. Routes catch this and return 401 without leaking which part
    of the check failed.
    """


class TokenReuseDetected(AuthenticationError):
    """Raised when an already-revoked refresh token is presented again -
    treated as a possible theft, not just an expired session.
    """


# --- Passwords ---------------------------------------------------------

def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


# --- Access tokens (JWT) ------------------------------------------------

def generate_access_token(user) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=current_app.config["ACCESS_TOKEN_TTL_MINUTES"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm=current_app.config["JWT_ALGORITHM"])


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=[current_app.config["JWT_ALGORITHM"]])
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid or expired access token") from exc


# --- Refresh + CSRF tokens ------------------------------------------------

def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def issue_refresh_token(user, ip_address=None, user_agent=None) -> tuple[str, str, RefreshToken]:
    """Creates and persists a new refresh token + bound CSRF token. Caller
    is responsible for committing (routes batch this with the audit-log
    write in one transaction). Returns (raw_refresh_token, raw_csrf_token, row).
    """
    raw_refresh_token = secrets.token_urlsafe(48)
    raw_csrf_token = secrets.token_urlsafe(32)
    ttl_days = current_app.config["REFRESH_TOKEN_TTL_DAYS"]
    row = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(raw_refresh_token),
        csrf_token_hash=_hash_token(raw_csrf_token),
        expires_at=datetime.utcnow() + timedelta(days=ttl_days),
        ip_address=ip_address,
        user_agent=(user_agent or "")[:255],
    )
    db.session.add(row)
    return raw_refresh_token, raw_csrf_token, row


def rotate_refresh_token(raw_refresh_token: str, csrf_header_value: str, ip_address=None, user_agent=None):
    """Validates a presented refresh token + its bound CSRF header and
    issues a replacement pair.

    Raises TokenReuseDetected if the refresh token was already revoked
    (possible theft) - revokes every still-valid token for that user as a
    precaution, forcing re-login everywhere.
    Raises AuthenticationError if the token is unknown/expired, its CSRF
    header doesn't match, or its user is inactive.

    Returns (new_raw_refresh_token, new_raw_csrf_token, new_row, user).
    """
    token_hash = _hash_token(raw_refresh_token)
    row = RefreshToken.query.filter_by(token_hash=token_hash).first()
    if row is None:
        raise AuthenticationError("Unknown refresh token")

    if row.revoked_at is not None:
        _revoke_all_active_tokens_for_user(row.user_id)
        raise TokenReuseDetected("Refresh token reuse detected")

    if row.expires_at <= datetime.utcnow():
        raise AuthenticationError("Refresh token expired")

    if not hmac.compare_digest(_hash_token(csrf_header_value or ""), row.csrf_token_hash):
        raise AuthenticationError("CSRF token mismatch")

    user = row.user
    if user is None or not user.is_active:
        raise AuthenticationError("Account is inactive")

    new_raw_refresh, new_raw_csrf, new_row = issue_refresh_token(user, ip_address=ip_address, user_agent=user_agent)
    row.revoked_at = datetime.utcnow()
    db.session.flush()  # assign new_row.id before linking
    row.replaced_by_id = new_row.id

    return new_raw_refresh, new_raw_csrf, new_row, user


def revoke_refresh_token(raw_refresh_token: str) -> None:
    """Used for logout. Silently no-ops on an unknown/already-revoked token
    so logout is always idempotent from the client's perspective.
    """
    token_hash = _hash_token(raw_refresh_token)
    row = RefreshToken.query.filter_by(token_hash=token_hash).first()
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.utcnow()


def _revoke_all_active_tokens_for_user(user_id: int) -> None:
    now = datetime.utcnow()
    active = RefreshToken.query.filter(
        RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
    ).all()
    for token in active:
        token.revoked_at = now
