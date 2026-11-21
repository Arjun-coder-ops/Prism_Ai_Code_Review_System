from __future__ import annotations

import hashlib
import hmac
import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import PrismError

_requests: dict[str, deque[float]] = defaultdict(deque)


async def require_api_key(request: Request) -> None:
    """Enforce the configured operator key while keeping local development opt-in."""
    expected = get_settings().api_key
    if expected is None:
        return
    provided = request.headers.get("x-prism-api-key", "")
    if not hmac.compare_digest(hashlib.sha256(provided.encode()).digest(), hashlib.sha256(expected.encode()).digest()):
        raise PrismError("authentication_required", "A valid PRISM API key is required.", 401)


async def enforce_rate_limit(request: Request) -> None:
    """Bound expensive intake operations per client IP in a single process."""
    limit = max(1, get_settings().rate_limit_per_minute)
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = _requests[client]
    while bucket and now - bucket[0] >= 60:
        bucket.popleft()
    if len(bucket) >= limit:
        raise PrismError("rate_limited", "Too many requests; retry later.", 429)
    bucket.append(now)


def ensure_repository_access(full_name: str) -> None:
    allowed = get_settings().authorized_repository_list
    if allowed and full_name.lower() not in allowed:
        raise PrismError("repository_forbidden", "The configured principal cannot access this repository.", 403)
