from __future__ import annotations

import hashlib
import hmac
import json
import os
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import SessionLocal, get_session
from app.main import app

pytestmark = pytest.mark.integration


def _dsn() -> str:
    return os.getenv("PRISM_ALEMBIC_DATABASE_URL", "postgresql://prism:prism@localhost:5432/prism").replace("postgresql+psycopg", "postgresql").replace("postgresql+asyncpg", "postgresql")


def _enabled() -> None:
    if os.getenv("PRISM_INTEGRATION") != "1":
        pytest.skip("set PRISM_INTEGRATION=1 to run Docker integration tests")


def _signed(body: bytes) -> str:
    return "sha256=" + hmac.new(b"integration-secret", body, hashlib.sha256).hexdigest()


def test_installation_repository_sync_through_fastapi() -> None:
    _enabled()
    installation_id = 700_000 + uuid4().int % 100_000
    added_name = f"integration/repo-{installation_id}"
    delivery_ids: list[str] = []

    async def override_session():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    os.environ["PRISM_GITHUB_WEBHOOK_SECRET"] = "integration-secret"
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            installation = {"id": installation_id, "account": {"login": "integration"}}
            created = json.dumps({"action": "created", "installation": installation}).encode()
            delivery_id = str(uuid4())
            delivery_ids.append(delivery_id)
            response = client.post("/api/webhooks/github", content=created, headers={"x-github-event": "installation", "x-github-delivery": delivery_id, "x-hub-signature-256": _signed(created)})
            assert response.status_code == 202

            added_payload = {"installation": {"id": installation_id}, "repositories_added": [{"id": installation_id, "full_name": added_name, "private": True}], "repositories_removed": []}
            added = json.dumps(added_payload).encode()
            delivery_id = str(uuid4())
            delivery_ids.append(delivery_id)
            response = client.post("/api/webhooks/github", content=added, headers={"x-github-event": "installation_repositories", "x-github-delivery": delivery_id, "x-hub-signature-256": _signed(added)})
            assert response.status_code == 202

            with psycopg.connect(_dsn()) as connection, connection.cursor() as cursor:
                cursor.execute("SELECT installation_id FROM repositories WHERE full_name = %s", (added_name,))
                row = cursor.fetchone()
                assert row is not None
                cursor.execute("SELECT id FROM github_installations WHERE installation_id = %s", (installation_id,))
                installation_row = cursor.fetchone()
                assert installation_row is not None
                assert row[0] == installation_row[0]

            removed = json.dumps({"installation": {"id": installation_id}, "repositories_added": [], "repositories_removed": [{"full_name": added_name}]}).encode()
            delivery_id = str(uuid4())
            delivery_ids.append(delivery_id)
            response = client.post("/api/webhooks/github", content=removed, headers={"x-github-event": "installation_repositories", "x-github-delivery": delivery_id, "x-hub-signature-256": _signed(removed)})
            assert response.status_code == 202
            with psycopg.connect(_dsn()) as connection, connection.cursor() as cursor:
                cursor.execute("SELECT installation_id FROM repositories WHERE full_name = %s", (added_name,))
                assert cursor.fetchone() == (None,)
    finally:
        with psycopg.connect(_dsn()) as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM webhook_deliveries WHERE delivery_id = ANY(%s)", (delivery_ids,))
            cursor.execute("DELETE FROM repositories WHERE full_name = %s", (added_name,))
            cursor.execute("DELETE FROM github_installations WHERE installation_id = %s", (installation_id,))
        app.dependency_overrides.clear()
        os.environ.pop("PRISM_GITHUB_WEBHOOK_SECRET", None)
        get_settings.cache_clear()
