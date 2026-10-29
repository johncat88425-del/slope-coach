"""meta_client: all Meta Model API calls for Slope Coach (T05).

Uses the OpenAI Python SDK against https://api.meta.ai/v1 with the key from
the MODEL_API_KEY environment variable. The key is never printed or written.

Submodules:
  client: shared SDK client, retry, timeouts
  cost:   official-price cost accounting with a hard spend limit
  spark:  muse-spark-1.3 scene check + release-time suggestion
  sam:    sam-3.1 video tracking (ffmpeg -> 15 fps -> Files API -> Responses API)
  hooks:  MetaHooks, the backend ModelHooks implementation
"""
from .exceptions import (
    AuthError,
    MediaError,
    MetaClientError,
    ModelOutputError,
    SpendLimitExceeded,
    TrackingError,
)

__all__ = [
    "AuthError",
    "MediaError",
    "MetaClientError",
    "ModelOutputError",
    "SpendLimitExceeded",
    "TrackingError",
]
