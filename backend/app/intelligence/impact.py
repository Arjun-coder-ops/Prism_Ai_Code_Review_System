from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class ImpactItem:
    component: str
    reason: str
    confidence: float


def infer_change_impact(paths: list[str]) -> list[ImpactItem]:
    items: list[ImpactItem] = []
    seen: set[str] = set()
    for raw_path in paths:
        path = PurePosixPath(raw_path)
        component = path.parts[0] if path.parts else "root"
        if component in seen:
            continue
        seen.add(component)
        reason = "changed files in component"
        if path.name in {"Dockerfile", "compose.yaml"}:
            reason = "deployment configuration changed"
        elif path.suffix in {".sql", ".py"} and "migration" in path.parts:
            reason = "database migration changed"
        items.append(ImpactItem(component, reason, 0.8 if reason != "changed files in component" else 0.6))
    return items
