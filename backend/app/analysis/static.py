from __future__ import annotations

from dataclasses import dataclass

from app.services.diff import DiffLine


@dataclass(frozen=True)
class CandidateFinding:
    path: str
    line: int
    severity: str
    category: str
    title: str
    explanation: str
    evidence: str


def candidates_from_diff(lines: list[DiffLine]) -> list[CandidateFinding]:
    candidates: list[CandidateFinding] = []
    for line in lines:
        if line.kind != "added" or line.line is None:
            continue
        if "eval(" in line.content:
            candidates.append(CandidateFinding(line.path, line.line, "high", "security", "Dynamic evaluation added", "The added code evaluates a runtime string, which can execute attacker-controlled input.", line.content))
        elif line.content.strip() == "except: pass":
            candidates.append(CandidateFinding(line.path, line.line, "medium", "reliability", "Exception is silently discarded", "The added bare handler hides failures and makes recovery or diagnosis difficult.", line.content))
    return candidates
