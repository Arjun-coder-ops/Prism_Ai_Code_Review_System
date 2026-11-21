from __future__ import annotations

import hashlib
import hmac

from app.core.errors import PrismError


def verify_signature(payload: bytes, signature: str | None, secret: str | None) -> None:
    if not secret or not signature or not signature.startswith("sha256="):
        raise PrismError("invalid_webhook_signature", "Webhook signature is missing or malformed.", 401)
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PrismError("invalid_webhook_signature", "Webhook signature did not match.", 401)


def payload_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
