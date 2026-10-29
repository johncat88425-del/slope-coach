"""T29: backend uses MetaHooks when a key is configured, else MockHooks."""
from __future__ import annotations

import sys

import pytest

from backend import main, model_hooks


@pytest.fixture(autouse=True)
def restore_hooks():
    current = model_hooks.get_hooks()
    yield
    model_hooks.set_hooks(current)


def test_no_key_stays_on_mock(monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    model_hooks.set_hooks(model_hooks.MockHooks())
    assert main._wire_model_hooks() == "mock"
    assert isinstance(model_hooks.get_hooks(), model_hooks.MockHooks)


def test_key_wires_meta_hooks(monkeypatch):
    pytest.importorskip("meta_client.hooks")
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    model_hooks.set_hooks(model_hooks.MockHooks())
    from meta_client.hooks import MetaHooks

    assert main._wire_model_hooks() == "meta"
    assert isinstance(model_hooks.get_hooks(), MetaHooks)


def test_missing_meta_client_stays_on_mock(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "meta_client.hooks", None)
    model_hooks.set_hooks(model_hooks.MockHooks())
    assert main._wire_model_hooks() == "mock"
    assert isinstance(model_hooks.get_hooks(), model_hooks.MockHooks)
