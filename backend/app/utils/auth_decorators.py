"""Route decorators enforcing admin authentication + role-based permission
checks. `require_permission` is the only decorator most routes need - it
authenticates the Bearer access token AND checks the caller's role against
ROLE_PERMISSIONS in one step, so there's no route that authenticates
without also checking authorization (a common source of "logged in but
shouldn't be able to do that" bugs).

New roles/permissions never require touching this file - see
app.models.admin_user.ROLE_PERMISSIONS.
"""

from functools import wraps

from flask import g, jsonify, request

from app.models import AdminUser
from app.services.auth import AuthenticationError, decode_access_token


def _authenticate_request():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing bearer token")
    token = auth_header[len("Bearer "):].strip()
    claims = decode_access_token(token)

    user = AdminUser.query.get(int(claims["sub"]))
    if user is None or not user.is_active:
        raise AuthenticationError("Account is inactive or no longer exists")
    return user


def require_permission(permission):
    """Decorator factory: `@require_permission("review")`."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                user = _authenticate_request()
            except AuthenticationError as exc:
                return jsonify({"error": str(exc)}), 401

            if not user.has_permission(permission):
                return jsonify({"error": f"Role '{user.role}' does not have '{permission}' permission"}), 403

            g.current_user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator
