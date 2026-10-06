"""Flip ledger: log real buy -> hold -> sell flips and compare what actually
happened against the Flip Calculator's prediction. Personal-use tool, so it
lives behind the same admin auth/RBAC as the rest of /admin: reads need
"view", writes need "ingest".
"""

from datetime import date

from flask import Blueprint, g, jsonify, request

from app.extensions import db
from app.models import Flip, FlipExpense, VALID_EXPENSE_CATEGORIES
from app.routes.flip_calculator import resolve_vehicle
from app.services import audit_log
from app.services.flip_calculator import ONTARIO_RST_RATE, calculate_flip
from app.services.flip_ledger import portfolio_summary, summarize_flip
from app.services.reference_resolver import resolve_generation, resolve_trim
from app.utils.auth_decorators import require_permission

admin_flips_bp = Blueprint("admin_flips", __name__, url_prefix="/admin/flips")


def _parse_date(value, default=None):
    if value in (None, ""):
        return default
    return date.fromisoformat(value)


def _serialize(flip, include_detail=False):
    data = {
        "id": flip.id, "make": flip.make, "model": flip.model, "year": flip.year, "trim": flip.trim,
        "title_status": flip.title_status, "condition": flip.condition, "status": flip.status,
        "purchase_date": flip.purchase_date.isoformat(), "purchase_price": flip.purchase_price,
        "purchase_tax": flip.purchase_tax, "purchase_fees": flip.purchase_fees,
        "mileage_at_purchase": flip.mileage_at_purchase, "planned_months": flip.planned_months,
        "sale_date": flip.sale_date.isoformat() if flip.sale_date else None,
        "sale_price": flip.sale_price, "sale_fees": flip.sale_fees, "mileage_at_sale": flip.mileage_at_sale,
        "notes": flip.notes, "summary": summarize_flip(flip),
    }
    if include_detail:
        data["predicted"] = flip.predicted
        data["expenses"] = [
            {"id": e.id, "date": e.expense_date.isoformat(), "category": e.category, "amount": e.amount, "note": e.note}
            for e in flip.expenses
        ]
    return data


@admin_flips_bp.route("", methods=["GET"])
@require_permission("view")
def list_flips():
    flips = Flip.query.order_by(Flip.purchase_date.desc(), Flip.id.desc()).all()
    return jsonify({"flips": [_serialize(f) for f in flips], "portfolio": portfolio_summary(flips)})


@admin_flips_bp.route("/<int:flip_id>", methods=["GET"])
@require_permission("view")
def get_flip(flip_id):
    return jsonify(_serialize(Flip.query.get_or_404(flip_id), include_detail=True))


@admin_flips_bp.route("", methods=["POST"])
@require_permission("ingest")
def create_flip():
    payload = request.get_json(silent=True) or {}
    missing = [f for f in ("make", "model", "year", "mileage_km", "purchase_price") if payload.get(f) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    make, model, error = resolve_vehicle(payload)
    if error is not None:
        return error

    try:
        year = int(payload["year"])
        price = float(payload["purchase_price"])
        mileage = int(payload["mileage_km"])
        planned_months = float(payload.get("planned_months") or 3)
        purchase_date = _parse_date(payload.get("purchase_date"), date.today())
        tax = payload.get("purchase_tax")
        tax = round(price * ONTARIO_RST_RATE, 2) if tax in (None, "") else float(tax)
        fees = float(payload.get("purchase_fees") or 0)
        insurance_annual = payload.get("insurance_annual")
        insurance_annual = None if insurance_annual in (None, "") else float(insurance_annual)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid number or date (dates must be YYYY-MM-DD)."}), 400
    if price <= 0 or mileage < 0 or not (0 < planned_months <= 36):
        return jsonify({"error": "purchase_price must be > 0, mileage_km >= 0, planned_months between 0 and 36."}), 400

    generation = resolve_generation(model, year)
    if generation is None:
        return jsonify({"error": f"No generation of {make.name} {model.name} covers model year {year}."}), 400

    title_status = payload.get("title_status", "clean")
    condition = payload.get("condition", "good")
    prediction = calculate_flip(
        generation, resolve_trim(generation, payload.get("trim")), make.name,
        purchase_price=price, mileage_km=mileage, months_held=planned_months,
        title_status=title_status, condition=condition, insurance_annual=insurance_annual,
    )

    flip = Flip(
        created_by_id=g.current_user.id, generation_id=generation.id, make=make.name, model=model.name, year=year,
        trim=payload.get("trim") or None, title_status=title_status, condition=condition,
        purchase_date=purchase_date, purchase_price=price, purchase_tax=tax, purchase_fees=fees,
        mileage_at_purchase=mileage, planned_months=planned_months, predicted=prediction, notes=payload.get("notes"),
    )
    db.session.add(flip)
    db.session.flush()
    audit_log.record("flip.create", actor=g.current_user, target_type="Flip", target_id=flip.id)
    db.session.commit()
    return jsonify(_serialize(flip, include_detail=True)), 201


@admin_flips_bp.route("/<int:flip_id>", methods=["PATCH"])
@require_permission("ingest")
def update_flip(flip_id):
    flip = Flip.query.get_or_404(flip_id)
    payload = request.get_json(silent=True) or {}
    try:
        for field in ("purchase_price", "purchase_tax", "purchase_fees"):
            if field in payload:
                setattr(flip, field, float(payload[field]))
        if "purchase_date" in payload:
            flip.purchase_date = _parse_date(payload["purchase_date"], flip.purchase_date)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid number or date."}), 400
    if "notes" in payload:
        flip.notes = payload["notes"]
    audit_log.record("flip.update", actor=g.current_user, target_type="Flip", target_id=flip.id)
    db.session.commit()
    return jsonify(_serialize(flip, include_detail=True))


@admin_flips_bp.route("/<int:flip_id>/expenses", methods=["POST"])
@require_permission("ingest")
def add_expense(flip_id):
    flip = Flip.query.get_or_404(flip_id)
    payload = request.get_json(silent=True) or {}
    if payload.get("category") not in VALID_EXPENSE_CATEGORIES:
        return jsonify({"error": f"category must be one of {list(VALID_EXPENSE_CATEGORIES)}"}), 400
    try:
        amount = float(payload["amount"])
        expense_date = _parse_date(payload.get("date"), date.today())
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "amount (number) is required; date must be YYYY-MM-DD."}), 400
    if amount <= 0:
        return jsonify({"error": "amount must be > 0"}), 400

    db.session.add(FlipExpense(flip_id=flip.id, expense_date=expense_date, category=payload["category"],
                               amount=amount, note=(payload.get("note") or None)))
    db.session.commit()
    db.session.refresh(flip)
    return jsonify(_serialize(flip, include_detail=True)), 201


@admin_flips_bp.route("/<int:flip_id>/expenses/<int:expense_id>", methods=["DELETE"])
@require_permission("ingest")
def delete_expense(flip_id, expense_id):
    expense = FlipExpense.query.filter_by(id=expense_id, flip_id=flip_id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    return jsonify(_serialize(Flip.query.get(flip_id), include_detail=True))


@admin_flips_bp.route("/<int:flip_id>/sell", methods=["POST"])
@require_permission("ingest")
def sell_flip(flip_id):
    flip = Flip.query.get_or_404(flip_id)
    if flip.status == "sold":
        return jsonify({"error": "This flip is already marked sold."}), 400
    payload = request.get_json(silent=True) or {}
    try:
        sale_price = float(payload["sale_price"])
        sale_date = _parse_date(payload.get("sale_date"), date.today())
        sale_fees = float(payload.get("sale_fees") or 0)
        mileage = payload.get("mileage_at_sale")
        mileage = None if mileage in (None, "") else int(mileage)
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "sale_price (number) is required; dates must be YYYY-MM-DD."}), 400
    if sale_price <= 0:
        return jsonify({"error": "sale_price must be > 0"}), 400
    if sale_date < flip.purchase_date:
        return jsonify({"error": "sale_date cannot be before purchase_date."}), 400

    flip.status = "sold"
    flip.sale_price, flip.sale_date, flip.sale_fees, flip.mileage_at_sale = sale_price, sale_date, sale_fees, mileage
    audit_log.record("flip.sell", actor=g.current_user, target_type="Flip", target_id=flip.id)
    db.session.commit()
    return jsonify(_serialize(flip, include_detail=True))


@admin_flips_bp.route("/<int:flip_id>", methods=["DELETE"])
@require_permission("ingest")
def delete_flip(flip_id):
    flip = Flip.query.get_or_404(flip_id)
    audit_log.record("flip.delete", actor=g.current_user, target_type="Flip", target_id=flip.id,
                     previous_values={"make": flip.make, "model": flip.model, "year": flip.year,
                                      "purchase_price": flip.purchase_price})
    db.session.delete(flip)
    db.session.commit()
    return jsonify({"deleted": flip_id})
