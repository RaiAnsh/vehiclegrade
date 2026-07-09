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


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)

    # Comma-separated list of allowed origins, e.g.
    # "https://vehiclegrade.com,https://www.vehiclegrade.com". Defaults to
    # "*" for local dev so the Next.js dev server can call this API without
    # any setup; production deployments must set this explicitly.
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
    origins = "*" if allowed_origins == "*" else [o.strip() for o in allowed_origins.split(",")]
    CORS(app, origins=origins)

    with app.app_context():
        from app import models  # noqa: F401 - ensures models are registered with SQLAlchemy

        from app.routes import register_routes
        register_routes(app)

        from app.utils.cli import register_cli
        register_cli(app)

    return app
