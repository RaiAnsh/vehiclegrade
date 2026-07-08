"""Flask application factory.

Using a factory (instead of a global `app = Flask(__name__)`) keeps routes,
config, and the database instance decoupled - useful for testing and for
avoiding circular imports between models/services/routes.
"""

from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app)  # allow the Next.js dev server (different origin) to call this API

    with app.app_context():
        from app import models  # noqa: F401 - ensures models are registered with SQLAlchemy

        from app.routes import register_routes
        register_routes(app)

        from app.utils.cli import register_cli
        register_cli(app)

    return app
