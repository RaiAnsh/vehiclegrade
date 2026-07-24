"""Single call site for writing to AdminAuditLog, so every admin action -
auth events and ingestion state changes alike - is logged with the same
shape (actor, action, target, previous values, request metadata) instead of
each route hand-rolling its own logging.

Callers pass the current `flask.request` object (or None for CLI-triggered
actions) so IP/user-agent capture happens in exactly one place.
"""

from flask import request as flask_request

from app.extensions import db
from app.models import AdminAuditLog


def record(action, actor=None, actor_email=None, target_type=None, target_id=None, previous_values=None,
           affected_record_ids=None, request=None):
    """Adds an AdminAuditLog row to the current session. Does not commit -
    callers should commit as part of the same transaction as the action
    being logged, so the audit entry and the change it describes are
    atomic (either both persist or neither does).
    """
    req = request if request is not None else flask_request
    ip_address = None
    user_agent = None
    try:
        ip_address = req.headers.get("X-Forwarded-For", req.remote_addr)
        user_agent = (req.headers.get("User-Agent") or "")[:255]
    except RuntimeError:
        pass  # outside a request context (e.g. CLI command)

    entry = AdminAuditLog(
        actor_id=actor.id if actor is not None else None,
        actor_email=(actor.email if actor is not None else actor_email),
        action=action,
        target_type=target_type,
        target_id=target_id,
        previous_values=previous_values,
        affected_record_ids=affected_record_ids,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(entry)
    return entry
