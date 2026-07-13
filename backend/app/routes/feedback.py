"""POST /feedback - accepts free-text feedback from the beta feedback form."""

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Feedback

feedback_bp = Blueprint("feedback", __name__)

VALID_CATEGORIES = {"bug", "inaccuracy", "suggestion", "other"}


@feedback_bp.route("/feedback", methods=["POST"])
def submit_feedback():
    payload = request.get_json(silent=True) or {}

    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Missing required field: message"}), 400

    category = payload.get("category")
    if category is not None and category not in VALID_CATEGORIES:
        category = "other"

    feedback = Feedback(
        message=message[:5000],
        email=(payload.get("email") or "").strip()[:255] or None,
        category=category,
        page_url=(payload.get("page_url") or "").strip()[:500] or None,
    )
    db.session.add(feedback)
    db.session.commit()

    return jsonify({"status": "received"}), 201
