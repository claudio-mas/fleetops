import pytest
from sqlalchemy import inspect

pytestmark = pytest.mark.asyncio

CADASTRO_TABLES = {
    "centro_custo",
    "conta_contabil",
    "cargo",
    "colaborador",
    "fornecedor",
    "combustivel",
    "tipo_equipamento",
    "tipo_servico",
    "grupo_insumo",
    "unidade_medida",
    "insumo",
}


async def test_all_cadastro_tables_exist(db_engine):
    async with db_engine.connect() as conn:
        names = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
    assert CADASTRO_TABLES.issubset(names)
