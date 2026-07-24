"""Covers Silver -> Gold: PATCH/approve/reject on a ListingObservation, and
batch-level rollback. This is the ONLY code path that may ever create a
Listing row from ingested data, or change review_status - proving that
path enforces "no unresolved gap, no unacknowledged duplicate, ever
reaches a user-facing market estimate" is the whole point of this file.

Builds a full batch -> process -> review lifecycle against the real seeded
catalog (Honda Civic) so generation/location resolution behaves exactly as
it would for a live paste, rather than mocking resolution away.
"""

import uuid

from app.extensions import db
from app.models import AdminAuditLog, AdminUser, ImportBatch, Listing, ListingObservation, RawListingSubmission
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


def test_approve_requires_no_unresolved_gaps(app, client):
    with app.app_context():
        admin = _create_user("admin")
        batch = None
        try:
            headers = _login_headers(client, admin)
            batch_id = _create_and_process_batch(client, headers, [INCOMPLETE_LISTING_TEXT])
            batch = ImportBatch.query.get(batch_id)
            observation = ListingObservation.query.filter_by(import_batch_id=batch_id).first()

            resp = client.post(f"/admin/observations/{observation.id}/approve", headers=headers)
            assert resp.status_code == 400
            assert "unresolved_fields" in resp.get_json()
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)


def test_patch_resolves_gap_and_enables_approval(app, client):
    with app.app_context():
        admin = _create_user("admin")
        batch = None
        try:
            headers = _login_headers(client, admin)
            batch_id = _create_and_process_batch(client, headers, [CLEAN_LISTING_TEXT])
            batch = ImportBatch.query.get(batch_id)
            observation = ListingObservation.query.filter_by(import_batch_id=batch_id).first()
            assert observation.review_status == "needs_review"  # fuel_type gap
            assert "fuel_type" in observation.unresolved_fields

            patch_resp = client.patch(
                f"/admin/observations/{observation.id}", headers=headers, json={"fuel_type": "Gasoline"},
            )
            assert patch_resp.status_code == 200
            body = patch_resp.get_json()
            assert body["review_status"] == "pending"
            assert body["unresolved_fields"] is None

            approve_resp = client.post(f"/admin/observations/{observation.id}/approve", headers=headers)
            assert approve_resp.status_code == 200
            approved = approve_resp.get_json()
            assert approved["review_status"] == "approved"
            assert approved["approved_listing_id"] is not None

            listing = Listing.query.get(approved["approved_listing_id"])
            assert listing is not None
            assert listing.generation.model.name == "Civic"
            assert listing.year == 2018
            assert listing.price == 19500.0
            assert listing.source == "admin_ingested"

            # Already-approved rows are immutable.
            second_approve = client.post(f"/admin/observations/{observation.id}/approve", headers=headers)
            assert second_approve.status_code == 400
            locked_patch = client.patch(f"/admin/observations/{observation.id}", headers=headers, json={"price": 1})
            assert locked_patch.status_code == 400
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)


def test_reject_requires_reason_and_is_terminal(app, client):
    with app.app_context():
        admin = _create_user("admin")
        batch = None
        try:
            headers = _login_headers(client, admin)
            batch_id = _create_and_process_batch(client, headers, [INCOMPLETE_LISTING_TEXT])
            batch = ImportBatch.query.get(batch_id)
            observation = ListingObservation.query.filter_by(import_batch_id=batch_id).first()

            missing_reason_resp = client.post(f"/admin/observations/{observation.id}/reject", headers=headers, json={})
            assert missing_reason_resp.status_code == 400

            resp = client.post(
                f"/admin/observations/{observation.id}/reject", headers=headers,
                json={"rejection_reason": "Not enough information to identify the vehicle"},
            )
            assert resp.status_code == 200
            assert resp.get_json()["review_status"] == "rejected"
            assert resp.get_json()["rejection_reason"]

            second = client.post(
                f"/admin/observations/{observation.id}/reject", headers=headers, json={"rejection_reason": "again"},
            )
            assert second.status_code == 400
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)


def test_duplicate_flag_blocks_approval_unless_overridden(app, client):
    with app.app_context():
        admin = _create_user("admin")
        batch = None
        try:
            headers = _login_headers(client, admin)
            text_with_url = CLEAN_LISTING_TEXT + "\nhttps://example.com/listing/admin-review-dupe-test"
            batch_id = _create_and_process_batch(client, headers, [text_with_url])
            batch = ImportBatch.query.get(batch_id)
            observation = ListingObservation.query.filter_by(import_batch_id=batch_id).first()

            # Fill the one real gap (fuel_type), approve it as the "original".
            client.patch(f"/admin/observations/{observation.id}", headers=headers, json={"fuel_type": "Gasoline"})
            client.post(f"/admin/observations/{observation.id}/approve", headers=headers)

            second_batch_id = _create_and_process_batch(client, headers, [text_with_url])
            second_batch = ImportBatch.query.get(second_batch_id)
            second_observation = ListingObservation.query.filter_by(import_batch_id=second_batch_id).first()
            try:
                assert second_observation.duplicate_of_observation_id == observation.id

                client.patch(
                    f"/admin/observations/{second_observation.id}", headers=headers, json={"fuel_type": "Gasoline"},
                )
                blocked_resp = client.post(f"/admin/observations/{second_observation.id}/approve", headers=headers)
                assert blocked_resp.status_code == 400
                assert "duplicate_of_observation_id" in blocked_resp.get_json()

                overridden_resp = client.post(
                    f"/admin/observations/{second_observation.id}/approve", headers=headers,
                    json={"override_duplicate": True},
                )
                assert overridden_resp.status_code == 200
                assert overridden_resp.get_json()["review_status"] == "approved"
            finally:
                _cleanup_batch(second_batch)
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)


def test_rollback_archives_approved_listings_and_rejects_remaining_rows(app, client):
    with app.app_context():
        admin = _create_user("admin")
        batch = None
        try:
            headers = _login_headers(client, admin)
            batch_id = _create_and_process_batch(client, headers, [CLEAN_LISTING_TEXT, INCOMPLETE_LISTING_TEXT])
            batch = ImportBatch.query.get(batch_id)
            observations = ListingObservation.query.filter_by(import_batch_id=batch_id).all()
            clean_obs = next(o for o in observations if o.make_raw == "Honda")

            client.patch(f"/admin/observations/{clean_obs.id}", headers=headers, json={"fuel_type": "Gasoline"})
            approve_resp = client.post(f"/admin/observations/{clean_obs.id}/approve", headers=headers)
            listing_id = approve_resp.get_json()["approved_listing_id"]

            rollback_resp = client.post(f"/admin/import-batches/{batch_id}/rollback", headers=headers)
            assert rollback_resp.status_code == 200
            body = rollback_resp.get_json()
            assert body["status"] == "rolled_back"
            assert listing_id in body["listings_archived"]

            listing = Listing.query.get(listing_id)
            assert listing.is_archived is True

            for observation in ListingObservation.query.filter_by(import_batch_id=batch_id).all():
                assert observation.review_status == "rejected"

            already_rolled_back = client.post(f"/admin/import-batches/{batch_id}/rollback", headers=headers)
            assert already_rolled_back.status_code == 400
        finally:
            _cleanup_batch(batch)
            _cleanup_user(admin)


def test_review_endpoints_require_review_permission(app, client):
    with app.app_context():
        analyst = _create_user("analyst")
        try:
            headers = _login_headers(client, analyst)
            resp = client.post("/admin/observations/1/approve", headers=headers)
            assert resp.status_code == 403
        finally:
            _cleanup_user(analyst)
