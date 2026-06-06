from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.crud_router import build_crud_router
from app.crud.base import CRUDBase
from app.crud.refs import compose, fk_validator
from app.models.cargo import Cargo
from app.models.centro_custo import CentroCusto
from app.models.colaborador import Colaborador
from app.models.combustivel import Combustivel
from app.models.conta_contabil import ContaContabil
from app.models.fornecedor import Fornecedor
from app.models.grupo_insumo import GrupoInsumo
from app.models.insumo import Insumo
from app.models.tipo_equipamento import TipoEquipamento
from app.models.tipo_servico import TipoServico
from app.models.unidade_medida import UnidadeMedida
from app.schemas.cargo import CargoCreate, CargoRead, CargoUpdate
from app.schemas.centro_custo import CentroCustoCreate, CentroCustoRead, CentroCustoUpdate
from app.schemas.colaborador import ColaboradorCreate, ColaboradorRead, ColaboradorUpdate
from app.schemas.combustivel import CombustivelCreate, CombustivelRead, CombustivelUpdate
from app.schemas.conta_contabil import ContaContabilCreate, ContaContabilRead, ContaContabilUpdate
from app.schemas.fornecedor import FornecedorCreate, FornecedorRead, FornecedorUpdate
from app.schemas.grupo_insumo import GrupoInsumoCreate, GrupoInsumoRead, GrupoInsumoUpdate
from app.schemas.insumo import InsumoCreate, InsumoRead, InsumoUpdate
from app.schemas.tipo_equipamento import (
    TipoEquipamentoCreate,
    TipoEquipamentoRead,
    TipoEquipamentoUpdate,
)
from app.schemas.tipo_servico import TipoServicoCreate, TipoServicoRead, TipoServicoUpdate
from app.schemas.unidade_medida import UnidadeMedidaCreate, UnidadeMedidaRead, UnidadeMedidaUpdate

_BASE = "/api/v1/cadastros"

routers: list[APIRouter] = [
    build_crud_router(
        prefix=f"{_BASE}/centro-custo",
        tag="cadastros:centro-custo",
        crud=CRUDBase(CentroCusto, search_fields=["nome", "codigo", "responsavel"]),
        create_schema=CentroCustoCreate,
        update_schema=CentroCustoUpdate,
        read_schema=CentroCustoRead,
    ),
    build_crud_router(
        prefix=f"{_BASE}/conta-contabil",
        tag="cadastros:conta-contabil",
        crud=CRUDBase(ContaContabil, search_fields=["nome", "grupo"]),
        create_schema=ContaContabilCreate,
        update_schema=ContaContabilUpdate,
        read_schema=ContaContabilRead,
    ),
    build_crud_router(
        prefix=f"{_BASE}/cargo",
        tag="cadastros:cargo",
        crud=CRUDBase(Cargo, search_fields=["nome"]),
        create_schema=CargoCreate,
        update_schema=CargoUpdate,
        read_schema=CargoRead,
    ),
    build_crud_router(
        prefix=f"{_BASE}/combustivel",
        tag="cadastros:combustivel",
        crud=CRUDBase(Combustivel, search_fields=["nome"]),
        create_schema=CombustivelCreate,
        update_schema=CombustivelUpdate,
        read_schema=CombustivelRead,
    ),
    build_crud_router(
        prefix=f"{_BASE}/tipo-equipamento",
        tag="cadastros:tipo-equipamento",
        crud=CRUDBase(TipoEquipamento, search_fields=["nome"]),
        create_schema=TipoEquipamentoCreate,
        update_schema=TipoEquipamentoUpdate,
        read_schema=TipoEquipamentoRead,
    ),
    build_crud_router(
        prefix=f"{_BASE}/tipo-servico",
        tag="cadastros:tipo-servico",
        crud=CRUDBase(TipoServico, search_fields=["nome"]),
        create_schema=TipoServicoCreate,
        update_schema=TipoServicoUpdate,
        read_schema=TipoServicoRead,
    ),
    build_crud_router(
        prefix=f"{_BASE}/grupo-insumo",
        tag="cadastros:grupo-insumo",
        crud=CRUDBase(GrupoInsumo, search_fields=["nome"]),
        create_schema=GrupoInsumoCreate,
        update_schema=GrupoInsumoUpdate,
        read_schema=GrupoInsumoRead,
    ),
    build_crud_router(
        prefix=f"{_BASE}/unidade-medida",
        tag="cadastros:unidade-medida",
        crud=CRUDBase(UnidadeMedida, search_fields=["codigo", "nome"]),
        create_schema=UnidadeMedidaCreate,
        update_schema=UnidadeMedidaUpdate,
        read_schema=UnidadeMedidaRead,
    ),
    build_crud_router(
        prefix=f"{_BASE}/colaborador",
        tag="cadastros:colaborador",
        crud=CRUDBase(Colaborador, search_fields=["nome", "email"]),
        create_schema=ColaboradorCreate,
        update_schema=ColaboradorUpdate,
        read_schema=ColaboradorRead,
        validate_refs=fk_validator("cargo_id", Cargo, "Cargo"),
    ),
    build_crud_router(
        prefix=f"{_BASE}/fornecedor",
        tag="cadastros:fornecedor",
        crud=CRUDBase(Fornecedor, search_fields=["nome", "cnpj_cpf", "cidade"]),
        create_schema=FornecedorCreate,
        update_schema=FornecedorUpdate,
        read_schema=FornecedorRead,
    ),
    build_crud_router(
        prefix=f"{_BASE}/insumo",
        tag="cadastros:insumo",
        crud=CRUDBase(Insumo, search_fields=["nome", "marca", "fabricante"]),
        create_schema=InsumoCreate,
        update_schema=InsumoUpdate,
        read_schema=InsumoRead,
        validate_refs=compose(
            fk_validator("grupo_insumo_id", GrupoInsumo, "Grupo de insumo"),
            fk_validator("unidade_medida_id", UnidadeMedida, "Unidade de medida"),
        ),
    ),
]
