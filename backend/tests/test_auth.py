import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_tenant_creates_tenant_and_user(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Oficina ABC Ltda",
            "cnpj": "11222333000181",
            "admin_email": "admin@oficina-abc.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Carlos Admin",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_register_tenant_rejects_duplicate_cnpj(client: AsyncClient) -> None:
    payload = {
        "razao_social": "Empresa Y",
        "cnpj": "22333444000195",
        "admin_email": "admin@empresa-y.com",
        "admin_password": "SenhaForte123!",
        "admin_full_name": "Admin",
    }
    resp1 = await client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    payload["admin_email"] = "outro@empresa-y.com"
    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409


async def test_login_returns_tokens(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Login Test Corp",
            "cnpj": "33444555000178",
            "admin_email": "login-test@corp.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Login Admin",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "login-test@corp.com", "password": "SenhaForte123!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Wrong Pass Corp",
            "cnpj": "44555666000150",
            "admin_email": "wrong@corp.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Admin",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "wrong@corp.com", "password": "senha-errada"},
    )
    assert resp.status_code == 401


async def test_me_returns_current_user(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Me Test Corp",
            "cnpj": "55666777000133",
            "admin_email": "me@corp.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Me Admin",
        },
    )
    token = reg.json()["access_token"]
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@corp.com"


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_refresh_returns_new_tokens(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Refresh Test",
            "cnpj": "66777888000116",
            "admin_email": "refresh@test.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Refresh Admin",
        },
    )
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["refresh_token"] != refresh_token


async def test_logout_invalidates_refresh_token(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "razao_social": "Logout Test",
            "cnpj": "77888999000199",
            "admin_email": "logout@test.com",
            "admin_password": "SenhaForte123!",
            "admin_full_name": "Logout Admin",
        },
    )
    tokens = reg.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 204

    resp2 = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp2.status_code == 401
