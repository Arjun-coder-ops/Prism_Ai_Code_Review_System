from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import Response
from kombu.exceptions import OperationalError
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import PrismError
from app.core.metrics import review_requests
from app.db.session import get_session
from app.github.webhooks import payload_hash, verify_signature
from app.intelligence.impact import infer_change_impact
from app.intelligence.test_gaps import recommend_test_gaps
from app.models import Finding, OutboxEvent, Repository, Review, ReviewStatus, WebhookDelivery
from app.schemas import FindingOut, HealthOut, ReviewCreate, ReviewOut
from app.workers.celery_app import dispatch_outbox, enqueue_review

router = APIRouter(prefix="/api")
SessionDep = Annotated[AsyncSession, Depends(get_session)]
logger = logging.getLogger(__name__)


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(status="ok", version="0.1.0")


@router.get("/readiness", response_model=HealthOut)
async def readiness(session: SessionDep) -> HealthOut:
    await session.execute(select(1))
    return HealthOut(status="ready", version="0.1.0")


@router.post("/reviews", response_model=ReviewOut, status_code=status.HTTP_202_ACCEPTED)
async def create_review(payload: ReviewCreate, session: SessionDep) -> Review:
    from app.services.github import parse_pull_request_url
    ref = parse_pull_request_url(str(payload.url))
    repo = await session.scalar(select(Repository).where(Repository.full_name == f"{ref.owner}/{ref.repo}"))
    if repo is None:
        repo = Repository(full_name=f"{ref.owner}/{ref.repo}")
        session.add(repo)
        await session.flush()
    existing = await session.scalar(select(Review).where(Review.repository_id == repo.id, Review.pr_number == ref.number, Review.status.in_([ReviewStatus.queued, ReviewStatus.fetching, ReviewStatus.analyzing])))
    if existing:
        return existing
    review = Review(repository_id=repo.id, pr_number=ref.number, url=str(payload.url), status=ReviewStatus.queued)
    session.add(review)
    await session.commit()
    await session.refresh(review)
    review_requests.inc()
    if not enqueue_review(str(review.id)):
        logger.warning("review_enqueue_deferred", extra={"review_id": str(review.id)})
    return review


@router.get("/reviews/{review_id}", response_model=ReviewOut)
async def get_review(review_id: uuid.UUID, session: SessionDep) -> Review:
    review = await session.scalar(select(Review).where(Review.id == review_id))
    if review is None:
        from app.core.errors import PrismError
        raise PrismError("review_not_found", "Review does not exist.", 404)
    await session.refresh(review, ["findings"])
    return review


@router.get("/reviews/{review_id}/findings", response_model=list[FindingOut])
async def list_findings(review_id: uuid.UUID, session: SessionDep) -> list[Finding]:
    return list((await session.scalars(select(Finding).where(Finding.review_id == review_id).order_by(Finding.start_line))).all())


@router.get("/reviews/{review_id}/impact")
async def review_impact(review_id: uuid.UUID, session: SessionDep) -> list[dict[str, object]]:
    review = await session.scalar(select(Review).where(Review.id == review_id))
    if review is None:
        raise PrismError("review_not_found", "Review does not exist.", 404)
    return [{"component": item.component, "reason": item.reason, "confidence": item.confidence} for item in infer_change_impact(review.changed_paths)]


@router.get("/reviews/{review_id}/test-gaps")
async def review_test_gaps(review_id: uuid.UUID, session: SessionDep) -> list[dict[str, str]]:
    review = await session.scalar(select(Review).where(Review.id == review_id))
    if review is None:
        raise PrismError("review_not_found", "Review does not exist.", 404)
    gaps = recommend_test_gaps(review.changed_paths, set())
    return [{"source_path": gap.source_path, "suggested_path": gap.suggested_path, "reason": gap.reason} for gap in gaps]


@router.post("/webhooks/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(request: Request, session: SessionDep) -> dict[str, str]:
    body = await request.body()
    verify_signature(body, request.headers.get("x-hub-signature-256"), get_settings().github_webhook_secret)
    delivery_id = request.headers.get("x-github-delivery")
    event_name = request.headers.get("x-github-event")
    if not delivery_id or not event_name:
        raise PrismError("invalid_webhook_headers", "GitHub delivery and event headers are required.", 400)
    if await session.scalar(select(WebhookDelivery).where(WebhookDelivery.delivery_id == delivery_id)):
        return {"status": "duplicate"}
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise PrismError("invalid_webhook_payload", "Webhook body is not valid JSON.", 400) from exc
    if not isinstance(payload, dict):
        raise PrismError("invalid_webhook_payload", "Webhook body must be a JSON object.", 400)
    delivery = WebhookDelivery(delivery_id=delivery_id, event_name=event_name, payload_hash=payload_hash(body), processed_at=datetime.now(UTC))
    session.add(delivery)
    review_id: uuid.UUID | None = None
    if event_name == "pull_request" and payload.get("action") in {"opened", "reopened", "synchronize"}:
        repository_data = payload.get("repository") or {}
        pull_request = payload.get("pull_request") or {}
        full_name = repository_data.get("full_name")
        number = payload.get("number")
        head_sha = (pull_request.get("head") or {}).get("sha")
        if not isinstance(full_name, str) or not isinstance(number, int) or not isinstance(head_sha, str):
            raise PrismError("invalid_pull_request_event", "Webhook lacks repository, PR number, or head SHA.", 400)
        repo = await session.scalar(select(Repository).where(Repository.full_name == full_name))
        if repo is None:
            repo = Repository(full_name=full_name, github_id=repository_data.get("id"))
            session.add(repo)
            await session.flush()
        review = await session.scalar(select(Review).where(Review.repository_id == repo.id, Review.pr_number == number, Review.head_sha == head_sha))
        if review is None:
            review = Review(repository_id=repo.id, pr_number=number, url=f"https://github.com/{full_name}/pull/{number}", head_sha=head_sha, status=ReviewStatus.queued)
            session.add(review)
            await session.flush()
        review_id = review.id
        session.add(OutboxEvent(event_type="review.requested", aggregate_id=str(review.id), payload={"review_id": str(review.id), "head_sha": head_sha}))
    await session.commit()
    if review_id is not None:
        try:
            dispatch_outbox.delay()
        except (OperationalError, OSError):
            logger.warning("outbox_dispatch_deferred", extra={"review_id": str(review_id)})
    return {"status": "accepted"}
