from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.errors import PrismError


@dataclass(frozen=True)
class ReviewContext:
    diff: str
    is_private: bool


class ReviewProvider(Protocol):
    async def candidates(self, context: ReviewContext) -> list[dict[str, object]]: ...


class DisabledProvider:
    def __init__(self, allow_private_ai: bool) -> None:
        self.allow_private_ai = allow_private_ai

    async def candidates(self, context: ReviewContext) -> list[dict[str, object]]:
        if context.is_private and not self.allow_private_ai:
            raise PrismError("private_ai_disabled", "Private repository source is not authorized for AI analysis.", 403)
        return []
