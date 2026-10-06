"""Flip ledger: log a flip, add real expenses, sell it, and compare actual
profit/loss against the calculator's snapshot taken at purchase time.
"""

import uuid

from app.extensions import db
from app.models import AdminAuditLog, AdminUser, Flip
from app.services.auth import hash_password

PASSWORD = "correct-horse-battery-staple"

NEW_FLIP = {
    "make": "Honda", "model": "Accord", "year": 2010, "trim": "EX-L V6", "mileage_km": 175000,
    "purchase_price": 7000, "purchase_date": "2026-01-01", "planned_months": 3, "purchase_fees": 100,
}


def _create_user(role):
    user = AdminUser(email=f"{role}-{uuid.uuid4().hex[:8]}@example.com", password_hash=hash_password(PASSWORD),
                     role=role, is_active=True)
    db.session.add(user)
    db.session.commit()
    return user


def _cleanup(user):
    for flip in Flip.query.filter_by(created_by_id=user.id).all():
        db.session.delete(flip)
    AdminAuditLog.query.filter_by(actor_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()


def _headers(client, user):
    resp = client.post("/auth/login", json={"email": user.email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def test_full_flip_lifecycle_compares_actual_to_predicted(app, client):
    with app.app_context():
        admin = _create_user("admin")
        try:
            headers = _headers(client, admin)
            created = client.post("/admin/flips", headers=headers, json=NEW_FLIP)
            assert created.status_code == 201
            flip = created.get_json()
            flip_id = flip["id"]
            assert flip["purchase_tax"] == 910.0  # defaulted to 13% of price
            assert flip["predicted"]["costs"]["totals"]["all_in"] > 7000
            assert flip["summary"]["acquisition_cost"] == 7000 + 910 + 100

            for category, amount in (("insurance", 1000), ("fuel", 300), ("repair", 450)):
                resp = client.post(f"/admin/flips/{flip_id}/expenses", headers=headers,
                                   json={"category": category, "amount": amount, "date": "2026-02-01"})
                assert resp.status_code == 201
            detail = client.get(f"/admin/flips/{flip_id}", headers=headers).get_json()
            assert detail["summary"]["expenses_total"] == 1750
            assert detail["summary"]["break_even_sale_price"] > detail["summary"]["total_invested"]
            assert detail["summary"]["actual_net"] is None

            sold = client.post(f"/admin/flips/{flip_id}/sell", headers=headers,
                               json={"sale_price": 10000, "sale_date": "2026-04-01", "sale_fees": 150})
            assert sold.status_code == 200
            body = sold.get_json()
            # 10000 - 150 - (7000 + 910 + 100) - 1750
            assert body["summary"]["actual_net"] == 90.0
            comparison = body["summary"]["comparison"]
            assert comparison["net_error"] == 90 - comparison["predicted_net"]
            assert {row["line"] for row in comparison["lines"]} == {"insurance", "fuel", "maintenance", "repairs"}

            assert client.post(f"/admin/flips/{flip_id}/sell", headers=headers, json={"sale_price": 1}).status_code == 400

            listing = client.get("/admin/flips", headers=headers).get_json()
            assert listing["portfolio"]["flips_sold"] == 1
            assert listing["portfolio"]["total_net"] == 90.0
            assert listing["portfolio"]["win_rate_pct"] == 100.0
            assert listing["portfolio"]["prediction"]["flips_compared"] == 1
        finally:
            _cleanup(admin)


def test_validation(app, client):
    with app.app_context():
        admin = _create_user("admin")
        try:
            headers = _headers(client, admin)
            assert client.post("/admin/flips", headers=headers, json={"make": "Honda"}).status_code == 400
            assert client.post("/admin/flips", headers=headers, json={**NEW_FLIP, "make": "Nope"}).status_code == 400
            assert client.post("/admin/flips", headers=headers, json={**NEW_FLIP, "purchase_date": "bad"}).status_code == 400
            flip_id = client.post("/admin/flips", headers=headers, json=NEW_FLIP).get_json()["id"]
            assert client.post(f"/admin/flips/{flip_id}/expenses", headers=headers,
                               json={"category": "snacks", "amount": 5}).status_code == 400
            assert client.post(f"/admin/flips/{flip_id}/expenses", headers=headers,
                               json={"category": "fuel", "amount": -5}).status_code == 400
            assert client.post(f"/admin/flips/{flip_id}/sell", headers=headers,
                               json={"sale_price": 9000, "sale_date": "2025-01-01"}).status_code == 400
        finally:
            _cleanup(admin)


def test_permissions(app, client):
    with app.app_context():
        analyst = _create_user("analyst")
        try:
            headers = _headers(client, analyst)
            assert client.get("/admin/flips", headers=headers).status_code == 200  # "view"
            assert client.post("/admin/flips", headers=headers, json=NEW_FLIP).status_code == 403  # needs "ingest"
            assert client.get("/admin/flips").status_code == 401
        finally:
            _cleanup(analyst)
