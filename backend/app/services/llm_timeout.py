"""Shared hard wall-clock timeout wrapper for LLM calls.

A request thread blocked on a hanging network call can outlive gunicorn's
own worker timeout and get hard-killed before any try/except in the calling
code ever runs. Running the call in a separate thread and bounding it with
`Future.result(timeout=...)` gives every LLM call site (ai_explainer.py,
listing_parser_llm.py, ...) the same second, code-level guarantee that a
slow/hung provider can never take the rest of the request down with it.
"""

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

DEFAULT_TIMEOUT_SECONDS = 10


def run_with_timeout(fn, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    """Run fn() with a hard wall-clock timeout.

    Returns fn()'s return value, or None if it times out or raises for any
    reason - callers should treat None as "the LLM step didn't happen" and
    fall back accordingly, never as an error to propagate.
    """
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        return executor.submit(fn).result(timeout=timeout_seconds)
    except (Exception, FutureTimeoutError):
        return None
    finally:
        # wait=False: if fn() timed out, don't block the caller waiting for a
        # possibly-hung network call to finish - let it die on its own.
        executor.shutdown(wait=False)
