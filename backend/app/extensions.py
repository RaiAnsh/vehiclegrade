"""Shared Flask extension instances.

Defined here (instead of inside app/__init__.py) so models and services can
import `db` without triggering a circular import with the app factory.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
