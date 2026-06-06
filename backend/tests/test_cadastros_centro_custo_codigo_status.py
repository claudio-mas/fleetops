import pytest

pytestmark = pytest.mark.anyio


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_create_with_codigo_and_status(client, user_with_token):
    token = user_with_token["token"]
    r = await client.post(
        "/api/v1/cadastros/centro-custo",
        json={"nome": "Matriz", "codigo": "CC-1024", "status": "inativo"},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["codigo"] == "CC-1024"
    assert body["status"] == "inativo"


async def test_status_defaults_to_ativo(client, user_with_token):
    token = user_with_token["token"]
    r = await client.post(
        "/api/v1/cadastros/centro-custo",
        json={"nome": "Sem status"},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "ativo"
    assert r.json()["codigo"] is None


async def test_status_rejects_invalid_value(client, user_with_token):
    token = user_with_token["token"]
    r = await client.post(
        "/api/v1/cadastros/centro-custo",
        json={"nome": "Inválido", "status": "pendente"},
        headers=_auth(token),
    )
    assert r.status_code == 422, r.text


async def test_search_by_codigo(client, user_with_token):
    token = user_with_token["token"]
    await client.post(
        "/api/v1/cadastros/centro-custo",
        json={"nome": "Operações Sul", "codigo": "CC-9090"},
        headers=_auth(token),
    )
    r = await client.get("/api/v1/cadastros/centro-custo?search=CC-9090", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["codigo"] == "CC-9090"


async def test_update_status(client, user_with_token):
    token = user_with_token["token"]
    c = await client.post(
        "/api/v1/cadastros/centro-custo",
        json={"nome": "Frota Norte", "codigo": "CC-1", "status": "ativo"},
        headers=_auth(token),
    )
    obj_id = c.json()["id"]
    r = await client.put(
        f"/api/v1/cadastros/centro-custo/{obj_id}",
        json={
            "nome": "Frota Norte",
            "codigo": "CC-1",
            "status": "inativo",
            "responsavel": None,
            "observacoes": None,
            "version": 1,
        },
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "inativo"
