"""Optional Sentry error tracking, enabled only when SENTRY_DSN is set.

Mirrors the pattern used for the LLM providers (app/services/llm_client.py):
the integration is entirely env-var-gated and the app must behave exactly
the same, crash-wise, whether or not it's configured. We only ever set this
up - we never require it, since creating the actual Sentry account/DSN is
something only the project owner can do.
"""

import os


def init_error_tracking(app):
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return

    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration()],
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0")),
    )
