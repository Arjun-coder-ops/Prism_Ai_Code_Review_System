from __future__ import annotations

import json
from pathlib import Path

from app.evaluations.runner import EvaluationCase, evaluate


def test_versioned_review_dataset_is_executable() -> None:
    dataset_path = Path(__file__).parents[2] / "evals" / "datasets" / "review-v1.json"
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    assert payload["version"] == "review-v1"
    cases = [
        EvaluationCase(
            case_id=item["case_id"],
            expected={tuple(location) for location in item["expected"]},
            predicted={tuple(location) for location in item["predicted"]},
        )
        for item in payload["cases"]
    ]
    result = evaluate(cases)
    assert result.true_positives == 2
    assert result.false_positives == 1
    assert result.false_negatives == 0
    assert result.precision == 2 / 3
    assert result.recall == 1.0
