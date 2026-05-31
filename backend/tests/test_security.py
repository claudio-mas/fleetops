import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_mfa_challenge_token,
    create_refresh_token,
    decode_access_token,
    hash_token,
)


def test_create_and_decode_access_token() -> None:
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    token = create_access_token(user_id, tenant_id)

    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["type"] == "access"


def test_decode_expired_token_raises() -> None:
    payload = {
        "sub": str(uuid.uuid4()),
        "tenant_id": str(uuid.uuid4()),
        "type": "access",
        "exp": datetime.now(UTC) - timedelta(seconds=1),
    }
    token = pyjwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_access_token(token)


def test_decode_access_token_rejects_mfa_challenge_token() -> None:
    """An MFA challenge token must NOT be usable as an access token."""
    challenge = create_mfa_challenge_token(uuid.uuid4(), uuid.uuid4())

    with pytest.raises(pyjwt.InvalidTokenError):
        decode_access_token(challenge)


def test_hash_token_is_deterministic() -> None:
    token = create_refresh_token()
    assert hash_token(token) == hash_token(token)


def test_hash_token_is_64_hex_chars() -> None:
    token = create_refresh_token()
    hashed = hash_token(token)
    assert len(hashed) == 64
    assert all(c in "0123456789abcdef" for c in hashed)
