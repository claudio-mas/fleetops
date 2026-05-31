import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.mfa_service import MFAService

pytestmark = pytest.mark.asyncio


async def _enable_mfa(db: AsyncSession, user_id) -> str:
    """Enable MFA for a user and return the TOTP secret."""
    secret, _ = await MFAService.setup_mfa(db, user_id)
    totp = MFAService.get_totp(secret)
    await MFAService.confirm_mfa(db, user_id, secret, totp.now())
    return secret


async def test_login_with_mfa_enabled_returns_challenge(
    client: AsyncClient, db: AsyncSession, sample_user
) -> None:
    await _enable_mfa(db, sample_user.id)

    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": sample_user.email, "password": "SenhaForte123!"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mfa_required"] is True
    assert body["mfa_challenge_token"]
    assert body.get("access_token") is None


async def test_mfa_login_completes_with_valid_token(
    client: AsyncClient, db: AsyncSession, sample_user
) -> None:
    secret = await _enable_mfa(db, sample_user.id)

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": sample_user.email, "password": "SenhaForte123!"},
    )
    challenge = login.json()["mfa_challenge_token"]

    code = MFAService.get_totp(secret).now()
    resp = await client.post(
        "/api/v1/mfa/login",
        json={"token": code},
        headers={"X-MFA-Challenge": challenge},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_mfa_login_rejects_invalid_totp(
    client: AsyncClient, db: AsyncSession, sample_user
) -> None:
    await _enable_mfa(db, sample_user.id)

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": sample_user.email, "password": "SenhaForte123!"},
    )
    challenge = login.json()["mfa_challenge_token"]

    resp = await client.post(
        "/api/v1/mfa/login",
        json={"token": "000000"},
        headers={"X-MFA-Challenge": challenge},
    )

    assert resp.status_code == 401


async def test_mfa_login_requires_challenge_header(
    client: AsyncClient, db: AsyncSession, sample_user
) -> None:
    secret = await _enable_mfa(db, sample_user.id)
    code = MFAService.get_totp(secret).now()

    resp = await client.post("/api/v1/mfa/login", json={"token": code})

    assert resp.status_code == 400


async def test_mfa_login_rejects_invalid_challenge_token(
    client: AsyncClient, db: AsyncSession, sample_user
) -> None:
    secret = await _enable_mfa(db, sample_user.id)
    code = MFAService.get_totp(secret).now()

    resp = await client.post(
        "/api/v1/mfa/login",
        json={"token": code},
        headers={"X-MFA-Challenge": "not-a-valid-jwt"},
    )

    assert resp.status_code == 401


async def test_challenge_token_cannot_access_protected_route(
    client: AsyncClient, db: AsyncSession, sample_user
) -> None:
    """The challenge token issued at /login must not authenticate protected routes."""
    await _enable_mfa(db, sample_user.id)

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": sample_user.email, "password": "SenhaForte123!"},
    )
    challenge = login.json()["mfa_challenge_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {challenge}"},
    )

    assert resp.status_code == 401


async def test_mfa_login_rejects_replayed_totp(
    client: AsyncClient, db: AsyncSession, sample_user
) -> None:
    """A TOTP code already used to complete an MFA login cannot be replayed."""
    secret = await _enable_mfa(db, sample_user.id)

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": sample_user.email, "password": "SenhaForte123!"},
    )
    challenge = login.json()["mfa_challenge_token"]

    code = MFAService.get_totp(secret).now()
    first = await client.post(
        "/api/v1/mfa/login",
        json={"token": code},
        headers={"X-MFA-Challenge": challenge},
    )
    assert first.status_code == 200, first.text

    replay = await client.post(
        "/api/v1/mfa/login",
        json={"token": code},
        headers={"X-MFA-Challenge": challenge},
    )
    assert replay.status_code == 401


async def test_login_without_mfa_still_returns_tokens(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "No MFA Corp",
            "cnpj": "88999000000172",
            "admin_email": "nomfa@corp.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "No MFA Admin",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "nomfa@corp.com", "password": "SenhaForte123!"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
