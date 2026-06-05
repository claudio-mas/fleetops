import pytest

pytestmark = pytest.mark.asyncio


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_create_list_get_update_delete_centro_custo(client, user_with_token):
    token = user_with_token["token"]

    r = await client.post(
        "/api/v1/cadastros/centro-custo",
        json={"nome": "Frota Pesada", "responsavel": "João"},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["nome"] == "Frota Pesada"
    assert created["version"] == 1
    obj_id = created["id"]

    r = await client.get("/api/v1/cadastros/centro-custo", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == obj_id

    r = await client.get("/api/v1/cadastros/centro-custo?search=inexistente", headers=_auth(token))
    assert r.json()["total"] == 0

    r = await client.get(f"/api/v1/cadastros/centro-custo/{obj_id}", headers=_auth(token))
    assert r.status_code == 200

    r = await client.put(
        f"/api/v1/cadastros/centro-custo/{obj_id}",
        json={"nome": "Frota Leve", "responsavel": None, "observacoes": None, "version": 1},
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["version"] == 2

    r = await client.put(
        f"/api/v1/cadastros/centro-custo/{obj_id}",
        json={"nome": "X", "responsavel": None, "observacoes": None, "version": 1},
        headers=_auth(token),
    )
    assert r.status_code == 409

    r = await client.delete(f"/api/v1/cadastros/centro-custo/{obj_id}", headers=_auth(token))
    assert r.status_code == 204

    r = await client.get("/api/v1/cadastros/centro-custo", headers=_auth(token))
    assert r.json()["total"] == 0


async def test_requires_authentication(client):
    r = await client.get("/api/v1/cadastros/centro-custo")
    assert r.status_code == 401


async def test_create_duplicate_nome_returns_409(client, user_with_token):
    token = user_with_token["token"]
    payload = {"nome": "Centro Único"}
    r1 = await client.post("/api/v1/cadastros/centro-custo", json=payload, headers=_auth(token))
    assert r1.status_code == 201, r1.text
    r2 = await client.post("/api/v1/cadastros/centro-custo", json=payload, headers=_auth(token))
    assert r2.status_code == 409, r2.text


async def test_update_to_duplicate_nome_returns_409(client, user_with_token):
    token = user_with_token["token"]
    a = await client.post(
        "/api/v1/cadastros/centro-custo", json={"nome": "Alpha CC"}, headers=_auth(token)
    )
    assert a.status_code == 201, a.text
    b = await client.post(
        "/api/v1/cadastros/centro-custo", json={"nome": "Beta CC"}, headers=_auth(token)
    )
    assert b.status_code == 201, b.text
    b_id = b.json()["id"]
    r = await client.put(
        f"/api/v1/cadastros/centro-custo/{b_id}",
        json={"nome": "Alpha CC", "responsavel": None, "observacoes": None, "version": 1},
        headers=_auth(token),
    )
    assert r.status_code == 409, r.text
