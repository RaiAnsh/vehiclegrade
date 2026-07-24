"""Shared Flask extension instances.

Defined here (instead of inside app/__init__.py) so models and services can
import `db` without triggering a circular import with the app factory.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Applied selectively (see app.routes.auth) rather than globally - the
# public catalog/analyze endpoints don't need it, but auth endpoints
# (brute-force login protection) and the anonymous community-contribution
# endpoint do.
limiter = Limiter(key_func=get_remote_address)
