from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from app.core.errors import PrismError


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int


def parse_pull_request_url(url: str) -> PullRequestRef:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        raise PrismError("invalid_github_url", "Only canonical https://github.com pull-request URLs are accepted.")
    match = re.fullmatch(r"/([^/]+)/([^/]+)/pull/(0|[1-9][0-9]*)/?", parsed.path)
    if not match:
        raise PrismError("invalid_pull_request_url", "URL must point to /owner/repository/pull/number.")
    return PullRequestRef(match.group(1), match.group(2), int(match.group(3)))


def github_api_url(ref: PullRequestRef, resource: str = "") -> str:
    suffix = f"/{resource.lstrip('/')}" if resource else ""
    return f"https://api.github.com/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}{suffix}"
