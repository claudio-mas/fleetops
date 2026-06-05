import pytest

pytestmark = pytest.mark.anyio


async def _mk(client, headers, resource, payload):
    r = await client.post(f"/api/v1/cadastros/{resource}", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_insumo_with_valid_refs(client, user_with_token):
    headers = {"Authorization": f"Bearer {user_with_token['token']}"}
    grupo_id = await _mk(client, headers, "grupo-insumo", {"nome": "Filtros"})
    um_id = await _mk(client, headers, "unidade-medida", {"codigo": "un", "nome": "Unidade"})
    r = await client.post(
        "/api/v1/cadastros/insumo",
        json={
            "nome": "Filtro de óleo",
            "grupo_insumo_id": grupo_id,
            "unidade_medida_id": um_id,
            "preco_medio": "29.9000",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["grupo_insumo_id"] == grupo_id
    assert body["unidade_medida_id"] == um_id


async def test_insumo_with_unknown_unidade_returns_400(client, user_with_token):
    import uuid

    headers = {"Authorization": f"Bearer {user_with_token['token']}"}
    r = await client.post(
        "/api/v1/cadastros/insumo",
        json={"nome": "X", "unidade_medida_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert r.status_code == 400
    assert "unidade" in r.json()["detail"].lower()
