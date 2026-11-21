from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.errors import PrismError


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int


def ensure_head_sha_stable(initial_sha: str, latest_sha: str) -> None:
    if initial_sha != latest_sha:
        raise PrismError("stale_review", "The pull request changed while it was being analyzed; retry the review.", 409)


def parse_pull_request_url(url: str) -> PullRequestRef:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment or parsed.params:
        raise PrismError("invalid_github_url", "Only canonical https://github.com pull-request URLs are accepted.")
    match = re.fullmatch(r"/([^/]+)/([^/]+)/pull/([1-9][0-9]*)/?", parsed.path)
    if not match:
        raise PrismError("invalid_pull_request_url", "URL must point to /owner/repository/pull/number.")
    owner, repo = match.group(1), match.group(2)
    if ".." in owner or ".." in repo or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", owner):
        raise PrismError("invalid_repository", "Owner is not a valid GitHub account name.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", repo) or repo.endswith("."):
        raise PrismError("invalid_repository", "Repository is not a valid GitHub repository name.")
    return PullRequestRef(owner, repo, int(match.group(3)))


def github_api_url(ref: PullRequestRef, resource: str = "") -> str:
    suffix = f"/{resource.lstrip('/')}" if resource else ""
    return f"https://api.github.com/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}{suffix}"


async def fetch_pull_request(ref: PullRequestRef, token: str | None = None) -> dict[str, Any]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0), follow_redirects=False) as client:
        response = await client.get(github_api_url(ref), headers=headers)
    if response.status_code == 404:
        raise PrismError("github_not_found", "The pull request was not found or is not accessible.", 404)
    if response.status_code == 429:
        raise PrismError("github_rate_limited", "GitHub rate limit reached; retry later.", 503)
    if response.status_code >= 500:
        raise PrismError("github_unavailable", "GitHub is temporarily unavailable.", 503)
    if response.status_code >= 400:
        raise PrismError("github_request_failed", "GitHub rejected the pull-request request.", 502)
    payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("head", {}).get("sha"), str):
        raise PrismError("github_invalid_response", "GitHub returned incomplete pull-request metadata.", 502)
    return payload


async def fetch_pull_request_files(ref: PullRequestRef, token: str | None = None) -> list[dict[str, Any]]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    files: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0), follow_redirects=False) as client:
        for page in range(1, 11):
            response = await client.get(f"{github_api_url(ref, 'files')}?per_page=100&page={page}", headers=headers)
            if response.status_code == 429 or response.status_code >= 500:
                raise PrismError("github_files_unavailable", "GitHub files are temporarily unavailable.", 503)
            if response.status_code >= 400:
                raise PrismError("github_files_failed", "GitHub did not return the pull-request files.", 502)
            page_files = response.json()
            if not isinstance(page_files, list):
                raise PrismError("github_invalid_files", "GitHub returned an invalid file list.", 502)
            files.extend(item for item in page_files if isinstance(item, dict))
            if len(page_files) < 100:
                break
    return files
