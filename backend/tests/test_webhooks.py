import hashlib
import hmac

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from app.core.errors import PrismError
from app.github.auth import build_app_jwt
from app.github.webhooks import verify_signature


def test_webhook_signature_is_constant_time_verified() -> None:
    payload = b'{"action":"opened"}'
    secret = "test-secret"
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    verify_signature(payload, f"sha256={digest}", secret)
    with pytest.raises(PrismError):
        verify_signature(payload, "sha256=bad", secret)


def test_app_jwt_contains_short_lived_claims() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    public_pem = private_key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    claims = jwt.decode(build_app_jwt("123", pem.decode(), now=1_700_000_000), public_pem, algorithms=["RS256"], options={"verify_exp": False})
    assert claims["iss"] == "123"
    assert claims["exp"] - claims["iat"] == 600
