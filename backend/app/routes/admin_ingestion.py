"""Admin-only Bronze-layer ingestion endpoints: create an ImportBatch, feed
it raw pasted text (one listing or many) or CSV rows, normalize every row
into a ListingObservation via app.services.ingestion_normalizer, and inspect
the result.

Nothing here ever creates an `approved`/`rejected` ListingObservation, and
nothing here writes to the `listings` table - that materialization only
happens in the (separate, Phase 4) admin_review routes once a human
explicitly approves a row. This file is purely Bronze -> Silver.

Splitting one multi-listing paste into individual listing blocks is left to
the caller (the frontend, which already knows the blank-line-separated
convention users type in) - this keeps `normalize_submission` a pure
single-text function with no NLP-ish segmentation logic of its own. Callers
send either one `text` or a `texts` list; both paste_single and paste_multi
batches accept either shape, since a paste_single batch that happens to add
one row via `texts: [text]` is harmless and not worth rejecting.

CSV upload follows a three-step flow, mirroring the paste flow's
create -> add rows -> process shape:
  1. POST /import-batches/csv-preview - upload a CSV file, get back its
     headers + a suggested (never auto-applied) column_mapping + a few
     sample rows, without touching the database at all.
  2. POST /import-batches (source_type=csv_upload, column_mapping=<admin-
     confirmed mapping>) then POST /import-batches/<id>/rows (rows=<CSV
     rows as {header: value} dicts>) - a csv_upload batch is homogeneous:
     every row in it is a CSV row, never a pasted text.
  3. POST /import-batches/<id>/process - same endpoint as the paste flow;
     it dispatches per-row to normalize_csv_row or normalize_submission
     based on whether that row has raw_row or raw_text set.
"""

import csv
import io
from datetime import datetime

from flask import Blueprint, Response, g, jsonify, request

from app.extensions import db
from app.models import ImportBatch, ListingObservation, RawListingSubmission
from app.models.import_batch import VALID_SOURCE_TYPES
from app.models.listing_observation import VALID_REVIEW_STATUSES
from app.services import audit_log
from app.services.ingestion_normalizer import (
    CSV_TEMPLATE_COLUMNS,
    normalize_csv_row,
    normalize_submission,
    suggest_column_mapping,
)
from app.utils.auth_decorators import require_permission

admin_ingestion_bp = Blueprint("admin_ingestion", __name__, url_prefix="/admin")

MAX_CSV_PREVIEW_ROWS = 5
MAX_CSV_ROWS = 2000


def _batch_summary(batch):
    counts = {status: 0 for status in VALID_REVIEW_STATUSES}
    for (status, count) in (
        db.session.query(ListingObservation.review_status, db.func.count(ListingObservation.id))
        .filter(ListingObservation.import_batch_id == batch.id)
        .group_by(ListingObservation.review_status)
        .all()
    ):
        counts[status] = count

    return {
        "id": batch.id,
        "source_type": batch.source_type,
        "status": batch.status,
        "original_filename": batch.original_filename,
        "created_by_id": batch.created_by_id,
        "created_at": batch.created_at.isoformat(),
        "processed_at": batch.processed_at.isoformat() if batch.processed_at else None,
        "row_count": batch.row_count,
        "notes": batch.notes,
        "observation_counts": counts,
    }


def _observation_public(observation):
    return {
        "id": observation.id,
        "raw_submission_id": observation.raw_submission_id,
        "review_status": observation.review_status,
        "make_raw": observation.make_raw,
        "model_raw": observation.model_raw,
        "generation_id": observation.generation_id,
        "trim_id": observation.trim_id,
        "location_id": observation.location_id,
        "year": observation.year,
        "mileage_km": observation.mileage_km,
        "price": observation.price,
        "title_status": observation.title_status,
        "condition": observation.condition,
        "transmission": observation.transmission,
        "fuel_type": observation.fuel_type,
        "validation_errors": observation.validation_errors,
        "unresolved_fields": observation.unresolved_fields,
        "quality_score": observation.quality_score,
    }


def _row_public(raw_submission):
    return {
        "id": raw_submission.id,
        "sequence_in_batch": raw_submission.sequence_in_batch,
        "raw_text": raw_submission.raw_text,
        "raw_row": raw_submission.raw_row,
        "submitted_at": raw_submission.submitted_at.isoformat(),
        "observation": _observation_public(raw_submission.observation) if raw_submission.observation else None,
    }


@admin_ingestion_bp.route("/import-batches/csv-template", methods=["GET"])
@require_permission("view")
def download_csv_template():
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_TEMPLATE_COLUMNS)
    writer.writerow([
        "2018", "Honda", "Civic", "EX", "19500", "82000",
        "clean", "good", "Automatic", "Gasoline", "Hamilton", "", "",
    ])
    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=vehiclegrade-import-template.csv"},
    )


@admin_ingestion_bp.route("/import-batches/csv-preview", methods=["POST"])
@require_permission("ingest")
def preview_csv():
    """Parses an uploaded CSV's headers only - never persisted, never touches
    the database. The admin confirms/corrects the suggested mapping
    client-side before it's ever passed back in as a real column_mapping.
    """
    uploaded = request.files.get("file")
    if uploaded is None:
        return jsonify({"error": "Provide a CSV file as multipart form field 'file'"}), 400

    try:
        text = uploaded.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return jsonify({"error": "File must be UTF-8 encoded CSV"}), 400

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return jsonify({"error": "CSV has no header row"}), 400

    sample_rows = []
    row_count = 0
    for row in reader:
        row_count += 1
        if len(sample_rows) < MAX_CSV_PREVIEW_ROWS:
            sample_rows.append(row)
    if row_count > MAX_CSV_ROWS:
        return jsonify({"error": f"CSV has {row_count} rows - maximum is {MAX_CSV_ROWS} per upload"}), 400

    return jsonify({
        "headers": reader.fieldnames,
        "suggested_mapping": suggest_column_mapping(reader.fieldnames),
        "sample_rows": sample_rows,
        "row_count": row_count,
        "original_filename": uploaded.filename,
    }), 200


@admin_ingestion_bp.route("/import-batches", methods=["POST"])
@require_permission("ingest")
def create_import_batch():
    payload = request.get_json(silent=True) or {}
    source_type = payload.get("source_type")

    if source_type not in VALID_SOURCE_TYPES:
        return jsonify({"error": f"source_type must be one of: {', '.join(VALID_SOURCE_TYPES)}"}), 400

    column_mapping = None
    original_filename = None
    if source_type == "csv_upload":
        column_mapping = payload.get("column_mapping")
        if not isinstance(column_mapping, dict) or not column_mapping:
            return jsonify({"error": "csv_upload batches require a non-empty column_mapping"}), 400
        original_filename = str(payload.get("original_filename") or "").strip()[:255] or None

    batch = ImportBatch(
        source_type=source_type,
        created_by_id=g.current_user.id,
        column_mapping=column_mapping,
        original_filename=original_filename,
        notes=(str(payload.get("notes") or "").strip()[:2000] or None),
    )
    db.session.add(batch)
    db.session.flush()

    audit_log.record(
        "import_batch.create", actor=g.current_user, target_type="ImportBatch", target_id=batch.id, request=request,
    )
    db.session.commit()

    return jsonify(_batch_summary(batch)), 201


@admin_ingestion_bp.route("/import-batches/<int:batch_id>/rows", methods=["POST"])
@require_permission("ingest")
def add_rows(batch_id):
    batch = ImportBatch.query.get(batch_id)
    if batch is None:
        return jsonify({"error": "Import batch not found"}), 404
    if batch.status != "open":
        return jsonify({"error": f"Batch is '{batch.status}' - rows can only be added to an 'open' batch"}), 400

    payload = request.get_json(silent=True) or {}
    texts = payload.get("texts")
    single_text = payload.get("text")
    rows_payload = payload.get("rows")

    if batch.source_type == "csv_upload":
        if rows_payload is None:
            return jsonify({"error": "csv_upload batches require 'rows' (a list of {column: value} objects)"}), 400
        if not isinstance(rows_payload, list) or not all(isinstance(r, dict) for r in rows_payload):
            return jsonify({"error": "rows must be a list of objects"}), 400
        if len(rows_payload) > MAX_CSV_ROWS:
            return jsonify({"error": f"Cannot add more than {MAX_CSV_ROWS} rows at once"}), 400
        raw_rows = rows_payload
        raw_texts = None
    elif rows_payload is not None:
        return jsonify({"error": "'rows' is only accepted for csv_upload batches"}), 400
    elif texts is not None:
        if not isinstance(texts, list) or not all(isinstance(t, str) for t in texts):
            return jsonify({"error": "texts must be a list of strings"}), 400
        raw_texts = [t for t in texts if t.strip()]
        raw_rows = None
    elif single_text is not None:
        raw_texts = [single_text] if single_text.strip() else []
        raw_rows = None
    else:
        return jsonify({"error": "Provide either 'text' (string) or 'texts' (list of strings)"}), 400

    if raw_rows is not None and not raw_rows:
        return jsonify({"error": "No rows provided"}), 400
    if raw_texts is not None and not raw_texts:
        return jsonify({"error": "No non-empty listing text provided"}), 400

    created_rows = []
    next_sequence = batch.row_count + 1
    if raw_rows is not None:
        for raw_row in raw_rows:
            row = RawListingSubmission(
                import_batch_id=batch.id, sequence_in_batch=next_sequence, raw_row=raw_row,
            )
            db.session.add(row)
            created_rows.append(row)
            next_sequence += 1
    else:
        for raw_text in raw_texts:
            row = RawListingSubmission(
                import_batch_id=batch.id, sequence_in_batch=next_sequence, raw_text=raw_text,
            )
            db.session.add(row)
            created_rows.append(row)
            next_sequence += 1

    batch.row_count = next_sequence - 1
    db.session.flush()

    audit_log.record(
        "import_batch.add_rows", actor=g.current_user, target_type="ImportBatch", target_id=batch.id,
        affected_record_ids=[row.id for row in created_rows], request=request,
    )
    db.session.commit()

    return jsonify({"batch": _batch_summary(batch), "rows_added": len(created_rows)}), 201


@admin_ingestion_bp.route("/import-batches/<int:batch_id>/process", methods=["POST"])
@require_permission("ingest")
def process_batch(batch_id):
    batch = ImportBatch.query.get(batch_id)
    if batch is None:
        return jsonify({"error": "Import batch not found"}), 404
    if batch.status == "completed":
        return jsonify({"error": "Batch has already been processed"}), 400
    if batch.status == "rolled_back":
        return jsonify({"error": "Batch was rolled back and cannot be reprocessed"}), 400
    if batch.row_count == 0:
        return jsonify({"error": "Batch has no rows to process"}), 400

    unprocessed_rows = (
        RawListingSubmission.query.filter_by(import_batch_id=batch.id)
        .outerjoin(ListingObservation)
        .filter(ListingObservation.id.is_(None))
        .order_by(RawListingSubmission.sequence_in_batch.asc())
        .all()
    )

    created_observations = []
    for row in unprocessed_rows:
        if row.raw_row is not None:
            fields = normalize_csv_row(row.raw_row, batch.column_mapping or {})
        else:
            fields = normalize_submission(row.raw_text or "")
        observation = ListingObservation(import_batch_id=batch.id, raw_submission_id=row.id, **fields)
        db.session.add(observation)
        created_observations.append(observation)

    batch.status = "completed"
    batch.processed_at = datetime.utcnow()
    db.session.flush()

    audit_log.record(
        "import_batch.process", actor=g.current_user, target_type="ImportBatch", target_id=batch.id,
        affected_record_ids=[obs.id for obs in created_observations], request=request,
    )
    db.session.commit()

    return jsonify(_batch_summary(batch)), 200


@admin_ingestion_bp.route("/import-batches/<int:batch_id>", methods=["GET"])
@require_permission("view")
def get_batch(batch_id):
    batch = ImportBatch.query.get(batch_id)
    if batch is None:
        return jsonify({"error": "Import batch not found"}), 404
    return jsonify(_batch_summary(batch)), 200


@admin_ingestion_bp.route("/import-batches/<int:batch_id>/rows", methods=["GET"])
@require_permission("view")
def list_rows(batch_id):
    batch = ImportBatch.query.get(batch_id)
    if batch is None:
        return jsonify({"error": "Import batch not found"}), 404

    review_status_filter = request.args.get("review_status")
    if review_status_filter is not None and review_status_filter not in VALID_REVIEW_STATUSES:
        return jsonify({"error": f"review_status must be one of: {', '.join(VALID_REVIEW_STATUSES)}"}), 400

    query = RawListingSubmission.query.filter_by(import_batch_id=batch.id)
    if review_status_filter is not None:
        query = query.join(ListingObservation).filter(ListingObservation.review_status == review_status_filter)

    rows = query.order_by(RawListingSubmission.sequence_in_batch.asc()).all()
    return jsonify({"batch_id": batch.id, "rows": [_row_public(row) for row in rows]}), 200


@admin_ingestion_bp.route("/import-batches/<int:batch_id>/rejected/export", methods=["GET"])
@require_permission("view")
def export_rejected_rows(batch_id):
    """CSV export of every rejected row in a batch - what was submitted, and
    why it never became a Listing (rejection_reason, or the validation_errors/
    unresolved_fields it was stuck on before a human explicitly rejected it).
    Lets an admin take rejected rows back to the source and fix them
    externally, rather than re-typing from the review UI.
    """
    batch = ImportBatch.query.get(batch_id)
    if batch is None:
        return jsonify({"error": "Import batch not found"}), 404

    rejected_observations = (
        ListingObservation.query.filter_by(import_batch_id=batch.id, review_status="rejected")
        .join(RawListingSubmission)
        .order_by(RawListingSubmission.sequence_in_batch.asc())
        .all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "sequence_in_batch", "raw_text_or_row", "make_raw", "model_raw", "year", "price", "mileage_km",
        "validation_errors", "unresolved_fields", "duplicate_of_observation_id", "rejection_reason",
    ])
    for observation in rejected_observations:
        row = observation.raw_submission
        writer.writerow([
            row.sequence_in_batch,
            row.raw_text if row.raw_text is not None else str(row.raw_row or ""),
            observation.make_raw, observation.model_raw, observation.year, observation.price, observation.mileage_km,
            ", ".join(observation.validation_errors or []),
            ", ".join(observation.unresolved_fields or []),
            observation.duplicate_of_observation_id or "",
            observation.rejection_reason or "",
        ])

    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=batch-{batch.id}-rejected.csv"},
    )
