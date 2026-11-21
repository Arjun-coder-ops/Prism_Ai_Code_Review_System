from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import Finding, Repository, Review, ReviewStatus
from app.schemas import FindingOut, HealthOut, ReviewCreate, ReviewOut

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(status="ok", version="0.1.0")


@router.get("/readiness", response_model=HealthOut)
async def readiness(session: AsyncSession = Depends(get_session)) -> HealthOut:
    await session.execute(select(1))
    return HealthOut(status="ready", version="0.1.0")


@router.post("/reviews", response_model=ReviewOut, status_code=status.HTTP_202_ACCEPTED)
async def create_review(payload: ReviewCreate, session: AsyncSession = Depends(get_session)) -> Review:
    from app.services.github import parse_pull_request_url
    ref = parse_pull_request_url(str(payload.url))
    repo = await session.scalar(select(Repository).where(Repository.full_name == f"{ref.owner}/{ref.repo}"))
    if repo is None:
        repo = Repository(full_name=f"{ref.owner}/{ref.repo}")
        session.add(repo)
        await session.flush()
    existing = await session.scalar(select(Review).where(Review.repository_id == repo.id, Review.pr_number == ref.number, Review.status.in_([ReviewStatus.queued, ReviewStatus.analyzing])))
    if existing:
        return existing
    review = Review(repository_id=repo.id, pr_number=ref.number, url=str(payload.url), status=ReviewStatus.queued)
    session.add(review)
    await session.commit()
    await session.refresh(review)
    return review


@router.get("/reviews/{review_id}", response_model=ReviewOut)
async def get_review(review_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Review:
    review = await session.scalar(select(Review).where(Review.id == review_id))
    if review is None:
        from app.core.errors import PrismError
        raise PrismError("review_not_found", "Review does not exist.", 404)
    await session.refresh(review, ["findings"])
    return review


@router.get("/reviews/{review_id}/findings", response_model=list[FindingOut])
async def list_findings(review_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> list[Finding]:
    return list((await session.scalars(select(Finding).where(Finding.review_id == review_id).order_by(Finding.start_line))).all())
