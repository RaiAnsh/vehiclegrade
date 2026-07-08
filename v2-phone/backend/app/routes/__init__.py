"""Registers every blueprint with the Flask app."""

from app.routes.listings import listings_bp
from app.routes.search import search_bp
from app.routes.analyze import analyze_bp
from app.routes.stats import stats_bp


def register_routes(app):
    app.register_blueprint(listings_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(analyze_bp)
    app.register_blueprint(stats_bp)
