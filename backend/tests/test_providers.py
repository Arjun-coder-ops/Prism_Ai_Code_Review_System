import pytest

from app.ai.providers import (
    DisabledProvider,
    FallbackProvider,
    GeminiProvider,
    GroqProvider,
    ReviewContext,
    build_provider,
    parse_candidates,
)
from app.core.config import Settings
from app.core.errors import PrismError


def test_provider_candidates_require_complete_locations() -> None:
    candidates = parse_candidates([{"path": "a.py", "line": 4, "severity": "high", "category": "security", "title": "x", "explanation": "y", "evidence": "z"}, {"path": "a.py", "line": 0}])
    assert len(candidates) == 1
    assert candidates[0].line == 4


def test_private_ai_is_denied_by_default() -> None:
    coroutine = DisabledProvider(False).candidates(ReviewContext("private source", True))
    with pytest.raises(PrismError):
        coroutine.send(None)


def test_provider_selection_prefers_groq_with_gemini_fallback() -> None:
    provider = build_provider(Settings(groq_api_key="g", gemini_api_key="g2"))
    assert isinstance(provider, FallbackProvider)
    assert isinstance(provider.primary, GroqProvider)
    assert isinstance(provider.fallback, GeminiProvider)


def test_fallback_provider_uses_secondary_on_primary_failure() -> None:
    class Failing:
        provider_name = "primary"
        last_usage = None

        async def candidates(self, context: ReviewContext) -> list[dict[str, object]]:
            raise PrismError("provider_down", "down", 503)

    class Working:
        provider_name = "fallback"
        last_usage = None

        async def candidates(self, context: ReviewContext) -> list[dict[str, object]]:
            return [{"path": "a.py", "line": 1, "severity": "low", "category": "style", "title": "t", "explanation": "e", "evidence": "x"}]

    coroutine = FallbackProvider(Failing(), Working()).candidates(ReviewContext("diff", False))
    with pytest.raises(StopIteration) as stopped:
        coroutine.send(None)
    assert stopped.value.value[0]["path"] == "a.py"
