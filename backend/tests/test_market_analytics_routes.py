"""Covers the two API surfaces built on top of the Gold layer:
GET /market/aggregates (public) and /admin/analytics/* (admin-only).
"""

import uuid

from app.extensions import db
from app.models import AdminUser, Generation, MarketAggregate, VehicleMake, VehicleModel
from app.services.auth import hash_password
from app.services.market_aggregation import recompute_generation

PASSWORD = "correct-horse-battery-staple"


def _civic_generation():
    return (
        Generation.query.join(VehicleModel).join(VehicleMake)
        .filter(VehicleMake.name == "Honda", VehicleModel.name == "Civic")
        .first()
    )


def _create_user(role="admin"):
    email = f"{role}-{uuid.uuid4().hex[:8]}@example.com"
    user = AdminUser(email=email, password_hash=hash_password(PASSWORD), role=role, is_active=True)
    db.session.add(user)
    db.session.commit()
    return user


def _cleanup_user(user):
    db.session.delete(user)
    db.session.commit()


def _login_headers(client, user):
    resp = client.post("/auth/login", json={"email": user.email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def test_market_aggregates_requires_generation_id(client):
    resp = client.get("/market/aggregates")
    assert resp.status_code == 400


def test_market_aggregates_404_for_unknown_generation(client):
    resp = client.get("/market/aggregates?generation_id=999999")
    assert resp.status_code == 404


def test_market_aggregates_returns_no_fabricated_data_when_empty(app, client):
    with app.app_context():
        civic_model = _civic_generation().model
        empty_generation = Generation(
            model_id=civic_model.id, label="Test Empty Gen 2", start_year=1999, end_year=2001,
            body_type="sedan", drivetrain="FWD", base_horsepower=100, fuel_economy_l_per_100km=7.0,
            reliability_stars=4.0, typical_lifespan_km=300000, parts_availability="good",
            insurance_category="low", expected_annual_maintenance_cost=500.0, base_value=5000.0,
            reference_mileage_km=100000,
        )
        db.session.add(empty_generation)
        db.session.commit()

        try:
            resp = client.get(f"/market/aggregates?generation_id={empty_generation.id}")
            assert resp.status_code == 200
            body = resp.get_json()
            assert body["overall"] is None
            assert body["by_region"] == []
            assert "No approved market observations" in body["disclosure"]
        finally:
            db.session.delete(empty_generation)
            db.session.commit()


def test_market_aggregates_returns_real_computed_cube(app, client):
    with app.app_context():
        generation = _civic_generation()
        recompute_generation(generation.id)

        resp = client.get(f"/market/aggregates?generation_id={generation.id}")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["overall"]["sample_size"] > 0
        assert body["overall"]["region"] is None  # ALL_DIMENSION_VALUE unwrapped to null over the wire
        assert body["by_region"]
        assert body["by_title_status"]
        assert "Honda Civic" in body["generation_label"]


def test_admin_analytics_overview_returns_bronze_silver_gold_counts(app, client):
    with app.app_context():
        admin = _create_user("analyst")  # read-only role should still see this
        try:
            headers = _login_headers(client, admin)
            resp = client.get("/admin/analytics/overview", headers=headers)
            assert resp.status_code == 200
            body = resp.get_json()
            assert "bronze" in body and "silver" in body and "gold" in body
            assert body["gold"]["total_listings"] > 0
        finally:
            _cleanup_user(admin)


def test_admin_analytics_recompute_requires_rollback_permission(app, client):
    with app.app_context():
        reviewer = _create_user("reviewer")  # has review/ingest/view but not rollback
        try:
            headers = _login_headers(client, reviewer)
            resp = client.post("/admin/analytics/recompute", headers=headers, json={})
            assert resp.status_code == 403
        finally:
            _cleanup_user(reviewer)


def test_admin_analytics_recompute_single_generation(app, client):
    with app.app_context():
        admin = _create_user("admin")
        try:
            headers = _login_headers(client, admin)
            generation = _civic_generation()
            resp = client.post(
                "/admin/analytics/recompute", headers=headers, json={"generation_id": generation.id},
            )
            assert resp.status_code == 200
            assert resp.get_json()["rows_written"] > 0
        finally:
            _cleanup_user(admin)


def test_admin_analytics_recompute_all(app, client):
    with app.app_context():
        admin = _create_user("admin")
        try:
            headers = _login_headers(client, admin)
            resp = client.post("/admin/analytics/recompute", headers=headers, json={})
            assert resp.status_code == 200
            body = resp.get_json()
            assert body["generations_recomputed"] > 0
            assert body["total_rows_written"] > 0
        finally:
            _cleanup_user(admin)
