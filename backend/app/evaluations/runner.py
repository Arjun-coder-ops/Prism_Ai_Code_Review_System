from __future__ import annotations

from dataclasses import dataclass

from app.analysis.static import CandidateFinding


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    expected: set[tuple[str, int]]
    predicted: set[tuple[str, int]]


@dataclass(frozen=True)
class EvaluationResult:
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float


def evaluate(cases: list[EvaluationCase]) -> EvaluationResult:
    tp = sum(len(case.expected & case.predicted) for case in cases)
    fp = sum(len(case.predicted - case.expected) for case in cases)
    fn = sum(len(case.expected - case.predicted) for case in cases)
    return EvaluationResult(tp, fp, fn, tp / (tp + fp) if tp + fp else 1.0, tp / (tp + fn) if tp + fn else 1.0)


def locations(findings: list[CandidateFinding]) -> set[tuple[str, int]]:
    return {(finding.path, finding.line) for finding in findings}
