from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg
import pytest
import redis

pytestmark = pytest.mark.integration


def _dsn() -> str:
    return os.getenv("PRISM_ALEMBIC_DATABASE_URL", "postgresql://prism:prism@localhost:5432/prism").replace("postgresql+psycopg", "postgresql").replace("postgresql+asyncpg", "postgresql")


def _enabled() -> None:
    if os.getenv("PRISM_INTEGRATION") != "1":
        pytest.skip("set PRISM_INTEGRATION=1 to run Docker integration tests")


def _cleanup(review_id, repository_id) -> None:
    with psycopg.connect(_dsn()) as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM findings WHERE review_id = %s", (review_id,))
        cursor.execute("DELETE FROM outbox_events WHERE aggregate_id = %s", (str(review_id),))
        cursor.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
        cursor.execute("DELETE FROM repositories WHERE id = %s", (repository_id,))


def _insert_review(status: str = "queued", lease_until: datetime | None = None):
    repository_id = uuid4()
    review_id = uuid4()
    with psycopg.connect(_dsn()) as connection, connection.cursor() as cursor:
        cursor.execute("INSERT INTO repositories (id, full_name) VALUES (%s, %s)", (repository_id, f"integration/{repository_id.hex}"))
        cursor.execute("INSERT INTO reviews (id, repository_id, pr_number, url, status, lease_until) VALUES (%s, %s, 1, %s, %s, %s)", (review_id, repository_id, "https://github.com/integration/repo/pull/1", status, lease_until))
    return review_id, repository_id


def test_redis_service_is_reachable() -> None:
    _enabled()
    client = redis.Redis.from_url(os.getenv("PRISM_REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    assert client.ping() is True


def test_duplicate_delivery_is_idempotent() -> None:
    _enabled()
    delivery_id = f"integration-{uuid4()}"
    try:
        with psycopg.connect(_dsn()) as connection, connection.cursor() as cursor:
            cursor.execute("INSERT INTO webhook_deliveries (delivery_id, event_name, payload_hash) VALUES (%s, %s, %s) ON CONFLICT (delivery_id) DO NOTHING", (delivery_id, "pull_request", "a" * 64))
            first = cursor.rowcount
            cursor.execute("INSERT INTO webhook_deliveries (delivery_id, event_name, payload_hash) VALUES (%s, %s, %s) ON CONFLICT (delivery_id) DO NOTHING", (delivery_id, "pull_request", "a" * 64))
            second = cursor.rowcount
        assert (first, second) == (1, 0)
    finally:
        with psycopg.connect(_dsn()) as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM webhook_deliveries WHERE delivery_id = %s", (delivery_id,))


def test_expired_lease_recovery_creates_durable_dispatch() -> None:
    _enabled()
    review_id, repository_id = _insert_review("fetching", datetime.now(UTC) - timedelta(minutes=1))
    try:
        with psycopg.connect(_dsn()) as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE reviews SET status = 'queued', lease_until = NULL WHERE id = %s AND lease_until < now() RETURNING id", (review_id,))
            assert cursor.fetchone() is not None
            cursor.execute("INSERT INTO outbox_events (id, event_type, aggregate_id, payload) VALUES (%s, %s, %s, %s)", (uuid4(), "review.recovery.requested", str(review_id), '{"review_id": "' + str(review_id) + '"}'))
            cursor.execute("SELECT reviews.status, outbox_events.published_at FROM reviews JOIN outbox_events ON outbox_events.aggregate_id = %s WHERE reviews.id = %s", (str(review_id), review_id))
            assert cursor.fetchone() == ("queued", None)
    finally:
        _cleanup(review_id, repository_id)


def test_concurrent_claims_allow_only_one_worker() -> None:
    _enabled()
    review_id, repository_id = _insert_review()

    def claim() -> bool:
        with psycopg.connect(_dsn()) as connection, connection.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute("SELECT id FROM reviews WHERE id = %s AND status = 'queued' FOR UPDATE SKIP LOCKED", (review_id,))
            row = cursor.fetchone()
            if row is None:
                connection.rollback()
                return False
            cursor.execute("SELECT pg_sleep(0.2)")
            cursor.execute("UPDATE reviews SET status = 'fetching', lease_until = now() + interval '10 minutes' WHERE id = %s", (review_id,))
            connection.commit()
            return True

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: claim(), range(2)))
        assert results.count(True) == 1
    finally:
        _cleanup(review_id, repository_id)


def test_outbox_failure_remains_pending_for_beat_retry() -> None:
    _enabled()
    review_id, repository_id = _insert_review()
    event_id = uuid4()
    try:
        with psycopg.connect(_dsn()) as connection, connection.cursor() as cursor:
            cursor.execute("INSERT INTO outbox_events (id, event_type, aggregate_id, payload, attempts, last_error) VALUES (%s, %s, %s, %s, 1, %s)", (event_id, "review.requested", str(review_id), '{"review_id": "' + str(review_id) + '"}', "redis unavailable"))
            cursor.execute("SELECT published_at, attempts, last_error FROM outbox_events WHERE id = %s", (event_id,))
            assert cursor.fetchone() == (None, 1, "redis unavailable")
    finally:
        _cleanup(review_id, repository_id)
