from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnalyzerFinding:
    tool: str
    path: str
    line: int
    severity: str
    rule_id: str
    message: str


_COMMANDS: dict[str, tuple[str, ...]] = {
    "semgrep": ("semgrep", "--json", "--config", "auto", "--no-git-ignore"),
    "ruff": ("ruff", "check", "--output-format", "json"),
    "eslint": ("eslint", "--format", "json", "--no-error-on-unmatched-pattern"),
}


def analyzer_names(paths: list[str]) -> list[str]:
    names = ["semgrep"] if paths else []
    if any(path.endswith(".py") for path in paths):
        names.append("ruff")
    if any(path.endswith((".js", ".jsx", ".ts", ".tsx")) for path in paths):
        names.append("eslint")
    return names


def run_analyzer(tool: str, root: Path, paths: list[str], timeout_seconds: float = 10.0, max_output_bytes: int = 1_000_000) -> list[AnalyzerFinding]:
    """Run a parser-only analyzer in an isolated temporary root.

    Callers must provide a temporary directory containing only sanitized snapshots of
    changed files. Commands are argument arrays, never shell strings, and output is bounded.
    """
    command = _COMMANDS.get(tool)
    if command is None or shutil.which(command[0]) is None:
        return []
    root = root.resolve()
    safe_paths: list[str] = []
    for raw_path in paths:
        candidate = (root / raw_path).resolve()
        if root not in candidate.parents and candidate != root:
            continue
        safe_paths.append(str(candidate.relative_to(root)))
    if not safe_paths:
        return []
    env = {"PATH": os.environ.get("PATH", ""), "NO_COLOR": "1", "PYTHONSAFEPATH": "1"}
    try:
        completed = subprocess.run([*command, *safe_paths], cwd=root, env=env, capture_output=True, text=True, timeout=timeout_seconds, check=False, shell=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    output = completed.stdout[:max_output_bytes]
    try:
        payload = json.loads(output) if output else []
    except json.JSONDecodeError:
        return []
    return parse_analyzer_output(tool, payload)


def parse_analyzer_output(tool: str, payload: object) -> list[AnalyzerFinding]:
    findings: list[AnalyzerFinding] = []
    if tool == "semgrep" and isinstance(payload, dict):
        for item in payload.get("results", []):
            if not isinstance(item, dict):
                continue
            start = item.get("start") or {}
            findings.append(AnalyzerFinding("semgrep", str(item.get("path", "")), int(start.get("line", 0)), str(item.get("extra", {}).get("severity", "warning")).lower(), str(item.get("check_id", "")), str(item.get("extra", {}).get("message", ""))))
    elif tool == "ruff" and isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            findings.append(AnalyzerFinding("ruff", str(item.get("filename", "")), int(item.get("location", {}).get("row", 0)), str(item.get("message", "warning")).lower(), str(item.get("code", "")), str(item.get("message", ""))))
    elif tool == "eslint" and isinstance(payload, list):
        for file_result in payload:
            if not isinstance(file_result, dict):
                continue
            for item in file_result.get("messages", []):
                if isinstance(item, dict):
                    findings.append(AnalyzerFinding("eslint", str(file_result.get("filePath", "")), int(item.get("line", 0)), str(item.get("severity", "warning")), str(item.get("ruleId", "")), str(item.get("message", ""))))
    return [finding for finding in findings if finding.path and finding.line > 0]
