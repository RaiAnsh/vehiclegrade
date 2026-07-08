"""GET /stats - dashboard stat cards + analytics chart data."""

from flask import Blueprint, jsonify

from app.services.stats_service import get_dashboard_stats

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/stats", methods=["GET"])
def get_stats():
    return jsonify(get_dashboard_stats())
