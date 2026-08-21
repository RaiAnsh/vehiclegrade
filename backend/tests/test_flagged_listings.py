"""Covers the two simple /api/* endpoints in app.routes.flagged_listings:
GET /api/flagged-listings (read, filtered by quality_score) and
POST /api/listings/<id>/review (approve/reject a ListingObservation).

Deliberately separate from test_admin_review.py (which covers the richer
PATCH/approve/reject/rollback workflow in app.routes.admin_review) - these
tests only need to prove this simpler, second entry point respects the same
invariants (blocked by unresolved gaps, terminal states are immutable)
without duplicating every case already covered there.
"""

import uuid

from app.extensions import db
from app.models import AdminAuditLog, AdminUser, ImportBatch, Listing, ListingObservation
from app.services.auth import hash_password

PASSWORD = "correct-horse-battery-staple"

CLEAN_LISTING_TEXT = """2018 Honda Civic EX
82,000 km
Automatic
$19,500
Clean title
Hamilton

Well maintained. New brakes."""

INCOMPLETE_LISTING_TEXT = "Selling my car, decent shape. Make an offer."


def _create_user(role="admin"):
    email = f"{role}-{uuid.uuid4().hex[:8]}@example.com"
    user = AdminUser(email=email, password_hash=hash_password(PASSWORD), role=role, is_active=True)
    db.session.add(user)
    db.session.commit()
    return user


def _cleanup_user(user):
    AdminAuditLog.query.filter_by(actor_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()


def _cleanup_batch(batch):
    if batch is None:
        return
    for observation in ListingObservation.query.filter_by(import_batch_id=batch.id).all():
        if observation.approved_listing_id:
            listing = Listing.query.get(observation.approved_listing_id)
            if listing is not None:
                db.session.delete(listing)
    AdminAuditLog.query.filter_by(target_type="ImportBatch", target_id=batch.id).delete()
    AdminAuditLog.query.filter(
        AdminAuditLog.target_type == "ListingObservation",
        AdminAuditLog.target_id.in_([o.id for o in ListingObservation.query.filter_by(import_batch_id=batch.id).all()]),
    ).delete(synchronize_session=False)
    db.session.delete(batch)
    db.session.commit()


def _login_headers(client, user):
    resp = client.post("/auth/login", json={"email": user.email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def _create_and_process_batch(client, headers, texts):
    create_resp = client.post("/admin/import-batches", headers=headers, json={"source_type": "paste_multi"})
    batch_id = create_resp.get_json()["id"]
    client.post(f"/admin/import-batches/{batch_id}/rows", headers=headers, json={"texts": texts})
    client.post(f"/admin/import-batches/{batch_id}/process", headers=headers)
    return batch_id


def test_flagged_listings_only_returns_rows_below_threshold(app, client):
    with app.app_context():
        admin = _create_user("admin")
        batch = None
        try:
            headers = _login_headers(client, admin)
            batch_id = _create_and_process_batch(client, headers, [CLEAN_LISTING_TEXT, INCOMPLETE_LISTING_TEXT])
            batch = ImportBatch.query.get(batch_id)
            observations = ListingObservation.query.filter_by(import_batch_id=batch_id).all()
            incomplete = next(o for o in observations if o.make_raw is None)
            clean = next(o for o in observations if o.make_raw == "Honda")
            assert incomplete.quality_score < clean.quality_score  # sanity check on the fixture itself

            resp = client.get(f"/api/flagged-listings?threshold={clean.quality_score}", headers=headers)
            assert resp.status_code == 200
            body = resp.get_json()
            returned_ids = {row["id"] for row in body["flagged_listings"]}
            assert incomplete.id in returned_ids
            assert clean.id not in returned_ids  # not strictly below its own score
            flagged_row = next(row for row in body["flagged_listings"] if row["id"] == incomplete.id)
            assert flagged_row["status"] == incomplete.review_status
            assert flagged_row["confidence_score"] == incomplete.quality_score
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)


def test_flagged_listings_requires_auth(app, client):
    with app.app_context():
        resp = client.get("/api/flagged-listings")
        assert resp.status_code == 401


def test_review_rejects_with_note(app, client):
    with app.app_context():
        admin = _create_user("admin")
        batch = None
        try:
            headers = _login_headers(client, admin)
            batch_id = _create_and_process_batch(client, headers, [INCOMPLETE_LISTING_TEXT])
            batch = ImportBatch.query.get(batch_id)
            observation = ListingObservation.query.filter_by(import_batch_id=batch_id).first()

            resp = client.post(
                f"/api/listings/{observation.id}/review", headers=headers,
                json={"status": "rejected", "note": "Not enough detail to identify the vehicle"},
            )
            assert resp.status_code == 200
            body = resp.get_json()
            assert body["status"] == "rejected"
            assert body["reviewer_note"] == "Not enough detail to identify the vehicle"
            assert body["approved_listing_id"] is None

            db.session.refresh(observation)
            assert observation.review_status == "rejected"
            assert observation.rejection_reason == "Not enough detail to identify the vehicle"

            second = client.post(f"/api/listings/{observation.id}/review", headers=headers, json={"status": "rejected"})
            assert second.status_code == 400
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)


def test_review_approve_blocked_by_unresolved_gap_but_succeeds_once_clean(app, client):
    with app.app_context():
        admin = _create_user("admin")
        batch = None
        try:
            headers = _login_headers(client, admin)
            batch_id = _create_and_process_batch(client, headers, [CLEAN_LISTING_TEXT])
            batch = ImportBatch.query.get(batch_id)
            observation = ListingObservation.query.filter_by(import_batch_id=batch_id).first()
            assert "fuel_type" in observation.unresolved_fields  # the one real gap in CLEAN_LISTING_TEXT

            blocked = client.post(
                f"/api/listings/{observation.id}/review", headers=headers, json={"status": "approved"},
            )
            assert blocked.status_code == 400
            assert "unresolved_fields" in blocked.get_json()

            observation.fuel_type = "Gasoline"
            observation.unresolved_fields = None
            db.session.commit()

            approved = client.post(
                f"/api/listings/{observation.id}/review", headers=headers,
                json={"status": "approved", "note": "Looks good"},
            )
            assert approved.status_code == 200
            body = approved.get_json()
            assert body["status"] == "approved"
            assert body["approved_listing_id"] is not None

            listing = Listing.query.get(body["approved_listing_id"])
            assert listing.source == "admin_ingested"
            assert listing.price == 19500.0
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)


def test_review_endpoint_requires_review_permission(app, client):
    with app.app_context():
        analyst = _create_user("analyst")
        try:
            headers = _login_headers(client, analyst)
            resp = client.post("/api/listings/1/review", headers=headers, json={"status": "approved"})
            assert resp.status_code == 403
        finally:
            _cleanup_user(analyst)
