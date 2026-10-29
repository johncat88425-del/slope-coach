"""Shared OpenAI SDK client, retry policy, and timeouts.

- base_url comes from META_BASE_URL (default https://api.meta.ai/v1).
- key comes from MODEL_API_KEY only; it is never logged, printed, or written.
- every paid call goes through call_with_retry: at most 2 retries, only for
  transient failures (timeout, connection error, 429, 5xx). 4xx fails fast.
"""
from __future__ import annotations

import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

from .exceptions import AuthError

BASE_URL = os.environ.get("META_BASE_URL", "https://api.meta.ai/v1")

SPARK_MODEL = os.environ.get("SPARK_MODEL", "muse-spark-1.3")
SAM_MODEL = "sam-3.1"

MAX_RETRIES = 2
RETRY_BACKOFF_S = (1.0, 4.0)  # wait before retry 1 and retry 2

# Per-call timeouts (seconds). SAM video segmentation of a short clip and
# file uploads get the longest budgets; nothing may block forever.
SPARK_TIMEOUT_S = 120.0
SPARK_VIDEO_TIMEOUT_S = 300.0
SAM_TIMEOUT_S = 600.0
UPLOAD_TIMEOUT_S = 300.0

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """Return the shared SDK client. Raises AuthError when no key is set."""
    global _client
    if _client is None:
        api_key = os.environ.get("MODEL_API_KEY")
        if not api_key:
            raise AuthError(
                "MODEL_API_KEY is not set; put the key in .env (never in code)."
            )
        _client = OpenAI(base_url=BASE_URL, api_key=api_key)
    return _client


def reset_client() -> None:
    """Drop the cached client (tests, key rotation)."""
    global _client
    _client = None


def upload_file(path: str | Path, *, timeout: float = UPLOAD_TIMEOUT_S) -> str:
    """Upload a local file via POST /v1/files (purpose=user_data).

    Upload is synchronous: success means the file is ready to reference by
    the returned file_id. Raises MediaError for local problems.
    """
    from .exceptions import MediaError

    p = Path(path)
    if not p.is_file():
        raise MediaError(f"media file not found: {p}")
    client = get_client()

    def _do() -> str:
        with open(p, "rb") as f:
            obj = client.files.create(file=f, purpose="user_data", timeout=timeout)
        return str(obj.id)

    return call_with_retry(_do, op=f"files.upload:{p.name}")


T = TypeVar("T")


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (APITimeoutError, APIConnectionError, RateLimitError)):
        return True
    if isinstance(exc, InternalServerError):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code >= 500
    return False


def call_with_retry(
    fn: Callable[[], T],
    *,
    max_retries: int = MAX_RETRIES,
    op: str = "Meta API call",
) -> T:
    """Run fn, retrying transient failures at most max_retries times.

    Non-retryable errors (400/401/403/404, validation bugs) are re-raised
    immediately: a 400 is permanent for that request (docs: "don't retry it
    unchanged"). A 401 is wrapped in AuthError.
    """
    last: BaseException | None = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except APIStatusError as exc:
            last = exc
            if exc.status_code == 401:
                raise AuthError(
                    "Meta API rejected the key (401); check MODEL_API_KEY."
                ) from exc
            if not _is_retryable(exc) or attempt >= max_retries:
                raise
        except (APITimeoutError, APIConnectionError, RateLimitError) as exc:
            last = exc
            if attempt >= max_retries:
                raise
        if attempt < max_retries:
            wait = RETRY_BACKOFF_S[min(attempt, len(RETRY_BACKOFF_S) - 1)]
            time.sleep(wait)
    assert last is not None  # unreachable: loop always returns or raises
    raise last
