import time

import httpx
import openai
import pytest

from meta_client import client
from meta_client.exceptions import AuthError


def _req():
    return httpx.Request("POST", "https://api.meta.ai/v1/responses")


def _status_error(cls, status, message="err"):
    return cls(message, response=httpx.Response(status, request=_req()), body=None)


def test_missing_key_raises_auth_error(monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    client.reset_client()
    with pytest.raises(AuthError):
        client.get_client()


def test_client_is_cached(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    client.reset_client()
    try:
        assert client.get_client() is client.get_client()
    finally:
        client.reset_client()


def test_retry_then_success(monkeypatch):
    sleeps = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise _status_error(openai.InternalServerError, 500)
        return "ok"

    assert client.call_with_retry(flaky, op="t") == "ok"
    assert len(calls) == 3
    assert sleeps == [1.0, 4.0]


def test_retryable_errors_are_retried(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    for err in (
        openai.APITimeoutError(request=_req()),
        openai.APIConnectionError(request=_req()),
        _status_error(openai.RateLimitError, 429),
        _status_error(openai.InternalServerError, 503),
    ):
        calls = []

        def fn(err=err):
            calls.append(1)
            if len(calls) == 1:
                raise err
            return "ok"

        assert client.call_with_retry(fn, op="t") == "ok"
        assert len(calls) == 2


def test_gives_up_after_two_retries(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    calls = []

    def always_500():
        calls.append(1)
        raise _status_error(openai.InternalServerError, 500)

    with pytest.raises(openai.InternalServerError):
        client.call_with_retry(always_500, op="t")
    assert len(calls) == 3  # initial + 2 retries


def test_400_fails_fast_without_retry(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: (_ for _ in ()).throw(AssertionError))
    with pytest.raises(openai.BadRequestError):
        client.call_with_retry(
            lambda: (_ for _ in ()).throw(_status_error(openai.BadRequestError, 400)),
            op="t",
        )


def test_non_api_errors_are_not_retried():
    with pytest.raises(ValueError, match="bug"):
        client.call_with_retry(lambda: (_ for _ in ()).throw(ValueError("bug")), op="t")


def test_401_becomes_auth_error_without_key_leak(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "sk-sentinel-secret")
    with pytest.raises(AuthError) as exc_info:
        client.call_with_retry(
            lambda: (_ for _ in ()).throw(
                _status_error(openai.AuthenticationError, 401)
            ),
            op="t",
        )
    assert "sk-sentinel-secret" not in str(exc_info.value)


def test_upload_missing_file(monkeypatch, tmp_path):
    with pytest.raises(Exception, match="not found"):
        client.upload_file(tmp_path / "nope.mp4")


def test_upload_success_and_retry(monkeypatch, tmp_path):
    from meta_client.exceptions import MediaError  # noqa: F401 (re-export check)

    path = tmp_path / "clip.mp4"
    path.write_bytes(b"fake-video")
    attempts = []

    class FakeFiles:
        def create(self, **kwargs):
            attempts.append(kwargs)
            if len(attempts) == 1:
                raise _status_error(openai.InternalServerError, 500)
            from types import SimpleNamespace

            assert kwargs["purpose"] == "user_data"
            return SimpleNamespace(id="file-123")

    class FakeSDK:
        files = FakeFiles()

    monkeypatch.setattr(client, "get_client", lambda: FakeSDK())
    monkeypatch.setattr(time, "sleep", lambda s: None)
    assert client.upload_file(path) == "file-123"
    assert len(attempts) == 2
