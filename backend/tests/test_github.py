import pytest

from app.core.errors import PrismError
from app.services.github import PullRequestRef, fetch_repository_file, parse_pull_request_url


def test_parse_canonical_url() -> None:
    assert parse_pull_request_url("https://github.com/acme/widget/pull/42").number == 42


def test_repository_file_rejects_traversal_before_network() -> None:
    with pytest.raises(PrismError):
        fetch_repository_file(PullRequestRef("acme", "widget", 1), "../secret.py", "a" * 40).send(None)


@pytest.mark.parametrize("url", ["http://github.com/a/b/pull/1", "https://evil.test/a/b/pull/1", "https://github.com/a/b/issues/1", "https://github.com/a/b/pull/1?redirect=evil", "https://GitHub.com/a/b/pull/1"])
def test_reject_unsafe_urls(url: str) -> None:
    with pytest.raises(PrismError):
        parse_pull_request_url(url)


@pytest.mark.parametrize("url", ["https://github.com/a..b/repo/pull/1", "https://github.com/acme/re..po/pull/1", "https://github.com/acme/repo/pull/0", "https://github.com/acme/repo/pull/01", "https://github.com/acme/repo name/pull/1"])
def test_reject_invalid_repository_or_number(url: str) -> None:
    with pytest.raises(PrismError):
        parse_pull_request_url(url)
