from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class DiffLine:
    path: str
    line: int | None
    kind: str
    content: str


_HUNK = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_unified_diff(patch: str, path: str) -> list[DiffLine]:
    lines: list[DiffLine] = []
    new_line: int | None = None
    for raw in patch.splitlines():
        hunk = _HUNK.match(raw)
        if hunk:
            new_line = int(hunk.group(3))
            continue
        if new_line is None or raw.startswith("\\ No newline"):
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            lines.append(DiffLine(path, new_line, "added", raw[1:]))
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            lines.append(DiffLine(path, None, "deleted", raw[1:]))
        else:
            lines.append(DiffLine(path, new_line, "context", raw.removeprefix(" ")))
            new_line += 1
    return lines
