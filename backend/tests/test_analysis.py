import pytest

from app.analysis.static import CandidateFinding, candidates_from_diff
from app.evaluations.runner import EvaluationCase, evaluate, locations
from app.intelligence.impact import infer_change_impact
from app.intelligence.test_gaps import recommend_test_gaps
from app.services.diff import DiffLine, parse_unified_diff
from app.services.github import ensure_head_sha_stable
from app.verification.evidence import verify_candidate, verify_candidates


def test_candidates_are_evidence_verified() -> None:
    lines = parse_unified_diff("@@ -1 +1,2 @@\n old\n+eval(user_input)", "app.py")
    candidates = candidates_from_diff(lines)
    verified = verify_candidates(candidates, lines)
    assert len(verified) == 1
    assert verified[0].evidence["source"] == "unified_diff"


def test_unverified_location_is_abstained() -> None:
    lines = parse_unified_diff("@@ -1 +1,2 @@\n old\n+safe", "app.py")
    assert verify_candidates(candidates_from_diff(lines), lines) == []


def test_impact_and_test_gap_helpers_are_deterministic() -> None:
    assert infer_change_impact(["backend/api.py", "backend/models.py"])[0].component == "backend"
    gaps = recommend_test_gaps(["src/widget.ts"], {"src/__tests__/other.test.ts"})
    assert gaps[0].suggested_path == "src/__tests__/widget.test.ts"


def test_evaluation_reports_precision_and_recall() -> None:
    result = evaluate([EvaluationCase("one", {("a.py", 2)}, {("a.py", 2), ("b.py", 4)})])
    assert result.true_positives == 1
    assert result.precision == 0.5
    assert result.recall == 1.0


def test_evidence_requires_the_full_changed_line() -> None:
    lines = [DiffLine("src/a.py", 4, "added", "safe_eval(value)")]
    candidate = CandidateFinding("src/a.py", 4, "high", "security", "title", "explanation", "eval(")
    assert verify_candidate(candidate, lines) is None


def test_high_risk_finding_requires_an_independent_signal() -> None:
    lines = [DiffLine("src/a.py", 4, "added", "value = user_input")]
    candidate = CandidateFinding("src/a.py", 4, "high", "security", "injection", "unsafe", "value = user_input")
    assert verify_candidate(candidate, lines) is None


def test_stale_head_sha_is_rejected() -> None:
    ensure_head_sha_stable("a" * 40, "a" * 40)
    from app.core.errors import PrismError

    with pytest.raises(PrismError, match="changed while"):
        ensure_head_sha_stable("a" * 40, "b" * 40)
    assert locations(candidates_from_diff(parse_unified_diff("@@ -1 +1,2 @@\n x\n+eval(x)", "a.py"))) == {("a.py", 2)}
