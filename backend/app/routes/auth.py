"""Admin authentication endpoints.

Cookie-authenticated endpoints (/auth/refresh, /auth/logout) are scoped to
this blueprint's own path (cookie `path="/auth"`) to minimize the surface
that ever receives the refresh cookie automatically, and require the
X-CSRF-Token header described in app.services.auth. Every other admin
endpoint in this app should authenticate via `Authorization: Bearer
<access_token>` instead, which needs no CSRF protection at all.
"""

from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, request

from app.extensions import db, limiter
from app.models import VALID_ROLES, AdminUser
from app.services import audit_log
from app.services.auth import (
    AuthenticationError,
    TokenReuseDetected,
    generate_access_token,
    hash_password,
    issue_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
    verify_password,
)
from app.utils.auth_decorators import require_permission

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

REFRESH_COOKIE_NAME = "vg_refresh_token"


def _set_refresh_cookie(response, raw_refresh_token):
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        raw_refresh_token,
        max_age=current_app.config["REFRESH_TOKEN_TTL_DAYS"] * 24 * 60 * 60,
        httponly=True,
        secure=current_app.config["REFRESH_COOKIE_SECURE"],
        samesite=current_app.config["REFRESH_COOKIE_SAMESITE"],
        domain=current_app.config["REFRESH_COOKIE_DOMAIN"],
        path="/auth",
    )


def _clear_refresh_cookie(response):
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        "",
        expires=0,
        httponly=True,
        secure=current_app.config["REFRESH_COOKIE_SECURE"],
        samesite=current_app.config["REFRESH_COOKIE_SAMESITE"],
        domain=current_app.config["REFRESH_COOKIE_DOMAIN"],
        path="/auth",
    )


def _user_public(user):
    return {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")

    generic_error = "Invalid email or password"

    if not email or not password:
        return jsonify({"error": generic_error}), 401

    user = AdminUser.query.filter_by(email=email).first()

    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        audit_log.record("auth.login_failed", actor_email=email, request=request)
        db.session.commit()
        return jsonify({"error": generic_error}), 401

    raw_refresh, raw_csrf, _row = issue_refresh_token(
        user, ip_address=request.remote_addr, user_agent=request.headers.get("User-Agent")
    )
    access_token = generate_access_token(user)
    user.last_login_at = datetime.utcnow()
    audit_log.record("auth.login", actor=user, request=request)
    db.session.commit()

    response = jsonify({"access_token": access_token, "csrf_token": raw_csrf, "user": _user_public(user)})
    _set_refresh_cookie(response, raw_refresh)
    return response, 200


@auth_bp.route("/refresh", methods=["POST"])
@limiter.limit("30 per minute")
def refresh():
    raw_refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    csrf_header = request.headers.get("X-CSRF-Token")

    if not raw_refresh_token:
        return jsonify({"error": "No refresh token present"}), 401

    try:
        new_raw_refresh, new_raw_csrf, _row, user = rotate_refresh_token(
            raw_refresh_token, csrf_header, ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )
    except TokenReuseDetected:
        audit_log.record("auth.token_reuse_detected", request=request)
        db.session.commit()
        response = jsonify({"error": "Session invalidated - please log in again"})
        _clear_refresh_cookie(response)
        return response, 401
    except AuthenticationError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 401

    access_token = generate_access_token(user)
    audit_log.record("auth.refresh", actor=user, request=request)
    db.session.commit()

    response = jsonify({"access_token": access_token, "csrf_token": new_raw_csrf, "user": _user_public(user)})
    _set_refresh_cookie(response, new_raw_refresh)
    return response, 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    raw_refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_refresh_token:
        revoke_refresh_token(raw_refresh_token)
        audit_log.record("auth.logout", request=request)
        db.session.commit()

    response = jsonify({"status": "logged_out"})
    _clear_refresh_cookie(response)
    return response, 200


@auth_bp.route("/me", methods=["GET"])
@require_permission("view")
def me():
    return jsonify(_user_public(g.current_user)), 200


@auth_bp.route("/users", methods=["GET"])
@require_permission("manage_users")
def list_users():
    users = AdminUser.query.order_by(AdminUser.created_at.asc()).all()
    return jsonify({"users": [_user_public(u) for u in users]}), 200


@auth_bp.route("/users", methods=["POST"])
@require_permission("manage_users")
def create_user():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    role = payload.get("role") or "analyst"

    if not email or "@" not in email:
        return jsonify({"error": "A valid email is required"}), 400
    if len(password) < 12:
        return jsonify({"error": "Password must be at least 12 characters"}), 400
    if role not in VALID_ROLES:
        return jsonify({"error": f"role must be one of: {', '.join(VALID_ROLES)}"}), 400
    if AdminUser.query.filter_by(email=email).first() is not None:
        return jsonify({"error": "A user with that email already exists"}), 400

    new_user = AdminUser(email=email, password_hash=hash_password(password), role=role)
    db.session.add(new_user)
    db.session.flush()

    audit_log.record(
        "user.create", actor=g.current_user, target_type="AdminUser", target_id=new_user.id,
        previous_values=None, request=request,
    )
    db.session.commit()

    return jsonify(_user_public(new_user)), 201


@auth_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@require_permission("manage_users")
def deactivate_user(user_id):
    user = AdminUser.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    if user.id == g.current_user.id:
        return jsonify({"error": "You cannot deactivate your own account"}), 400

    previous_values = {"is_active": user.is_active}
    user.is_active = False
    audit_log.record(
        "user.deactivate", actor=g.current_user, target_type="AdminUser", target_id=user.id,
        previous_values=previous_values, request=request,
    )
    db.session.commit()

    return jsonify(_user_public(user)), 200
