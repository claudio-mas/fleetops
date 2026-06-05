import pytest

pytestmark = pytest.mark.anyio


async def test_unidade_medida_uses_codigo(client, user_with_token):
    headers = {"Authorization": f"Bearer {user_with_token['token']}"}
    r = await client.post(
        "/api/v1/cadastros/unidade-medida",
        json={"codigo": "kg", "nome": "Quilograma"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["codigo"] == "kg"
    r = await client.get("/api/v1/cadastros/unidade-medida?search=kg", headers=headers)
    assert r.json()["total"] == 1


async def test_unidade_medida_duplicate_codigo_returns_409(client, user_with_token):
    headers = {"Authorization": f"Bearer {user_with_token['token']}"}
    p = {"codigo": "L", "nome": "Litro"}
    r1 = await client.post("/api/v1/cadastros/unidade-medida", json=p, headers=headers)
    assert r1.status_code == 201, r1.text
    r2 = await client.post("/api/v1/cadastros/unidade-medida", json=p, headers=headers)
    assert r2.status_code == 409, r2.text
