from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from celery import Celery  # type: ignore[import-untyped]
from kombu.exceptions import OperationalError
from sqlalchemy import select

from app.analysis.static import candidates_from_diff
from app.core.config import get_settings
from app.core.errors import PrismError
from app.db.session import SessionLocal
from app.models import Finding, OutboxEvent, Review, ReviewStatus
from app.services.diff import parse_unified_diff
from app.services.github import fetch_pull_request, fetch_pull_request_files, parse_pull_request_url
from app.verification.evidence import verify_candidate

celery_app = Celery("prism", broker=get_settings().redis_url, backend=get_settings().redis_url)
celery_app.conf.update(task_default_queue="reviews", task_serializer="json", accept_content=["json"], result_serializer="json", task_acks_late=True, worker_prefetch_multiplier=1)


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
        events = list((await session.scalars(select(OutboxEvent).where(OutboxEvent.published_at.is_(None)).order_by(OutboxEvent.created_at).limit(100).with_for_update(skip_locked=True))).all())
        for event in events:
            review_id = event.payload.get("review_id")
            if isinstance(review_id, str) and enqueue_review(review_id):
                event.published_at = datetime.now(UTC)
                event.attempts += 1
                dispatched += 1
    return dispatched


@celery_app.task(bind=True, name="prism.process_review", max_retries=3, acks_late=True)  # type: ignore[untyped-decorator]
def process_review(self: Any, review_id: str) -> str:
    try:
        return asyncio.run(_process_review(review_id))
    except PrismError as exc:
        retryable = exc.status_code >= 500
        asyncio.run(_set_review_state(review_id, ReviewStatus.queued if retryable else ReviewStatus.failed, exc.message))
        if retryable and self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=min(300, 2 ** (self.request.retries + 1))) from exc
        if retryable:
            return "failed"
        return "failed"
    except Exception as exc:
        asyncio.run(_set_review_state(review_id, ReviewStatus.failed, str(exc)))
        if self.request.retries >= self.max_retries:
            raise
        raise self.retry(exc=exc, countdown=min(300, 2 ** (self.request.retries + 1))) from exc


async def _set_review_state(review_id: str, state: ReviewStatus, error: str | None = None) -> None:
    async with SessionLocal() as session:
        review = await session.scalar(select(Review).where(Review.id == review_id).with_for_update())
        if review is not None:
            review.status = state
            review.error_message = error
            review.lease_until = None
            await session.commit()


async def _process_review(review_id: str) -> str:
    async with SessionLocal() as session:
        async with session.begin():
            review = await session.scalar(select(Review).where(Review.id == review_id).with_for_update())
            if review is None:
                return "missing"
            if review.status in {ReviewStatus.completed, ReviewStatus.canceled}:
                return str(review.status.value)
            review.status = ReviewStatus.fetching
            review.attempt_count += 1
            review.lease_until = datetime.now(UTC) + timedelta(minutes=10)

        ref = parse_pull_request_url(review.url)
        settings = get_settings()
        metadata = await fetch_pull_request(ref, settings.github_token)
        files = await fetch_pull_request_files(ref, settings.github_token)
        review.head_sha = metadata["head"]["sha"]
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
        session.add_all(findings)
        review.status = ReviewStatus.completed
        review.lease_until = None
        await session.commit()
        return str(review.status.value)
