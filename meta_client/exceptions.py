"""Error types for meta_client. Transport-level openai errors (4xx) propagate
unchanged so callers can distinguish permanent request problems."""
from __future__ import annotations


class MetaClientError(RuntimeError):
    """Base class for meta_client failures."""


class AuthError(MetaClientError):
    """MODEL_API_KEY is missing or rejected (401)."""


class SpendLimitExceeded(MetaClientError):
    """Cumulative spend reached SPEND_LIMIT_USD; no new paid calls."""


class ModelOutputError(MetaClientError):
    """Model output failed schema/range validation after retries."""


class MediaError(MetaClientError):
    """Local media problem: missing file, bad format, ffmpeg/ffprobe missing."""


class TrackingError(MetaClientError):
    """SAM tracking failed (upload, request, or wire-format parse)."""
