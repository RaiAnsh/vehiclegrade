"""Provider-agnostic LLM access, driven entirely by env vars.

No LLM is required for VehicleGrade to work - repair-cost detection and
every other report section are deterministic. This module exists purely so
that an optional AI-explanation layer (see ai_explainer.py) can activate the
moment an API key is added, with zero code changes.

get_llm() returns None (never raises) when nothing is configured, so callers
can treat "no LLM" as a normal, expected state rather than an error case.
"""

import os

_llm_cache = None
_llm_cache_built = False


def _provider_and_key():
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()

    if provider:
        return provider, os.environ.get(f"{provider.upper()}_API_KEY")

    # No explicit provider set - infer one from whichever key is present so
    # adding just an API key (no other config) is enough to activate this.
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic", os.environ["ANTHROPIC_API_KEY"]
    if os.environ.get("OPENAI_API_KEY"):
        return "openai", os.environ["OPENAI_API_KEY"]

    return None, None


def get_llm():
    """Returns a LangChain chat model, or None if no provider is configured."""
    global _llm_cache, _llm_cache_built

    if _llm_cache_built:
        return _llm_cache

    _llm_cache_built = True

    provider, api_key = _provider_and_key()
    if not provider or not api_key:
        _llm_cache = None
        return None

    default_models = {
        "anthropic": "claude-sonnet-4-6",
        "openai": "gpt-4o-mini",
    }
    model = os.environ.get("LLM_MODEL", default_models.get(provider))

    try:
        from langchain.chat_models import init_chat_model

        _llm_cache = init_chat_model(model, model_provider=provider, api_key=api_key, timeout=15)
    except Exception:
        # Any failure to construct the client (bad model name, missing
        # optional dependency, etc.) just means the AI layer stays off.
        _llm_cache = None

    return _llm_cache
