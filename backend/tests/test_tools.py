from pathlib import Path

from app.analysis.tools import analyzer_names, parse_analyzer_output, run_analyzer


def test_language_aware_analyzer_selection() -> None:
    assert analyzer_names(["src/a.py", "web/app.tsx"]) == ["semgrep", "ruff", "eslint"]


def test_semgrep_output_is_normalized() -> None:
    findings = parse_analyzer_output("semgrep", {"results": [{"path": "a.py", "check_id": "x", "start": {"line": 3}, "extra": {"severity": "ERROR", "message": "unsafe"}}]})
    assert findings[0].tool == "semgrep"
    assert findings[0].line == 3
    assert findings[0].severity == "error"


def test_analyzer_rejects_path_traversal(tmp_path: Path) -> None:
    assert run_analyzer("ruff", tmp_path, ["../outside.py"]) == []
