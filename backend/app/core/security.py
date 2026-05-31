from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt

from app.core.config import settings


def create_access_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(seconds=settings.jwt_access_token_expire_seconds),
        "iat": datetime.now(UTC),
    }
    return pyjwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, object]:
    return pyjwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"verify_exp": True},
    )


def create_mfa_challenge_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "mfa_challenge",
        "exp": datetime.now(UTC) + timedelta(seconds=settings.jwt_mfa_challenge_expire_seconds),
        "iat": datetime.now(UTC),
    }
    return pyjwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_mfa_challenge_token(token: str) -> dict[str, object]:
    payload = pyjwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"verify_exp": True},
    )
    if payload.get("type") != "mfa_challenge":
        raise pyjwt.InvalidTokenError("not an mfa challenge token")
    return payload


def create_refresh_token() -> str:
    return str(uuid.uuid4())


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
