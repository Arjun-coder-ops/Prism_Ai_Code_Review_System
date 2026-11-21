import pytest
from app.core.errors import PrismError
from app.services.github import parse_pull_request_url


def test_parse_canonical_url() -> None:
    assert parse_pull_request_url("https://github.com/acme/widget/pull/42").number == 42


@pytest.mark.parametrize("url", ["http://github.com/a/b/pull/1", "https://evil.test/a/b/pull/1", "https://github.com/a/b/issues/1"])
def test_reject_unsafe_urls(url: str) -> None:
    with pytest.raises(PrismError):
        parse_pull_request_url(url)
