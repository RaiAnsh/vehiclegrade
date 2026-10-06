"""Public flip tools that need no account: the level roadmap, and a stateless
ledger summary. Users' flips live in *their own browser* (localStorage); this
endpoint only does the arithmetic on whatever the browser sends, and stores
nothing.
"""

from datetime import date
from types import SimpleNamespace

from flask import Blueprint, jsonify, request

from app.extensions import limiter
from app.services.flip_ledger import VALID_EXPENSE_CATEGORIES, portfolio_summary, summarize_flip
from app.services.flip_roadmap import compute_progress, level_for, public_levels

flip_public_bp = Blueprint("flip_public", __name__, url_prefix="/flip")

MAX_FLIPS = 100
MAX_EXPENSES_PER_FLIP = 300


def _num(value, field, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < minimum:
        raise ValueError(f"{field} must be a number >= {minimum}")
    return float(value)


def _date(value, field):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be YYYY-MM-DD")


def _valid_prediction(p):
    """The snapshot is kept client-side, so only trust it if it has the shape
    the comparison reads; otherwise treat the flip as having no prediction."""
    try:
        for group in ("buying", "holding", "selling"):
            assert isinstance(p["costs"][group], dict)
        assert isinstance(p["costs"]["repair_reserve"], (int, float))
        assert isinstance(p["months_held"], (int, float)) and p["months_held"] > 0
        assert isinstance(p["expected_net"], (int, float))
        assert isinstance(p["scenarios"]["expected"]["sale_price"], (int, float))
        return p
    except (AssertionError, KeyError, TypeError):
        return None


def _build_flip(raw):
    if not isinstance(raw, dict):
        raise ValueError("each flip must be an object")
    status = raw.get("status")
    if status not in ("holding", "sold"):
        raise ValueError("status must be 'holding' or 'sold'")
    expenses = raw.get("expenses") or []
    if not isinstance(expenses, list) or len(expenses) > MAX_EXPENSES_PER_FLIP:
        raise ValueError("too many expenses")

    flip = SimpleNamespace(
        id=raw.get("id"), make=str(raw.get("make", ""))[:50], model=str(raw.get("model", ""))[:50],
        status=status,
        purchase_date=_date(raw.get("purchase_date"), "purchase_date"),
        purchase_price=_num(raw.get("purchase_price"), "purchase_price"),
        purchase_tax=_num(raw.get("purchase_tax", 0), "purchase_tax"),
        purchase_fees=_num(raw.get("purchase_fees", 0), "purchase_fees"),
        sale_date=None, sale_price=None, sale_fees=0.0,
        predicted=_valid_prediction(raw.get("predicted")) if raw.get("predicted") else None,
        expenses=[],
    )
    for e in expenses:
        if not isinstance(e, dict) or e.get("category") not in VALID_EXPENSE_CATEGORIES:
            raise ValueError("invalid expense category")
        flip.expenses.append(SimpleNamespace(category=e["category"], amount=_num(e.get("amount"), "amount")))
    if status == "sold":
        flip.sale_price = _num(raw.get("sale_price"), "sale_price")
        flip.sale_date = _date(raw.get("sale_date"), "sale_date")
        flip.sale_fees = _num(raw.get("sale_fees", 0), "sale_fees")
        if flip.sale_date < flip.purchase_date:
            raise ValueError("sale_date cannot be before purchase_date")
    return flip


@flip_public_bp.route("/roadmap", methods=["GET"])
def roadmap():
    return jsonify({"levels": public_levels()})


@flip_public_bp.route("/ledger/summarize", methods=["POST"])
@limiter.limit("60 per minute")
def summarize_ledger():
    payload = request.get_json(silent=True) or {}
    raw_flips = payload.get("flips")
    if not isinstance(raw_flips, list) or len(raw_flips) > MAX_FLIPS:
        return jsonify({"error": f"flips must be a list of at most {MAX_FLIPS}"}), 400
    try:
        flips = [_build_flip(raw) for raw in raw_flips]
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    summaries = {}
    sold = []
    for flip in flips:
        summary = summarize_flip(flip)
        summaries[str(flip.id)] = {"level": level_for(flip.make, flip.model), "summary": summary}
        if flip.status == "sold" and summary["actual_net"] is not None:
            sold.append((level_for(flip.make, flip.model), summary["actual_net"]))

    return jsonify({
        "flips": summaries,
        "portfolio": portfolio_summary(flips),
        "progress": compute_progress(sold),
    })
