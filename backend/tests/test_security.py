from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core import security
from app.core.errors import PrismError


def test_configured_api_key_is_required(monkeypatch) -> None:
    monkeypatch.setattr(security, "get_settings", lambda: SimpleNamespace(api_key="expected", rate_limit_per_minute=30))
    request = SimpleNamespace(headers={"x-prism-api-key": "wrong"})
    with pytest.raises(PrismError) as error:
        security.require_api_key(request).send(None)
    assert error.value.status_code == 401


def test_unconfigured_api_key_keeps_local_flow_open(monkeypatch) -> None:
    monkeypatch.setattr(security, "get_settings", lambda: SimpleNamespace(api_key=None, rate_limit_per_minute=30))
    coroutine = security.require_api_key(SimpleNamespace(headers={}))
    with pytest.raises(StopIteration):
        coroutine.send(None)


def test_repository_allowlist_rejects_unscoped_data(monkeypatch) -> None:
    monkeypatch.setattr(security, "get_settings", lambda: SimpleNamespace(authorized_repository_list={"acme/allowed"}))
    with pytest.raises(PrismError) as error:
        security.ensure_repository_access("acme/private")
    assert error.value.status_code == 403
