"""GET /catalog - the full make -> model -> generation -> trim tree.

Powers the cascading dropdowns on the manual-entry analyze form. Returned as
one nested payload rather than four separate endpoints since the whole tree
is small and the frontend needs it all at once anyway.
"""

from flask import Blueprint, jsonify

from app.models import VehicleMake

catalog_bp = Blueprint("catalog", __name__)


@catalog_bp.route("/catalog", methods=["GET"])
def get_catalog():
    makes = VehicleMake.query.order_by(VehicleMake.name).all()

    return jsonify({
        "makes": [
            {
                "id": make.id,
                "name": make.name,
                "models": [
                    {
                        "id": model.id,
                        "name": model.name,
                        "generations": [
                            {
                                "id": generation.id,
                                "label": generation.label,
                                "start_year": generation.start_year,
                                "end_year": generation.end_year,
                                "body_type": generation.body_type,
                                "trims": [
                                    {"id": trim.id, "name": trim.name}
                                    for trim in generation.trims
                                ],
                            }
                            for generation in model.generations
                        ],
                    }
                    for model in make.models
                ],
            }
            for make in makes
        ]
    })
