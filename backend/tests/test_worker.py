from app.workers import celery_app as worker_module


def test_enqueue_review_delegates_to_celery(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(worker_module.process_review, "delay", lambda review_id: calls.append(review_id))
    assert worker_module.enqueue_review("review-1") is True
    assert calls == ["review-1"]


def test_enqueue_review_reports_broker_failure(monkeypatch) -> None:
    from kombu.exceptions import OperationalError

    def fail(_: str) -> None:
        raise OperationalError("redis unavailable")

    monkeypatch.setattr(worker_module.process_review, "delay", fail)
    assert worker_module.enqueue_review("review-1") is False
