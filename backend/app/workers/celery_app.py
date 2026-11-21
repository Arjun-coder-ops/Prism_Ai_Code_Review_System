from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from celery import Celery  # type: ignore[import-untyped]
from kombu.exceptions import OperationalError
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import selectinload

from app.analysis.static import candidates_from_diff
from app.core.config import get_settings
from app.core.errors import PrismError
from app.db.session import SessionLocal
from app.github.auth import fetch_installation_token, load_private_key
from app.models import Finding, OutboxEvent, Repository, Review, ReviewStatus
from app.services.diff import parse_unified_diff
from app.services.github import (
    ensure_head_sha_stable,
    fetch_pull_request,
    fetch_pull_request_files,
    parse_pull_request_url,
)
from app.verification.evidence import verify_candidate

celery_app = Celery("prism", broker=get_settings().redis_url, backend=get_settings().redis_url)
celery_app.conf.update(
    task_default_queue="reviews",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "dispatch-outbox": {"task": "prism.dispatch_outbox", "schedule": 30.0},
        "recover-stale-reviews": {"task": "prism.recover_stale_reviews", "schedule": 60.0},
    },
)


@celery_app.task(name="prism.healthcheck")  # type: ignore[untyped-decorator]
def healthcheck() -> str:
    return "ok"


def enqueue_review(review_id: str) -> bool:
    """Submit a durable review job without turning broker outages into false success."""
    try:
        process_review.delay(review_id)
    except (OperationalError, OSError):
        return False
    return True


@celery_app.task(name="prism.dispatch_outbox")  # type: ignore[untyped-decorator]
def dispatch_outbox() -> int:
    return asyncio.run(_dispatch_outbox())


async def _dispatch_outbox() -> int:
    dispatched = 0
    async with SessionLocal() as session, session.begin():
        now = datetime.now(UTC)
        events = list((await session.scalars(select(OutboxEvent).where(OutboxEvent.published_at.is_(None), OutboxEvent.attempts < 10, or_(OutboxEvent.next_attempt_at.is_(None), OutboxEvent.next_attempt_at <= now)).order_by(OutboxEvent.created_at).limit(100).with_for_update(skip_locked=True))).all())
        for event in events:
            review_id = event.payload.get("review_id")
            event.attempts += 1
            event.next_attempt_at = now + timedelta(seconds=min(300, 2 ** event.attempts))
            if isinstance(review_id, str) and enqueue_review(review_id):
                event.published_at = now
                event.last_error = None
                dispatched += 1
            else:
                event.last_error = "review queue unavailable"
    return dispatched


@celery_app.task(name="prism.recover_stale_reviews")  # type: ignore[untyped-decorator]
def recover_stale_reviews() -> int:
    return asyncio.run(_recover_stale_reviews())


async def _recover_stale_reviews() -> int:
    recovered = 0
    async with SessionLocal() as session, session.begin():
        now = datetime.now(UTC)
        reviews = list((await session.scalars(select(Review).where(Review.status.in_([ReviewStatus.fetching, ReviewStatus.analyzing]), Review.lease_until < now).with_for_update(skip_locked=True))).all())
        for review in reviews:
            review.status = ReviewStatus.queued
            review.lease_until = None
            review.error_message = "Recovered after an expired worker lease."
            pending = await session.scalar(select(OutboxEvent).where(OutboxEvent.aggregate_id == str(review.id), OutboxEvent.published_at.is_(None), OutboxEvent.attempts < 10).limit(1))
            if pending is None:
                session.add(OutboxEvent(event_type="review.recovery.requested", aggregate_id=str(review.id), payload={"review_id": str(review.id)}))
            recovered += 1
    return recovered


@celery_app.task(bind=True, name="prism.process_review", max_retries=3, acks_late=True)  # type: ignore[untyped-decorator]
def process_review(self: Any, review_id: str) -> str:
    try:
        return asyncio.run(_process_review(review_id))
    except PrismError as exc:
        retryable = exc.status_code >= 500 and self.request.retries < self.max_retries
        asyncio.run(_set_review_state(review_id, retry_state(self.request.retries, self.max_retries) if exc.status_code >= 500 else ReviewStatus.failed, exc.message))
        if retryable:
            raise self.retry(exc=exc, countdown=min(300, 2 ** (self.request.retries + 1))) from exc
        return "failed"
    except Exception as exc:
        retryable = self.request.retries < self.max_retries
        asyncio.run(_set_review_state(review_id, retry_state(self.request.retries, self.max_retries), str(exc)))
        if not retryable:
            raise
        raise self.retry(exc=exc, countdown=min(300, 2 ** (self.request.retries + 1))) from exc


def retry_state(retries: int, max_retries: int) -> ReviewStatus:
    return ReviewStatus.failed if retries >= max_retries else ReviewStatus.queued


async def _set_review_state(review_id: str, state: ReviewStatus, error: str | None = None) -> None:
    async with SessionLocal() as session:
        review = await session.scalar(select(Review).where(Review.id == review_id).with_for_update())
        if review is not None and review.status not in {ReviewStatus.completed, ReviewStatus.canceled}:
            review.status = state
            review.error_message = error
            review.lease_until = None
            await session.commit()


async def _process_review(review_id: str) -> str:
    async with SessionLocal() as session:
        async with session.begin():
            review = await session.scalar(select(Review).options(selectinload(Review.repository).selectinload(Repository.installation)).where(Review.id == review_id).with_for_update(skip_locked=True))
            if review is None:
                return "missing"
            if review.status in {ReviewStatus.completed, ReviewStatus.canceled}:
                return str(review.status.value)
            now = datetime.now(UTC)
            if review.status in {ReviewStatus.fetching, ReviewStatus.analyzing} and review.lease_until is not None and review.lease_until > now:
                return "in_flight"
            review.status = ReviewStatus.fetching
            review.attempt_count += 1
            review.lease_until = now + timedelta(minutes=10)

        ref = parse_pull_request_url(review.url)
        settings = get_settings()
        token = settings.github_token
        if review.repository is not None and review.repository.installation_id is not None:
            if not settings.github_app_id or not settings.github_private_key_path:
                raise PrismError("github_app_unconfigured", "The authorized GitHub installation cannot be accessed yet.", 503)
            token = await fetch_installation_token(settings.github_app_id, load_private_key(settings.github_private_key_path), review.repository.installation.installation_id if review.repository.installation else 0)
        metadata = await fetch_pull_request(ref, token)
        initial_sha = metadata["head"]["sha"]
        files = await fetch_pull_request_files(ref, token)
        latest_metadata = await fetch_pull_request(ref, token)
        ensure_head_sha_stable(initial_sha, latest_metadata["head"]["sha"])
        review.head_sha = initial_sha
        review.changed_paths = [path for file in files if isinstance((path := file.get("filename")), str)]
        review.status = ReviewStatus.analyzing
        await session.commit()

        findings: list[Finding] = []
        for file in files:
            patch = file.get("patch")
            path = file.get("filename")
            if not isinstance(patch, str) or not isinstance(path, str):
                continue
            diff_lines = parse_unified_diff(patch, path)
            for candidate in candidates_from_diff(diff_lines):
                verified = verify_candidate(candidate, diff_lines)
                if verified is None:
                    continue
                findings.append(Finding(review_id=review.id, path=candidate.path, start_line=candidate.line, end_line=candidate.line, severity=candidate.severity, category=candidate.category, title=candidate.title, explanation=candidate.explanation, evidence=verified.evidence, verification_state="verified"))
        await session.execute(delete(Finding).where(Finding.review_id == review.id))
        session.add_all(findings)
        review.status = ReviewStatus.completed
        review.lease_until = None
        await session.commit()
        return str(review.status.value)
