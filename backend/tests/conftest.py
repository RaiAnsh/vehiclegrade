"""Shared pytest fixtures.

Points the app at a throwaway file-based SQLite database (never the real
dev/prod database) and seeds it with the same deterministic mock dataset
`flask seed-db` produces, so tests see a reproducible catalog/listing set.
"""

import os
import tempfile

import pytest

_DB_FD, _DB_PATH = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"

from app import create_app  # noqa: E402 - must follow the DATABASE_URL override above
from app.utils.seed_data import seed_database  # noqa: E402


@pytest.fixture(scope="session")
def app():
    flask_app = create_app()
    with flask_app.app_context():
        seed_database()
        yield flask_app

    os.close(_DB_FD)
    os.remove(_DB_PATH)
