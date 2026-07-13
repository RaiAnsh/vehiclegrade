"""Flask application factory.

Using a factory (instead of a global `app = Flask(__name__)`) keeps routes,
config, and the database instance decoupled - useful for testing and for
avoiding circular imports between models/services/routes.
"""

import os

from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db
from app.services.error_tracking import init_error_tracking


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    init_error_tracking(app)

    db.init_app(app)

    # Comma-separated list of allowed origins, e.g.
    # "https://vehiclegrade.ca,https://www.vehiclegrade.ca". Defaults to
    # "*" for local dev so the Next.js dev server can call this API without
    # any setup; production deployments must set this explicitly.
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
    origins = "*" if allowed_origins == "*" else [o.strip() for o in allowed_origins.split(",")]
    CORS(app, origins=origins)

    with app.app_context():
        from app import models  # noqa: F401 - ensures models are registered with SQLAlchemy

        _sync_schema()

        from app.routes import register_routes
        register_routes(app)

        from app.utils.cli import register_cli
        register_cli(app)

    return app


def _sync_schema():
    """Additive-only schema sync: adds any columns that exist on a model but
    not yet on its table.

    This project has no migration tool (Flask-Migrate/Alembic) - the models
    are the only source of truth, and `seed-db` is a manual, destructive
    (drop + recreate) CLI command. That means a normal model change like
    adding a new nullable column (e.g. Listing.image_url) silently breaks
    every route touching that table in production until someone remembers to
    run a manual migration. Running this on every startup means a plain
    `git push` is enough to keep the live schema in sync - it only ever adds
    missing columns, never drops or alters existing ones, so it's safe to
    run unconditionally.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    for table in db.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_columns:
                continue
            if not column.nullable:
                # Adding a NOT NULL column to a table that already has rows
                # needs a default/backfill strategy - out of scope for this
                # auto-sync, so it's skipped rather than risking a startup
                # crash. New required columns still need a real migration.
                continue
            column_type = column.type.compile(dialect=db.engine.dialect)
            ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column_type}'
            with db.engine.begin() as conn:
                conn.execute(text(ddl))
