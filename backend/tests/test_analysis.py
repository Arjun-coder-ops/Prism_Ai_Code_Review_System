from app.analysis.static import candidates_from_diff
from app.evaluations.runner import EvaluationCase, evaluate, locations
from app.intelligence.impact import infer_change_impact
from app.intelligence.test_gaps import recommend_test_gaps
from app.services.diff import parse_unified_diff
from app.verification.evidence import verify_candidates


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
    assert locations(candidates_from_diff(parse_unified_diff("@@ -1 +1,2 @@\n x\n+eval(x)", "a.py"))) == {("a.py", 2)}
