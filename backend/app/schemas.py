from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


class ReviewCreate(BaseModel):
    url: AnyHttpUrl

    @field_validator("url")
    @classmethod
    def canonical_github_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        from app.services.github import parse_pull_request_url
        parse_pull_request_url(str(value))
        return value


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    path: str
    start_line: int
    end_line: int
    severity: str
    category: str
    title: str
    explanation: str
    evidence: dict[str, Any]
    verification_state: str


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    url: str
    pr_number: int
    head_sha: str | None
    status: str
    error_message: str | None
    created_at: datetime
    findings: list[FindingOut] = Field(default_factory=list)
    changed_paths: list[str] = Field(default_factory=list)


class HealthOut(BaseModel):
    status: str
    version: str
