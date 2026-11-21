from app.api import health


def test_health() -> None:
    coroutine = health()
    try:
        coroutine.send(None)
    except StopIteration as completed:
        response = completed.value
    assert response.status == "ok"
    assert response.version == "0.1.0"
