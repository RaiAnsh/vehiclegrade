"""POST /flip-calculator - estimated profit/loss of a buy-hold-sell flip."""

from flask import Blueprint, jsonify, request

from app.models import VehicleMake, VehicleModel
from app.services.flip_calculator import calculate_flip
from app.services.reference_resolver import resolve_generation, resolve_make, resolve_model, resolve_trim

flip_calculator_bp = Blueprint("flip_calculator", __name__)

REQUIRED_FIELDS = ["make", "model", "year", "mileage_km", "purchase_price", "months_held"]


def resolve_vehicle(payload):
    """Returns (make, model, None) or (None, None, (json_response, 400)). Shared with the flip ledger."""
    make = resolve_make(payload["make"])
    if make is None:
        supported = [m.name for m in VehicleMake.query.all()]
        return None, None, (jsonify({"error": f"Unsupported make '{payload['make']}'. Supported: {supported}"}), 400)
    model = resolve_model(make, payload["model"])
    if model is None:
        supported = [m.name for m in VehicleModel.query.filter(VehicleModel.make_id == make.id).all()]
        return None, None, (jsonify({"error": f"Unsupported model '{payload['model']}' for {make.name}. Supported: {supported}"}), 400)
    return make, model, None


def _number(payload, key, cast=float):
    """None if absent/blank; raises ValueError on garbage so the route can 400."""
    value = payload.get(key)
    if value is None or value == "":
        return None
    return cast(value)


@flip_calculator_bp.route("/flip-calculator", methods=["POST"])
def flip_calculator():
    payload = request.get_json(silent=True) or {}
    missing = [field for field in REQUIRED_FIELDS if payload.get(field) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    make, model, error = resolve_vehicle(payload)
    if error is not None:
        return error

    try:
        year = int(payload["year"])
        purchase_price = float(payload["purchase_price"])
        mileage_km = int(payload["mileage_km"])
        months_held = float(payload["months_held"])
        km_per_month = _number(payload, "km_per_month", int)
        expected_sale_price = _number(payload, "expected_sale_price")
        repair_budget = _number(payload, "repair_budget")
        insurance_annual = _number(payload, "insurance_annual")
        target_net = _number(payload, "target_net")
    except (TypeError, ValueError):
        return jsonify({"error": "Numeric fields must be numbers."}), 400

    if purchase_price <= 0 or mileage_km < 0 or not (0 < months_held <= 36):
        return jsonify({"error": "purchase_price must be > 0, mileage_km >= 0, and months_held between 0 and 36."}), 400

    generation = resolve_generation(model, year)
    if generation is None:
        return jsonify({"error": f"No generation of {make.name} {model.name} covers model year {year}."}), 400

    kwargs = {}
    if km_per_month is not None:
        kwargs["km_per_month"] = km_per_month
    if target_net is not None:
        kwargs["target_net"] = target_net

    result = calculate_flip(
        generation, resolve_trim(generation, payload.get("trim")), make.name,
        purchase_price=purchase_price, mileage_km=mileage_km, months_held=months_held,
        title_status=payload.get("title_status", "clean"), condition=payload.get("condition", "good"),
        expected_sale_price=expected_sale_price, repair_budget=repair_budget,
        insurance_annual=insurance_annual, **kwargs,
    )
    result["vehicle"] = {
        "make": make.name, "model": model.name, "year": year,
        "generation": generation.label, "trim": payload.get("trim"),
    }
    return jsonify(result)
