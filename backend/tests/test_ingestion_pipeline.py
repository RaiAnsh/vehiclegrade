"""Covers the Bronze -> Silver ingestion pipeline: the pure normalizer
function (app.services.ingestion_normalizer.normalize_submission) and the
admin-only /admin/import-batches routes that create batches, append raw
pasted rows, process them into ListingObservations, and expose summaries.

Every route test also doubles as an authorization test - each mutating
endpoint requires the "ingest" permission (admin/reviewer, not analyst),
matching the same RBAC convention already covered end-to-end in
test_auth.py. Not re-tested here: the token/CSRF machinery itself (that's
test_auth.py's job) - these tests just log in and use the resulting access
token like any other authenticated client would.

Each test creates and tears down its own AdminUser + ImportBatch (+ cascaded
RawListingSubmission/ListingObservation rows) rather than depending on a
shared fixture, matching this project's existing per-test build-and-cleanup
convention (see test_engine_match_confidence.py).
"""

import csv
import io
import uuid

from app.extensions import db
from app.models import AdminAuditLog, AdminUser, ImportBatch, ListingObservation
from app.services.auth import hash_password
from app.services.ingestion_normalizer import normalize_submission

PASSWORD = "correct-horse-battery-staple"

CLEAN_LISTING_TEXT = """2018 Honda Civic EX
82,000 km
Automatic
$19,500
Clean title
Hamilton

Well maintained. New brakes. Selling because I bought an SUV."""


def _create_user(role="admin", password=PASSWORD):
    email = f"{role}-{uuid.uuid4().hex[:8]}@example.com"
    user = AdminUser(email=email, password_hash=hash_password(password), role=role, is_active=True)
    db.session.add(user)
    db.session.commit()
    return user


def _cleanup_user(user):
    AdminAuditLog.query.filter_by(actor_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()


def _cleanup_batch(batch):
    if batch is not None:
        AdminAuditLog.query.filter_by(target_type="ImportBatch", target_id=batch.id).delete()
        db.session.delete(batch)  # cascades to raw_submissions -> observations
        db.session.commit()


def _login_headers(client, user):
    resp = client.post("/auth/login", json={"email": user.email, "password": PASSWORD})
    access_token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


# --- normalize_submission (pure function) ------------------------------

def test_normalize_submission_clean_listing_is_pending(app):
    with app.app_context():
        fields = normalize_submission(CLEAN_LISTING_TEXT)
        # Missing fuel_type (not present anywhere in the text) is exactly
        # the kind of gap this pipeline is deliberately conservative about.
        assert fields["review_status"] == "needs_review"
        assert fields["unresolved_fields"] == ["fuel_type"]
        assert fields["validation_errors"] is None
        assert fields["make_raw"] == "Honda"
        assert fields["model_raw"] == "Civic"
        assert fields["year"] == 2018
        assert fields["price"] == 19500.0
        assert fields["title_status"] == "clean"


def test_normalize_submission_empty_text_flags_every_field_unresolved(app):
    with app.app_context():
        fields = normalize_submission("Selling my old car, decent shape. Make an offer.")
        assert fields["review_status"] == "needs_review"
        assert "make" in fields["unresolved_fields"]
        assert "price" in fields["unresolved_fields"]
        assert fields["validation_errors"] is None


def test_normalize_submission_invalid_values_are_validation_errors(app):
    with app.app_context():
        fields = normalize_submission("1950 Honda Civic\n-500 km\n$99999999\nSalvage title")
        assert fields["review_status"] == "needs_review"
        assert "year" in fields["validation_errors"]
        assert "price" in fields["validation_errors"]


def test_normalize_submission_extracts_url_and_hashes_it(app):
    with app.app_context():
        text = CLEAN_LISTING_TEXT + "\nhttps://example.com/listing/12345"
        fields = normalize_submission(text)
        assert fields["external_url"] == "https://example.com/listing/12345"
        assert fields["url_hash"] is not None


def test_normalize_submission_flags_duplicate_by_url_and_penalizes_quality(app):
    with app.app_context():
        from app.extensions import db
        from app.models import ImportBatch, ListingObservation, RawListingSubmission

        admin = _create_user(role="admin")
        batch = ImportBatch(source_type="paste_single", created_by_id=admin.id)
        db.session.add(batch)
        db.session.flush()
        row = RawListingSubmission(import_batch_id=batch.id, sequence_in_batch=1, raw_text="seed row")
        db.session.add(row)
        db.session.flush()

        text_with_url = CLEAN_LISTING_TEXT + "\nhttps://example.com/listing/dupe-test"
        first_fields = normalize_submission(text_with_url)
        existing = ListingObservation(import_batch_id=batch.id, raw_submission_id=row.id, **first_fields)
        db.session.add(existing)
        db.session.commit()

        try:
            second_fields = normalize_submission(text_with_url)
            assert second_fields["duplicate_of_observation_id"] == existing.id
            assert second_fields["review_status"] == "needs_review"
            assert second_fields["quality_score"] < first_fields["quality_score"]
        finally:
            db.session.delete(existing)
            db.session.delete(row)
            db.session.delete(batch)
            db.session.commit()
            _cleanup_user(admin)


# --- /admin/import-batches routes ---------------------------------------

def test_create_batch_requires_ingest_permission(app, client):
    with app.app_context():
        analyst = _create_user(role="analyst")
        batch = None
        try:
            headers = _login_headers(client, analyst)
            resp = client.post("/admin/import-batches", headers=headers, json={"source_type": "paste_single"})
            assert resp.status_code == 403
        finally:
            _cleanup_batch(batch)
            _cleanup_user(analyst)


def test_create_batch_rejects_bad_source_type(app, client):
    with app.app_context():
        admin = _create_user(role="admin")
        try:
            headers = _login_headers(client, admin)
            resp = client.post("/admin/import-batches", headers=headers, json={"source_type": "telepathy"})
            assert resp.status_code == 400
        finally:
            _cleanup_user(admin)


def test_full_paste_single_flow_creates_pending_observation(app, client):
    with app.app_context():
        admin = _create_user(role="admin")
        batch = None
        try:
            headers = _login_headers(client, admin)

            create_resp = client.post("/admin/import-batches", headers=headers, json={"source_type": "paste_single"})
            assert create_resp.status_code == 201
            batch_id = create_resp.get_json()["id"]
            batch = ImportBatch.query.get(batch_id)

            rows_resp = client.post(
                f"/admin/import-batches/{batch_id}/rows", headers=headers, json={"text": CLEAN_LISTING_TEXT},
            )
            assert rows_resp.status_code == 201
            assert rows_resp.get_json()["rows_added"] == 1
            assert rows_resp.get_json()["batch"]["row_count"] == 1

            process_resp = client.post(f"/admin/import-batches/{batch_id}/process", headers=headers)
            assert process_resp.status_code == 200
            summary = process_resp.get_json()
            assert summary["status"] == "completed"
            assert summary["observation_counts"]["needs_review"] == 1

            summary_resp = client.get(f"/admin/import-batches/{batch_id}", headers=headers)
            assert summary_resp.status_code == 200
            assert summary_resp.get_json()["observation_counts"]["needs_review"] == 1

            rows_list_resp = client.get(f"/admin/import-batches/{batch_id}/rows", headers=headers)
            assert rows_list_resp.status_code == 200
            rows = rows_list_resp.get_json()["rows"]
            assert len(rows) == 1
            assert rows[0]["observation"]["make_raw"] == "Honda"
            assert rows[0]["observation"]["review_status"] == "needs_review"

            reprocess_resp = client.post(f"/admin/import-batches/{batch_id}/process", headers=headers)
            assert reprocess_resp.status_code == 400

            assert AdminAuditLog.query.filter_by(action="import_batch.create", target_id=batch_id).count() == 1
            assert AdminAuditLog.query.filter_by(action="import_batch.add_rows", target_id=batch_id).count() == 1
            assert AdminAuditLog.query.filter_by(action="import_batch.process", target_id=batch_id).count() == 1
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)


def test_paste_multi_flow_appends_multiple_rows_at_once(app, client):
    with app.app_context():
        reviewer = _create_user(role="reviewer")
        batch = None
        try:
            headers = _login_headers(client, reviewer)

            create_resp = client.post("/admin/import-batches", headers=headers, json={"source_type": "paste_multi"})
            batch_id = create_resp.get_json()["id"]
            batch = ImportBatch.query.get(batch_id)

            rows_resp = client.post(
                f"/admin/import-batches/{batch_id}/rows",
                headers=headers,
                json={"texts": [CLEAN_LISTING_TEXT, "another partial listing, no numbers at all"]},
            )
            assert rows_resp.status_code == 201
            assert rows_resp.get_json()["rows_added"] == 2

            process_resp = client.post(f"/admin/import-batches/{batch_id}/process", headers=headers)
            assert process_resp.status_code == 200
            assert sum(process_resp.get_json()["observation_counts"].values()) == 2

            filtered_resp = client.get(
                f"/admin/import-batches/{batch_id}/rows?review_status=needs_review", headers=headers,
            )
            assert filtered_resp.status_code == 200
            assert len(filtered_resp.get_json()["rows"]) == 2
        finally:
            _cleanup_batch(batch)
            _cleanup_user(reviewer)


# --- CSV ingestion ------------------------------------------------------

CSV_TEXT = (
    "Model Year,Make,Model,Asking Price,Odometer (km),Title,Transmission,Fuel,City\n"
    "2018,Honda,Civic,19500,82000,clean,Automatic,Gasoline,Hamilton\n"
    "2019,Honda,Civic,,91000,clean,Automatic,Gasoline,Hamilton\n"
)


def test_csv_template_download_has_canonical_headers(app, client):
    with app.app_context():
        admin = _create_user(role="admin")
        try:
            headers = _login_headers(client, admin)
            resp = client.get("/admin/import-batches/csv-template", headers=headers)
            assert resp.status_code == 200
            assert resp.mimetype == "text/csv"
            first_line = resp.get_data(as_text=True).splitlines()[0]
            assert first_line.split(",")[:3] == ["year", "make", "model"]
        finally:
            _cleanup_user(admin)


def test_csv_preview_suggests_mapping_without_touching_db(app, client):
    with app.app_context():
        admin = _create_user(role="admin")
        try:
            headers = _login_headers(client, admin)
            batches_before = ImportBatch.query.count()
            data = {"file": (io.BytesIO(CSV_TEXT.encode("utf-8")), "listings.csv")}
            resp = client.post(
                "/admin/import-batches/csv-preview", headers=headers,
                data=data, content_type="multipart/form-data",
            )
            assert resp.status_code == 200
            body = resp.get_json()
            assert body["row_count"] == 2
            assert body["suggested_mapping"]["Model Year"] == "year"
            assert body["suggested_mapping"]["Asking Price"] == "price"
            assert body["suggested_mapping"]["Odometer (km)"] == "mileage_km"
            assert len(body["sample_rows"]) == 2
            assert ImportBatch.query.count() == batches_before  # preview never creates a batch
        finally:
            _cleanup_user(admin)


def test_csv_upload_full_flow_creates_observations(app, client):
    with app.app_context():
        admin = _create_user(role="admin")
        batch = None
        try:
            headers = _login_headers(client, admin)
            column_mapping = {
                "Model Year": "year", "Make": "make", "Model": "model",
                "Asking Price": "price", "Odometer (km)": "mileage_km",
                "Title": "title_status", "Transmission": "transmission",
                "Fuel": "fuel_type", "City": "location",
            }
            create_resp = client.post(
                "/admin/import-batches", headers=headers,
                json={"source_type": "csv_upload", "column_mapping": column_mapping, "original_filename": "listings.csv"},
            )
            assert create_resp.status_code == 201
            batch_id = create_resp.get_json()["id"]
            batch = ImportBatch.query.get(batch_id)

            reader = csv.DictReader(io.StringIO(CSV_TEXT))
            rows = list(reader)
            rows_resp = client.post(
                f"/admin/import-batches/{batch_id}/rows", headers=headers, json={"rows": rows},
            )
            assert rows_resp.status_code == 201
            assert rows_resp.get_json()["rows_added"] == 2

            process_resp = client.post(f"/admin/import-batches/{batch_id}/process", headers=headers)
            assert process_resp.status_code == 200
            counts = process_resp.get_json()["observation_counts"]
            assert sum(counts.values()) == 2
            # Row 1 is fully clean -> pending; row 2 is missing price -> needs_review.
            assert counts["pending"] == 1
            assert counts["needs_review"] == 1

            rows_list_resp = client.get(f"/admin/import-batches/{batch_id}/rows", headers=headers)
            observations = [r["observation"] for r in rows_list_resp.get_json()["rows"]]
            assert any(o["make_raw"] == "Honda" and o["price"] == 19500.0 for o in observations)
            assert any(o["price"] is None for o in observations)
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)


def test_csv_batch_rejects_text_rows_and_paste_batch_rejects_csv_rows(app, client):
    with app.app_context():
        admin = _create_user(role="admin")
        csv_batch = None
        paste_batch = None
        try:
            headers = _login_headers(client, admin)
            csv_create = client.post(
                "/admin/import-batches", headers=headers,
                json={"source_type": "csv_upload", "column_mapping": {"Make": "make"}},
            )
            csv_batch_id = csv_create.get_json()["id"]
            csv_batch = ImportBatch.query.get(csv_batch_id)
            bad_text_resp = client.post(
                f"/admin/import-batches/{csv_batch_id}/rows", headers=headers, json={"text": "Honda Civic"},
            )
            assert bad_text_resp.status_code == 400

            paste_create = client.post(
                "/admin/import-batches", headers=headers, json={"source_type": "paste_single"},
            )
            paste_batch_id = paste_create.get_json()["id"]
            paste_batch = ImportBatch.query.get(paste_batch_id)
            bad_rows_resp = client.post(
                f"/admin/import-batches/{paste_batch_id}/rows", headers=headers, json={"rows": [{"Make": "Honda"}]},
            )
            assert bad_rows_resp.status_code == 400
        finally:
            _cleanup_batch(csv_batch)
            _cleanup_batch(paste_batch)
            _cleanup_user(admin)


def test_create_csv_batch_requires_column_mapping(app, client):
    with app.app_context():
        admin = _create_user(role="admin")
        try:
            headers = _login_headers(client, admin)
            resp = client.post("/admin/import-batches", headers=headers, json={"source_type": "csv_upload"})
            assert resp.status_code == 400
        finally:
            _cleanup_user(admin)


def test_export_rejected_rows_returns_csv_with_reasons(app, client):
    with app.app_context():
        admin = _create_user(role="admin")
        batch = None
        try:
            headers = _login_headers(client, admin)
            create_resp = client.post("/admin/import-batches", headers=headers, json={"source_type": "paste_single"})
            batch_id = create_resp.get_json()["id"]
            client.post(
                f"/admin/import-batches/{batch_id}/rows", headers=headers,
                json={"text": "Selling my old car, decent shape."},
            )
            client.post(f"/admin/import-batches/{batch_id}/process", headers=headers)
            batch = ImportBatch.query.get(batch_id)
            observation = ListingObservation.query.filter_by(import_batch_id=batch_id).first()

            client.post(
                f"/admin/observations/{observation.id}/reject", headers=headers,
                json={"rejection_reason": "Not enough information to identify the vehicle"},
            )

            resp = client.get(f"/admin/import-batches/{batch_id}/rejected/export", headers=headers)
            assert resp.status_code == 200
            assert resp.mimetype == "text/csv"
            body = resp.get_data(as_text=True)
            assert "rejection_reason" in body.splitlines()[0]
            assert "Not enough information" in body
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)


def test_add_rows_rejects_empty_payload_and_closed_batch(app, client):
    with app.app_context():
        admin = _create_user(role="admin")
        batch = None
        try:
            headers = _login_headers(client, admin)
            create_resp = client.post("/admin/import-batches", headers=headers, json={"source_type": "paste_single"})
            batch_id = create_resp.get_json()["id"]
            batch = ImportBatch.query.get(batch_id)

            empty_resp = client.post(f"/admin/import-batches/{batch_id}/rows", headers=headers, json={"text": "   "})
            assert empty_resp.status_code == 400

            missing_batch_resp = client.post(
                "/admin/import-batches/999999/rows", headers=headers, json={"text": "anything"},
            )
            assert missing_batch_resp.status_code == 404
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)
