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
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.errors import PrismError
from app.core.metrics import review_requests
from app.core.security import enforce_rate_limit, ensure_repository_access, require_api_key
from app.db.session import get_session
from app.github.auth import (
    fetch_installation_repositories,
    fetch_installation_token,
    load_private_key,
)
from app.github.webhooks import payload_hash, verify_signature
from app.intelligence.impact import infer_change_impact
from app.intelligence.test_gaps import recommend_test_gaps
from app.models import (
    Finding,
    GithubInstallation,
    OutboxEvent,
    Repository,
    Review,
    ReviewStatus,
    WebhookDelivery,
)
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


@router.post("/reviews", response_model=ReviewOut, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)])
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


@router.get("/reviews/{review_id}", response_model=ReviewOut, dependencies=[Depends(require_api_key)])
async def get_review(review_id: uuid.UUID, session: SessionDep) -> Review:
    review = await session.scalar(select(Review).options(selectinload(Review.repository)).where(Review.id == review_id))
    if review is None:
        from app.core.errors import PrismError
        raise PrismError("review_not_found", "Review does not exist.", 404)
    ensure_repository_access(review.repository.full_name)
    await session.refresh(review, ["findings"])
    return review


@router.get("/reviews/{review_id}/findings", response_model=list[FindingOut], dependencies=[Depends(require_api_key)])
async def list_findings(review_id: uuid.UUID, session: SessionDep) -> list[Finding]:
    review = await session.scalar(select(Review).options(selectinload(Review.repository)).where(Review.id == review_id))
    if review is None:
        raise PrismError("review_not_found", "Review does not exist.", 404)
    ensure_repository_access(review.repository.full_name)
    return list((await session.scalars(select(Finding).where(Finding.review_id == review_id).order_by(Finding.start_line))).all())


@router.get("/reviews/{review_id}/impact", dependencies=[Depends(require_api_key)])
async def review_impact(review_id: uuid.UUID, session: SessionDep) -> list[dict[str, object]]:
    review = await session.scalar(select(Review).options(selectinload(Review.repository)).where(Review.id == review_id))
    if review is None:
        raise PrismError("review_not_found", "Review does not exist.", 404)
    ensure_repository_access(review.repository.full_name)
    return [{"component": item.component, "reason": item.reason, "confidence": item.confidence} for item in infer_change_impact(review.changed_paths)]


@router.get("/reviews/{review_id}/test-gaps", dependencies=[Depends(require_api_key)])
async def review_test_gaps(review_id: uuid.UUID, session: SessionDep) -> list[dict[str, str]]:
    review = await session.scalar(select(Review).options(selectinload(Review.repository)).where(Review.id == review_id))
    if review is None:
        raise PrismError("review_not_found", "Review does not exist.", 404)
    ensure_repository_access(review.repository.full_name)
    gaps = recommend_test_gaps(review.changed_paths, set(review.test_paths))
    return [{"source_path": gap.source_path, "suggested_path": gap.suggested_path, "reason": gap.reason} for gap in gaps]


@router.post("/webhooks/github", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(enforce_rate_limit)])
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
    installation_data = payload.get("installation") or {}
    installation_id = installation_data.get("id") if isinstance(installation_data, dict) else None
    if event_name == "installation" and isinstance(installation_id, int):
        account = installation_data.get("account") or {}
        login = account.get("login") if isinstance(account, dict) else None
        if not isinstance(login, str) or not login:
            raise PrismError("invalid_installation_event", "Installation account information is required.", 400)
        installation = await session.scalar(select(GithubInstallation).where(GithubInstallation.installation_id == installation_id))
        if installation is None:
            installation = GithubInstallation(installation_id=installation_id, account_login=login)
            session.add(installation)
        action = payload.get("action")
        installation.account_login = login
        installation.suspended_at = datetime.now(UTC) if action in {"suspend", "deleted"} else None
        if action in {"suspend", "deleted"}:
            await session.execute(update(Repository).where(Repository.installation_id == installation.id).values(installation_id=None))
        settings = get_settings()
        if action in {"created", "unsuspend"} and settings.github_app_id and settings.github_private_key_path:
            token = await fetch_installation_token(settings.github_app_id, load_private_key(settings.github_private_key_path), installation_id)
            for item in await fetch_installation_repositories(token):
                full_name = item.get("full_name")
                if not isinstance(full_name, str):
                    continue
                repo = await session.scalar(select(Repository).where(Repository.full_name == full_name))
                if repo is None:
                    repo = Repository(full_name=full_name)
                    session.add(repo)
                repo.github_id = item.get("id") if isinstance(item.get("id"), int) else repo.github_id
                repo.is_private = bool(item.get("private"))
                repo.installation_id = installation.id
        await session.commit()
        return {"status": "installation_synced"}
    if event_name == "installation_repositories" and isinstance(installation_id, int):
        installation = await session.scalar(select(GithubInstallation).where(GithubInstallation.installation_id == installation_id))
        if installation is None or installation.suspended_at is not None:
            raise PrismError("installation_not_authorized", "The GitHub installation is not authorized.", 403)
        for item in payload.get("repositories_added", []):
            if not isinstance(item, dict) or not isinstance(item.get("full_name"), str):
                continue
            repo = await session.scalar(select(Repository).where(Repository.full_name == item["full_name"]))
            if repo is None:
                repo = Repository(full_name=item["full_name"])
                session.add(repo)
            repo.github_id = item.get("id") if isinstance(item.get("id"), int) else repo.github_id
            repo.is_private = bool(item.get("private"))
            repo.installation_id = installation.id
        for item in payload.get("repositories_removed", []):
            if isinstance(item, dict) and isinstance(item.get("full_name"), str):
                repo = await session.scalar(select(Repository).where(Repository.full_name == item["full_name"], Repository.installation_id == installation.id))
                if repo is not None:
                    repo.installation_id = None
        await session.commit()
        return {"status": "repositories_synced"}
    if event_name == "pull_request" and payload.get("action") in {"opened", "reopened", "synchronize"}:
        repository_data = payload.get("repository") or {}
        pull_request = payload.get("pull_request") or {}
        full_name = repository_data.get("full_name")
        number = payload.get("number")
        head_sha = (pull_request.get("head") or {}).get("sha")
        if not isinstance(full_name, str) or not isinstance(number, int) or not isinstance(head_sha, str) or not isinstance(installation_id, int):
            raise PrismError("invalid_pull_request_event", "Webhook lacks repository, PR number, or head SHA.", 400)
        installation = await session.scalar(select(GithubInstallation).where(GithubInstallation.installation_id == installation_id))
        if installation is None or installation.suspended_at is not None:
            raise PrismError("installation_not_authorized", "The GitHub installation is not authorized.", 403)
        repo = await session.scalar(select(Repository).where(Repository.full_name == full_name))
        if repo is None:
            repo = Repository(full_name=full_name, github_id=repository_data.get("id"), is_private=bool(repository_data.get("private")), installation_id=installation.id)
            session.add(repo)
            await session.flush()
        elif repo.installation_id not in {None, installation.id}:
            raise PrismError("repository_not_authorized", "The repository is not authorized for this installation.", 403)
        else:
            repo.installation_id = installation.id
            repo.is_private = bool(repository_data.get("private"))
        review = await session.scalar(select(Review).where(Review.repository_id == repo.id, Review.pr_number == number, Review.head_sha == head_sha))
        if review is None:
            review = Review(repository_id=repo.id, pr_number=number, url=f"https://github.com/{full_name}/pull/{number}", head_sha=head_sha, status=ReviewStatus.queued)
            session.add(review)
            await session.flush()
        review_id = review.id
        existing_outbox = list((await session.scalars(select(OutboxEvent).where(OutboxEvent.event_type == "review.requested", OutboxEvent.aggregate_id == str(review.id)))).all())
        if not any(event.payload.get("head_sha") == head_sha for event in existing_outbox):
            session.add(OutboxEvent(event_type="review.requested", aggregate_id=str(review.id), payload={"review_id": str(review.id), "head_sha": head_sha}))
    await session.commit()
    if review_id is not None:
        try:
            dispatch_outbox.delay()
        except (OperationalError, OSError):
            logger.warning("outbox_dispatch_deferred", extra={"review_id": str(review_id)})
    return {"status": "accepted"}
