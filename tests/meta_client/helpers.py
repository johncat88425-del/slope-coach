"""Shared fakes for meta_client tests. No test here may touch the network."""
from __future__ import annotations

from types import SimpleNamespace


class FakeResponses:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        result = self.results.pop(0) if len(self.results) > 1 else self.results[0]
        if isinstance(result, Exception):
            raise result
        return result


def fake_response(output_text="", usage=None):
    return SimpleNamespace(output_text=output_text, usage=usage)


def fake_usage(input_tokens=100, output_tokens=50, cached_tokens=0):
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_tokens_details": {"cached_tokens": cached_tokens},
    }


class FakeClient:
    def __init__(self, results):
        self.responses = FakeResponses(results)
