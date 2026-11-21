from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class TestGap:
    source_path: str
    suggested_path: str
    reason: str


def recommend_test_gaps(changed_paths: list[str], repository_paths: set[str]) -> list[TestGap]:
    gaps: list[TestGap] = []
    for raw_path in changed_paths:
        path = PurePosixPath(raw_path)
        if path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"} or "test" in path.name.lower() or "spec" in path.name.lower():
            continue
        stem = path.stem
        if path.suffix == ".py":
            suggestion = f"tests/test_{stem}.py"
        else:
            suggestion = f"{path.parent}/__tests__/{stem}.test{path.suffix}"
        if suggestion not in repository_paths:
            gaps.append(TestGap(raw_path, suggestion, "changed production code has no matching test file"))
    return gaps
