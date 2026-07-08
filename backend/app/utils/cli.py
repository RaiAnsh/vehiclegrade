"""Custom Flask CLI commands. Run with: flask --app run.py seed-db"""

import csv
import json
from datetime import datetime
from pathlib import Path

import click

from app.extensions import db
from app.models import Generation, KnownIssue, MaintenanceItem, VehicleMake, VehicleModel
from app.utils.seed_data import seed_database

EXPORTS_DIR = Path(__file__).parent.parent.parent / "data" / "exports"

EXPORTS = {
    "vehicle_specs": "export_vehicle_specs",
    "known_issues": "export_known_issues",
    "maintenance_intervals": "export_maintenance_intervals",
    "market_comparables": "export_market_comparables",
}


def register_cli(app):
    @app.cli.command("seed-db")
    def seed_db():
        """Drop, recreate, and repopulate all tables with mock data."""
        counts = seed_database()
        click.echo(
            f"Seeded {counts['models']} models, {counts['locations']} locations, "
            f"{counts['listings']} listings."
        )

    @app.cli.command("export-reference-data")
    def export_reference_data():
        """Write vehicle_specs, known_issues, maintenance_intervals, and
        market_comparables to backend/data/exports/ as both JSON and CSV -
        the admin/import-ready deliverable for future real-data pipelines.
        """
        from app.services import reference_export

        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

        for name, fn_name in EXPORTS.items():
            rows = getattr(reference_export, fn_name)()
            fieldnames = getattr(reference_export, f"{name.upper()}_FIELDS")

            meta = {
                "generated_at": datetime.utcnow().isoformat(),
                "source": "vehiclegrade_reference_v1",
                "record_count": len(rows),
                "is_sample_data": name == "market_comparables",
            }

            json_path = EXPORTS_DIR / f"{name}.json"
            with open(json_path, "w") as f:
                json.dump({"_meta": meta, "records": rows}, f, indent=2, default=str)

            csv_path = EXPORTS_DIR / f"{name}.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            click.echo(f"Exported {len(rows)} {name} records -> {json_path.name}, {csv_path.name}")

    @app.cli.command("import-reference-data")
    @click.argument("path", default=str(EXPORTS_DIR))
    def import_reference_data(path):
        """Upsert known_issues and maintenance_intervals from previously
        exported JSON files, matched by (make, model, generation_label,
        title/name). Proves the reference layer can round-trip with a real
        import pipeline later - does not create new makes/models/generations,
        only updates existing knowledge-base rows.
        """
        base = Path(path)
        updated = {"known_issues": 0, "maintenance_intervals": 0}
        skipped = {"known_issues": 0, "maintenance_intervals": 0}

        known_issues_path = base / "known_issues.json"
        if known_issues_path.exists():
            with open(known_issues_path) as f:
                records = json.load(f)["records"]
            for record in records:
                generation = _find_generation(record["make"], record["model"], record["generation_label"])
                if generation is None:
                    skipped["known_issues"] += 1
                    continue
                issue = KnownIssue.query.filter(
                    KnownIssue.generation_id == generation.id, KnownIssue.title == record["title"]
                ).first()
                if issue is None:
                    skipped["known_issues"] += 1
                    continue
                issue.description = record["description"]
                issue.symptoms = record.get("symptoms")
                issue.severity = record["severity"]
                issue.typical_mileage_km = record["typical_mileage_km"]
                issue.estimated_repair_cost_min = record["estimated_repair_cost_min"]
                issue.estimated_repair_cost_max = record["estimated_repair_cost_max"]
                issue.recommendation = record["recommendation"]
                updated["known_issues"] += 1

        maintenance_path = base / "maintenance_intervals.json"
        if maintenance_path.exists():
            with open(maintenance_path) as f:
                records = json.load(f)["records"]
            for record in records:
                generation = _find_generation(record["make"], record["model"], record["generation_label"])
                if generation is None:
                    skipped["maintenance_intervals"] += 1
                    continue
                item = MaintenanceItem.query.filter(
                    MaintenanceItem.generation_id == generation.id, MaintenanceItem.name == record["name"]
                ).first()
                if item is None:
                    skipped["maintenance_intervals"] += 1
                    continue
                item.interval_km = record["interval_km"]
                item.estimated_cost_min = record.get("estimated_cost_min")
                item.estimated_cost_max = record.get("estimated_cost_max")
                updated["maintenance_intervals"] += 1

        db.session.commit()
        click.echo(
            f"Updated {updated['known_issues']} known issues ({skipped['known_issues']} skipped, no match), "
            f"{updated['maintenance_intervals']} maintenance intervals ({skipped['maintenance_intervals']} skipped, no match)."
        )


def _find_generation(make_name, model_name, generation_label):
    return (
        Generation.query.join(VehicleModel).join(VehicleMake)
        .filter(VehicleMake.name == make_name, VehicleModel.name == model_name, Generation.label == generation_label)
        .first()
    )
