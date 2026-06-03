import pytest

pytestmark = pytest.mark.anyio

SIMPLE_RESOURCES = [
    ("conta-contabil", {"nome": "Despesas Operacionais"}),
    ("cargo", {"nome": "Mecânico", "salario": "3500.0000"}),
    ("combustivel", {"nome": "Diesel S10"}),
    ("tipo-equipamento", {"nome": "Retroescavadeira", "depreciacao_anual": "10.0000"}),
    ("tipo-servico", {"nome": "Troca de óleo"}),
    ("grupo-insumo", {"nome": "Lubrificantes"}),
]


@pytest.mark.parametrize("resource,payload", SIMPLE_RESOURCES)
async def test_simple_cadastro_create_and_list(client, user_with_token, resource, payload):
    headers = {"Authorization": f"Bearer {user_with_token['token']}"}
    r = await client.post(f"/api/v1/cadastros/{resource}", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    r = await client.get(f"/api/v1/cadastros/{resource}", headers=headers)
    assert r.status_code == 200
    assert r.json()["total"] == 1
