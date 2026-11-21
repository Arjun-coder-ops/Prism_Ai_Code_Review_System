from __future__ import annotations

from dataclasses import dataclass

from app.analysis.static import CandidateFinding
from app.services.diff import DiffLine


@dataclass(frozen=True)
class VerifiedFinding:
    candidate: CandidateFinding
    evidence: dict[str, str]


def verify_candidate(candidate: CandidateFinding, lines: list[DiffLine]) -> VerifiedFinding | None:
    for line in lines:
        if line.path == candidate.path and line.line == candidate.line and line.kind == "added" and candidate.evidence.strip() == line.content.strip():
            return VerifiedFinding(candidate, {"line": line.content, "source": "unified_diff"})
    return None


def verify_candidates(candidates: list[CandidateFinding], lines: list[DiffLine]) -> list[VerifiedFinding]:
    return [verified for candidate in candidates if (verified := verify_candidate(candidate, lines)) is not None]
