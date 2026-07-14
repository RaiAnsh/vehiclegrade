"""Custom Flask CLI commands. Run with: flask --app run.py seed-db"""

import csv
import json
from datetime import datetime
from pathlib import Path

import click

from app.extensions import db
from app.models import Engine, GenerationEngine, Generation, KnownIssue, MaintenanceItem, Trim, VehicleMake, VehicleModel
from app.utils.seed_data import seed_database

EXPORTS_DIR = Path(__file__).parent.parent.parent / "data" / "exports"
ENGINE_DATA_PATH = Path(__file__).parent / "engine_data" / "engines.json"

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

    @app.cli.command("import-engine-data")
    @click.argument("path", default=str(ENGINE_DATA_PATH))
    def import_engine_data(path):
        """Upsert Engine rows (matched by name) and their GenerationEngine
        links from an import-ready JSON file, and backfill Trim/KnownIssue/
        MaintenanceItem.engine_id wherever the source data resolves a single,
        unambiguous engine. Safe to re-run - adding coverage for a new engine
        or generation later only means adding an entry to the JSON file, not
        touching this command.
        """
        with open(path) as f:
            data = json.load(f)

        reviewed_at = datetime.fromisoformat(data["_meta"]["reviewed_at"])

        counts = {
            "engines_created": 0, "engines_updated": 0, "generation_links": 0,
            "trim_links": 0, "known_issue_links": 0, "maintenance_item_links": 0,
        }
        skipped = {"generations": set(), "trims": set(), "known_issues": set(), "maintenance_items": set()}

        for engine_data in data["engines"]:
            engine = Engine.query.filter_by(name=engine_data["name"]).first()
            if engine is None:
                engine = Engine(name=engine_data["name"])
                db.session.add(engine)
                counts["engines_created"] += 1
            else:
                counts["engines_updated"] += 1

            for field in (
                "description", "manufacturer", "code", "displacement_l", "cylinders", "configuration",
                "aspiration", "fuel_type", "production_start_year", "production_end_year", "source_name",
                "source_url", "confidence",
            ):
                setattr(engine, field, engine_data.get(field))
            engine.reviewed_at = reviewed_at

            db.session.flush()

            for link in engine_data.get("generation_links", []):
                generation = _find_generation(link["make"], link["model"], link["generation_label"])
                if generation is None:
                    skipped["generations"].add((link["make"], link["model"], link["generation_label"]))
                    continue
                exists = GenerationEngine.query.filter_by(generation_id=generation.id, engine_id=engine.id).first()
                if exists is None:
                    db.session.add(GenerationEngine(generation_id=generation.id, engine_id=engine.id))
                    counts["generation_links"] += 1

            for link in engine_data.get("trim_links", []):
                trim = _find_trim(link["make"], link["model"], link["generation_label"], link["trim"])
                if trim is None:
                    skipped["trims"].add((link["make"], link["model"], link["generation_label"], link["trim"]))
                    continue
                trim.engine_id = engine.id
                counts["trim_links"] += 1

            for link in engine_data.get("known_issue_links", []):
                issue = _find_known_issue(link["make"], link["model"], link["generation_label"], link["title"])
                if issue is None:
                    skipped["known_issues"].add((link["make"], link["model"], link["generation_label"], link["title"]))
                    continue
                issue.engine_id = engine.id
                counts["known_issue_links"] += 1

            for link in engine_data.get("maintenance_item_links", []):
                item = _find_maintenance_item(link["make"], link["model"], link["generation_label"], link["name"])
                if item is None:
                    skipped["maintenance_items"].add((link["make"], link["model"], link["generation_label"], link["name"]))
                    continue
                item.engine_id = engine.id
                counts["maintenance_item_links"] += 1

        db.session.commit()

        click.echo(
            f"Engines: {counts['engines_created']} created, {counts['engines_updated']} updated. "
            f"Links created - generation: {counts['generation_links']}, trim: {counts['trim_links']}, "
            f"known_issue: {counts['known_issue_links']}, maintenance_item: {counts['maintenance_item_links']}."
        )
        for kind, missed in skipped.items():
            if missed:
                click.echo(f"Skipped {kind} (no match found): {len(missed)}")
                for item in sorted(missed):
                    click.echo(f"    {item}")


def _find_generation(make_name, model_name, generation_label):
    return (
        Generation.query.join(VehicleModel).join(VehicleMake)
        .filter(VehicleMake.name == make_name, VehicleModel.name == model_name, Generation.label == generation_label)
        .first()
    )


def _find_trim(make_name, model_name, generation_label, trim_name):
    generation = _find_generation(make_name, model_name, generation_label)
    if generation is None:
        return None
    return Trim.query.filter_by(generation_id=generation.id, name=trim_name).first()


def _find_known_issue(make_name, model_name, generation_label, title):
    generation = _find_generation(make_name, model_name, generation_label)
    if generation is None:
        return None
    return KnownIssue.query.filter_by(generation_id=generation.id, title=title).first()


def _find_maintenance_item(make_name, model_name, generation_label, name):
    generation = _find_generation(make_name, model_name, generation_label)
    if generation is None:
        return None
    return MaintenanceItem.query.filter_by(generation_id=generation.id, name=name).first()
