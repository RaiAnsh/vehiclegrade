"""Shared Flask extension instances.

Defined here (instead of inside app/__init__.py) so models and services can
import `db` without triggering a circular import with the app factory.
"""

import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Applied selectively (see app.routes.auth) rather than globally - the
# public catalog/analyze endpoints don't need it, but auth endpoints
# (brute-force login protection) and the anonymous community-contribution
# endpoint do.
#
# Storage is set explicitly: with no storage_uri flask-limiter warns on every
# startup/CLI command. The default "memory://" behaves identically (per-process
# counters), which is fine for a single dev/small instance; set
# RATELIMIT_STORAGE_URI (e.g. a Redis URL) when running multiple workers.
limiter = Limiter(key_func=get_remote_address, storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"))
