"""Registers every blueprint with the Flask app."""

from app.routes.catalog import catalog_bp
from app.routes.listings import listings_bp
from app.routes.search import search_bp
from app.routes.analyze import analyze_bp
from app.routes.parse_listing import parse_listing_bp
from app.routes.stats import stats_bp
from app.routes.feedback import feedback_bp
from app.routes.community import community_bp
from app.routes.auth import auth_bp
from app.routes.admin_ingestion import admin_ingestion_bp
from app.routes.admin_review import admin_review_bp
from app.routes.admin_analytics import admin_analytics_bp
from app.routes.market_analytics import market_analytics_bp


def register_routes(app):
    app.register_blueprint(catalog_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(analyze_bp)
    app.register_blueprint(parse_listing_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_ingestion_bp)
    app.register_blueprint(admin_review_bp)
    app.register_blueprint(admin_analytics_bp)
    app.register_blueprint(market_analytics_bp)
