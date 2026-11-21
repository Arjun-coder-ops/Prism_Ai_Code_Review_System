import pytest

from app.ai.providers import DisabledProvider, ReviewContext, parse_candidates
from app.core.errors import PrismError


def test_provider_candidates_require_complete_locations() -> None:
    candidates = parse_candidates([{"path": "a.py", "line": 4, "severity": "high", "category": "security", "title": "x", "explanation": "y", "evidence": "z"}, {"path": "a.py", "line": 0}])
    assert len(candidates) == 1
    assert candidates[0].line == 4


def test_private_ai_is_denied_by_default() -> None:
    coroutine = DisabledProvider(False).candidates(ReviewContext("private source", True))
    with pytest.raises(PrismError):
        coroutine.send(None)
