"""Covers the admin auth lifecycle: login, access/refresh token issuance,
refresh rotation bound to a CSRF header, reuse detection, role-based
authorization, and audit logging of every auth event.

Rate limiting is disabled for the whole test session (see conftest.py)
since Flask-Limiter's in-memory counter is shared by one long-lived app
instance across every test in this file - real request-rate protection is
still wired up in app.routes.auth via @limiter.limit(...), just not
exercised here to avoid tests interfering with each other's counts.

Each test creates and tears down its own AdminUser (+ its RefreshTokens via
cascade, + its AdminAuditLog rows explicitly) rather than depending on any
shared fixture user, matching this project's existing per-test
build-and-cleanup convention (see test_engine_match_confidence.py).
"""

import re
import uuid

from app.extensions import db
from app.models import AdminAuditLog, AdminUser
from app.services.auth import hash_password

PASSWORD = "correct-horse-battery-staple"


def _extract_refresh_cookie(response):
    """The Werkzeug test client's cookie jar auto-advances to the newest
    refresh cookie on every request, which is exactly what real reuse
    detection needs to defend against: pulling the raw cookie value out of
    a response manually lets a test explicitly replay an old cookie after
    the jar has already moved past it.
    """
    set_cookie = response.headers.get("Set-Cookie", "")
    match = re.search(r"vg_refresh_token=([^;]+)", set_cookie)
    assert match, f"No refresh cookie in response: {set_cookie}"
    return match.group(1)


def _create_user(role="admin", password=PASSWORD, is_active=True):
    email = f"{role}-{uuid.uuid4().hex[:8]}@example.com"
    user = AdminUser(email=email, password_hash=hash_password(password), role=role, is_active=is_active)
    db.session.add(user)
    db.session.commit()
    return user


def _cleanup_user(user):
    AdminAuditLog.query.filter_by(actor_id=user.id).delete()
    db.session.delete(user)  # cascades to RefreshToken rows
    db.session.commit()


def _login(client, user, password=PASSWORD):
    return client.post("/auth/login", json={"email": user.email, "password": password})


def test_login_success_returns_tokens_and_sets_refresh_cookie(app, client):
    with app.app_context():
        user = _create_user()
        try:
            resp = _login(client, user)
            assert resp.status_code == 200
            body = resp.get_json()
            assert body["access_token"]
            assert body["csrf_token"]
            assert body["user"] == {"id": user.id, "email": user.email, "role": "admin", "is_active": True}
            assert "vg_refresh_token" in resp.headers.get("Set-Cookie", "")

            assert AdminAuditLog.query.filter_by(action="auth.login", actor_id=user.id).count() == 1
        finally:
            _cleanup_user(user)


def test_login_wrong_password_returns_generic_error(app, client):
    with app.app_context():
        user = _create_user()
        try:
            resp = client.post("/auth/login", json={"email": user.email, "password": "not-the-password"})
            assert resp.status_code == 401
            assert resp.get_json()["error"] == "Invalid email or password"
            assert AdminAuditLog.query.filter_by(action="auth.login_failed", actor_email=user.email).count() == 1
        finally:
            _cleanup_user(user)


def test_login_unknown_email_returns_same_generic_error(client):
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever12345"})
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Invalid email or password"


def test_login_inactive_user_rejected(app, client):
    with app.app_context():
        user = _create_user(is_active=False)
        try:
            resp = _login(client, user)
            assert resp.status_code == 401
        finally:
            _cleanup_user(user)


def test_me_requires_bearer_token(app, client):
    with app.app_context():
        user = _create_user()
        try:
            assert client.get("/auth/me").status_code == 401

            access_token = _login(client, user).get_json()["access_token"]
            resp = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
            assert resp.status_code == 200
            assert resp.get_json()["email"] == user.email
        finally:
            _cleanup_user(user)


def test_me_rejects_garbage_token(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_refresh_rotates_token_and_requires_matching_csrf_header(app, client):
    with app.app_context():
        user = _create_user()
        try:
            login_body = _login(client, user).get_json()
            csrf_token = login_body["csrf_token"]

            # Wrong/missing CSRF header is rejected even with a valid cookie.
            bad_resp = client.post("/auth/refresh", headers={"X-CSRF-Token": "wrong"})
            assert bad_resp.status_code == 401

            resp = client.post("/auth/refresh", headers={"X-CSRF-Token": csrf_token})
            assert resp.status_code == 200
            body = resp.get_json()
            assert body["access_token"]
            assert body["csrf_token"] != csrf_token  # rotated
            assert AdminAuditLog.query.filter_by(action="auth.refresh", actor_id=user.id).count() == 1
        finally:
            _cleanup_user(user)


def test_refresh_token_reuse_is_detected_and_revokes_session(app, client):
    with app.app_context():
        user = _create_user()
        try:
            login_resp = _login(client, user)
            old_raw_cookie = _extract_refresh_cookie(login_resp)

            # Legitimate rotation - the jar now holds the new cookie.
            first_refresh = client.post("/auth/refresh", headers={"X-CSRF-Token": login_resp.get_json()["csrf_token"]})
            assert first_refresh.status_code == 200

            # Replay the OLD (now-revoked) cookie, simulating a stolen
            # token being used after the legitimate client already rotated
            # past it. Any CSRF header is fine here - reuse is detected
            # before the CSRF check even runs.
            client.set_cookie("vg_refresh_token", old_raw_cookie, path="/auth")
            replay_resp = client.post("/auth/refresh", headers={"X-CSRF-Token": "irrelevant"})
            assert replay_resp.status_code == 401
            assert replay_resp.get_json()["error"] == "Session invalidated - please log in again"
            assert AdminAuditLog.query.filter_by(action="auth.token_reuse_detected").count() >= 1

            # The whole session was killed as a precaution - even the
            # legitimately-rotated newest token must now be rejected.
            from app.models import RefreshToken
            still_valid = [t for t in RefreshToken.query.filter_by(user_id=user.id).all() if t.is_valid()]
            assert still_valid == []
        finally:
            _cleanup_user(user)


def test_logout_revokes_refresh_token(app, client):
    with app.app_context():
        user = _create_user()
        try:
            login_body = _login(client, user).get_json()
            csrf_token = login_body["csrf_token"]

            logout_resp = client.post("/auth/logout")
            assert logout_resp.status_code == 200
            assert AdminAuditLog.query.filter_by(action="auth.logout").count() >= 1

            resp = client.post("/auth/refresh", headers={"X-CSRF-Token": csrf_token})
            assert resp.status_code == 401
        finally:
            _cleanup_user(user)


def test_analyst_role_is_read_only(app, client):
    with app.app_context():
        analyst = _create_user(role="analyst")
        try:
            access_token = _login(client, analyst).get_json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}

            assert client.get("/auth/me", headers=headers).status_code == 200

            resp = client.post(
                "/auth/users", headers=headers,
                json={"email": "new@example.com", "password": "whatever-long-enough", "role": "analyst"},
            )
            assert resp.status_code == 403
        finally:
            _cleanup_user(analyst)


def test_admin_can_create_and_deactivate_users(app, client):
    with app.app_context():
        admin = _create_user(role="admin")
        created_user = None
        try:
            access_token = _login(client, admin).get_json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}

            create_resp = client.post(
                "/auth/users", headers=headers,
                json={"email": f"reviewer-{uuid.uuid4().hex[:8]}@example.com",
                      "password": "whatever-long-enough", "role": "reviewer"},
            )
            assert create_resp.status_code == 201
            created_body = create_resp.get_json()
            created_user = AdminUser.query.get(created_body["id"])
            assert created_user.role == "reviewer"

            weak_password_resp = client.post(
                "/auth/users", headers=headers,
                json={"email": "x@example.com", "password": "short", "role": "reviewer"},
            )
            assert weak_password_resp.status_code == 400

            bad_role_resp = client.post(
                "/auth/users", headers=headers,
                json={"email": "y@example.com", "password": "whatever-long-enough", "role": "superadmin"},
            )
            assert bad_role_resp.status_code == 400

            deactivate_resp = client.post(f"/auth/users/{created_user.id}/deactivate", headers=headers)
            assert deactivate_resp.status_code == 200
            assert deactivate_resp.get_json()["is_active"] is False

            self_deactivate_resp = client.post(f"/auth/users/{admin.id}/deactivate", headers=headers)
            assert self_deactivate_resp.status_code == 400
        finally:
            if created_user is not None:
                _cleanup_user(created_user)
            _cleanup_user(admin)
