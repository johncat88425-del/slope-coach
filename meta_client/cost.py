"""Cost accounting at official Meta Model API prices.

Source: https://dev.meta.ai/docs/pricing-rate-limits (read 2026-10-28).
Every paid call must record its usage here BEFORE the next call is made; the
tracker refuses new calls once the cumulative total reaches SPEND_LIMIT_USD
(default 120). The log lives at data/cost_log.csv (committed: it holds only
aggregate token/frame counts, never prompts, media, or keys).
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

from .exceptions import SpendLimitExceeded

DEFAULT_LIMIT_USD = 120.0
DEFAULT_LOG_PATH = Path("data/cost_log.csv")

# USD per 1M tokens: (input, cached_input, output). From the official pricing
# page; contributor tiers bill training-data opt-in traffic at a discount.
TOKEN_PRICES: dict[str, tuple[float, float, float]] = {
    "muse-spark-1.3": (1.25, 0.15, 4.25),
    "muse-spark-1.2": (1.25, 0.15, 4.25),
    "muse-spark-1.1": (1.25, 0.15, 4.25),
    "muse-spark-1.3-contributor": (0.10, 0.002, 0.20),
    "muse-spark-1.2-contributor": (0.10, 0.002, 0.20),
    "muse-wonder-1.0": (4.00, 0.20, 20.00),
}

# SAM 3.1 is billed per image / per video frame, not per token. Each video
# request bills at least 50 frames; usage.video_frames_processed reports the
# billed count.
SAM_IMAGE_USD_PER_1K = 2.50
SAM_VIDEO_USD_PER_1K_FRAMES = 0.20
SAM_VIDEO_MIN_BILLED_FRAMES = 50

IMAGE_USD_PER_IMAGE = 0.01  # muse-image-1.0
VOICE_USD_PER_HOUR = 0.18  # muse-voice-transcribe-1.0, whole seconds, floor

CSV_COLUMNS = (
    "timestamp_utc",
    "model",
    "operation",
    "input_tokens",
    "cached_tokens",
    "output_tokens",
    "images",
    "frames",
    "audio_seconds",
    "cost_usd",
)


def token_cost_usd(
    model: str, input_tokens: int, output_tokens: int, cached_tokens: int = 0
) -> float:
    try:
        price_in, price_cached, price_out = TOKEN_PRICES[model]
    except KeyError:
        raise ValueError(f"no recorded price for model {model!r}") from None
    return (
        (input_tokens - cached_tokens) * price_in
        + cached_tokens * price_cached
        + output_tokens * price_out
    ) / 1_000_000


def sam_video_cost_usd(frames_billed: int) -> float:
    return max(frames_billed, SAM_VIDEO_MIN_BILLED_FRAMES) * (
        SAM_VIDEO_USD_PER_1K_FRAMES / 1000
    )


def sam_image_cost_usd(n_images: int) -> float:
    return n_images * SAM_IMAGE_USD_PER_1K / 1000


def voice_cost_usd(audio_seconds: float) -> float:
    import math

    return math.floor(audio_seconds) / 3600 * VOICE_USD_PER_HOUR


class CostTracker:
    """Append-only spend log with a hard ceiling."""

    def __init__(
        self,
        log_path: str | Path = DEFAULT_LOG_PATH,
        limit_usd: float | None = None,
    ) -> None:
        self.log_path = Path(log_path)
        if limit_usd is None:
            limit_usd = float(os.environ.get("SPEND_LIMIT_USD", DEFAULT_LIMIT_USD))
        self.limit_usd = limit_usd

    def total_usd(self) -> float:
        if not self.log_path.exists():
            return 0.0
        total = 0.0
        with open(self.log_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    total += float(row.get("cost_usd") or 0)
                except ValueError:
                    continue
        return total

    def check(self, extra_usd: float = 0.0) -> float:
        """Return current total, or raise SpendLimitExceeded at the ceiling.

        extra_usd pre-books a known upcoming cost (T181): the call is
        refused when total + extra would reach the ceiling.
        """
        total = self.total_usd()
        if total + extra_usd >= self.limit_usd:
            raise SpendLimitExceeded(
                f"cumulative Meta API spend ${total:.4f} plus this "
                f"${extra_usd:.4f} call reached the "
                f"${self.limit_usd:.2f} limit; refusing new paid calls."
            )
        return total

    def record(
        self,
        model: str,
        operation: str,
        *,
        input_tokens: int = 0,
        cached_tokens: int = 0,
        output_tokens: int = 0,
        images: int = 0,
        frames: int = 0,
        audio_seconds: float = 0.0,
    ) -> float:
        """Check the ceiling, append one row, return this call's cost in USD."""
        self.check()
        cost = 0.0
        if input_tokens or output_tokens or cached_tokens:
            cost += token_cost_usd(model, input_tokens, output_tokens, cached_tokens)
        if images:
            if model != "sam-3.1":
                raise ValueError(f"image billing is only defined for sam-3.1, not {model}")
            cost += sam_image_cost_usd(images)
        if frames:
            if model != "sam-3.1":
                raise ValueError(f"frame billing is only defined for sam-3.1, not {model}")
            cost += sam_video_cost_usd(frames)
        if audio_seconds:
            cost += voice_cost_usd(audio_seconds)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.log_path.exists()
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerow(
                {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "model": model,
                    "operation": operation,
                    "input_tokens": input_tokens,
                    "cached_tokens": cached_tokens,
                    "output_tokens": output_tokens,
                    "images": images,
                    "frames": frames,
                    "audio_seconds": audio_seconds,
                    "cost_usd": f"{cost:.6f}",
                }
            )
        return cost


_tracker: CostTracker | None = None


def get_tracker() -> CostTracker:
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker
