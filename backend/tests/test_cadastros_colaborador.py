import pytest

pytestmark = pytest.mark.anyio


async def test_colaborador_with_valid_cargo(client, user_with_token):
    headers = {"Authorization": f"Bearer {user_with_token['token']}"}
    rc = await client.post("/api/v1/cadastros/cargo", json={"nome": "Operador"}, headers=headers)
    cargo_id = rc.json()["id"]
    r = await client.post(
        "/api/v1/cadastros/colaborador",
        json={"nome": "Maria", "cargo_id": cargo_id, "email": "maria@x.com"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["cargo_id"] == cargo_id


async def test_colaborador_with_unknown_cargo_returns_400(client, user_with_token):
    import uuid

    headers = {"Authorization": f"Bearer {user_with_token['token']}"}
    r = await client.post(
        "/api/v1/cadastros/colaborador",
        json={"nome": "Bob", "cargo_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert r.status_code == 400
    assert "cargo" in r.json()["detail"].lower()


async def test_colaborador_without_cargo_is_allowed(client, user_with_token):
    headers = {"Authorization": f"Bearer {user_with_token['token']}"}
    r = await client.post(
        "/api/v1/cadastros/colaborador", json={"nome": "Sem Cargo"}, headers=headers
    )
    assert r.status_code == 201, r.text
