"""Application configuration.

Kept as a single class for V1/V2 since we only run one environment locally.
A future version could add DevelopmentConfig/ProductionConfig subclasses.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    # Flask-SQLAlchemy looks for the SQLite file relative to the instance folder.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'vehiclegrade.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    # --- Admin auth (app.services.auth) ---
    # Signs/verifies admin JWT access tokens. Must be set to a long random
    # value in production - the insecure fallback below only exists so local
    # dev/tests work with zero setup; _sync_schema-style "fail loud in prod"
    # checks aren't done here since Config has no environment concept yet,
    # but every deploy MUST set this via env var.
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-insecure-secret-do-not-use-in-production")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_TTL_MINUTES = int(os.environ.get("ACCESS_TOKEN_TTL_MINUTES", "15"))
    REFRESH_TOKEN_TTL_DAYS = int(os.environ.get("REFRESH_TOKEN_TTL_DAYS", "7"))

    # Refresh/CSRF cookies. Frontend and backend are on different domains in
    # production (Vercel/Railway), so cross-site cookies need SameSite=None
    # + Secure. Local dev (same-site http://localhost) uses Lax + non-Secure
    # so cookies work over plain HTTP without extra setup.
    REFRESH_COOKIE_SECURE = os.environ.get("REFRESH_COOKIE_SECURE", "false").lower() == "true"
    REFRESH_COOKIE_SAMESITE = os.environ.get("REFRESH_COOKIE_SAMESITE", "Lax")
    REFRESH_COOKIE_DOMAIN = os.environ.get("REFRESH_COOKIE_DOMAIN") or None

    # Flask-Limiter reads this. Left on by default; tests disable it via env
    # var so a whole test session sharing one app instance (and therefore
    # one in-memory rate-limit counter) doesn't trip limits meant for real
    # brute-force traffic.
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "true").lower() != "false"
