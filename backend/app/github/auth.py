from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import httpx
import jwt

from app.core.errors import PrismError


def build_app_jwt(app_id: str, private_key: str, now: int | None = None) -> str:
    issued_at = int(time.time()) if now is None else now
    return str(jwt.encode({"iat": issued_at - 60, "exp": issued_at + 540, "iss": app_id}, private_key, algorithm="RS256"))


def load_private_key(path: str) -> str:
    key_path = Path(path)
    if not key_path.is_file():
        raise PrismError("github_key_missing", "GitHub App private key file is unavailable.", 500)
    return key_path.read_text(encoding="utf-8")


async def fetch_installation_token(app_id: str, private_key: str, installation_id: int) -> str:
    token = build_app_jwt(app_id, private_key)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0), follow_redirects=False) as client:
        response = await client.post(url, headers=headers)
    if response.status_code >= 400:
        raise PrismError("github_installation_token_failed", "GitHub rejected the installation-token request.", 502)
    payload: dict[str, Any] = response.json()
    value = payload.get("token")
    if not isinstance(value, str) or not value:
        raise PrismError("github_invalid_token_response", "GitHub returned no installation token.", 502)
    return value
