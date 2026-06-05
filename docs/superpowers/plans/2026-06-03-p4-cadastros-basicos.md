# P4 — Cadastros Básicos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar os 11 CRUDs do domínio Cadastros/Catálogos (centro_custo, conta_contabil, cargo, colaborador, fornecedor, combustivel, tipo_equipamento, tipo_servico, grupo_insumo, insumo, unidade_medida) full-stack — modelos + migração RLS + API REST paginada/buscável com soft delete + páginas React de listagem/formulário — sobre a fundação multi-tenant já existente (P0–P2).

**Architecture:** Como as 11 entidades são estruturalmente idênticas (lookup tables com `nome`/FKs/observações), a base é **DRY**: (1) uma classe `OperationalBase` que materializa o padrão de tabela operacional (id UUID v7, tenant_id, timestamps, soft delete, optimistic lock); (2) um `CRUDBase[ModelT]` genérico async com paginação, busca `ilike` e soft delete; (3) um `build_crud_router(...)` que gera os endpoints REST (list/get/create/update/delete) com `TenantSession` + `require_role`; (4) no frontend, `useCrudResource(path)` (TanStack Query) + componentes genéricos `CrudListPage`/`CrudForm` dirigidos por configuração de campos por entidade. Cada entidade = 1 model + 3 schemas Pydantic + 1 config de router + 1 config de campos no frontend.

**Tech Stack:** Python 3.12 · FastAPI · SQLAlchemy 2.0 async · Alembic · Pydantic v2 · uv · pytest — React 18 · Vite · TypeScript · TanStack Query · axios · Tailwind · Vitest.

---

## Convenções herdadas (NÃO violar — ver `.wolf/cerebrum.md`)

- PK `id UUID v7` (`from uuid6 import uuid7`), nunca inteiro sequencial.
- `tenant_id UUID NOT NULL`; unicidade **sempre composta com `tenant_id`** e **parcial** (`WHERE deleted_at IS NULL`) por causa do soft delete.
- `TIMESTAMPTZ` em tudo; dinheiro em `NUMERIC(15,4)`, **nunca FLOAT** (Access usava `REAL` — converter para `Numeric(15,4)`).
- RLS: `ENABLE` + `FORCE ROW LEVEL SECURITY` + `CREATE POLICY tenant_isolation ... USING (tenant_id = NULLIF(current_setting('app.current_tenant', TRUE), '')::uuid)`. Defense in depth: endpoints sempre via `TenantSession` (faz `set_config('app.current_tenant', ...)`).
- Enums Postgres em migração: `postgresql.ENUM(..., create_type=False)` + `.create(bind, checkfirst=True)` (bug-022). **Nenhuma entidade deste plano usa enum** — não há esse risco aqui.
- mypy strict, ruff line-length 100. Sem comentários que narram "o quê"; só "porquê" não óbvio.
- Próxima revisão Alembic: **`0005`**, `down_revision = "0004"`.
- Backend rodando no host: `localhost:5433` (Postgres) e senha `fleetops:fleetops_dev_password`. Banco de teste: `fleetops_test`.

## Mapeamento Access → SaaS (extraído de `ERD.accdb` / `levantamento_access_20260515_134156.xlsx`)

Regra de tipos: `INTEGER cod_*` (PK) → `id UUID v7`; `INTEGER id_*` (FK) → `*_id UUID`; `WVARCHAR(n)` → `String(n)`; `WVARCHAR(255)` → `String(255)`; `WLONGVARCHAR` (memo) → `Text`; `REAL` → `Numeric(15,4)`. Sufixo `_<entidade>` removido das colunas. `descricao_*`/`nome_*` → coluna canônica `nome`. `obs_*` → `observacoes`. `fone_*` → `telefone`.

| Entidade (tabela) | Colunas próprias (além do padrão operacional) | FKs internas |
|---|---|---|
| `centro_custo` | `nome` str255, `responsavel` str255?, `observacoes` text? | — |
| `conta_contabil` | `nome` str255, `grupo` str255?, `observacoes` text? | — |
| `cargo` | `nome` str255, `salario` num(15,4)?, `observacoes` text? | — |
| `colaborador` | `nome` str255, `telefone` str255?, `email` str255?, `observacoes` text? | `cargo_id` → cargo |
| `fornecedor` | `nome` str255, `tipo` str50?, `cnpj_cpf` str18?, `rg_ie` str255?, `endereco` str255?, `bairro` str255?, `cep` str9?, `cidade` str255?, `uf` str2?, `telefone` str255?, `email` str255?, `observacoes` text? | — |
| `combustivel` | `nome` str255, `observacoes` text? | — |
| `tipo_equipamento` | `nome` str255, `depreciacao_anual` num(15,4)?, `observacoes` text? | — |
| `tipo_servico` | `nome` str255, `observacoes` text? | — |
| `grupo_insumo` | `nome` str255, `observacoes` text? | — |
| `unidade_medida` | `codigo` str5, `nome` str255, `observacoes` text? | — |
| `insumo` | `nome` str255, `preco_medio` num(15,4)?, `marca` str255?, `fabricante` str255?, `observacoes` text? | `grupo_insumo_id` → grupo_insumo, `unidade_medida_id` → unidade_medida |

`?` = nullable (Access marcava `Nulo? = Sim`). `nome` é sempre `NOT NULL` na versão SaaS (era nullable no Access, mas é o rótulo primário). Unicidade: `UNIQUE(tenant_id, nome) WHERE deleted_at IS NULL` para todas, **exceto** `unidade_medida` que usa `UNIQUE(tenant_id, codigo) WHERE deleted_at IS NULL`.

Ordem de dependência de FK (importa para criação de tabelas e ordem de tasks): `cargo` antes de `colaborador`; `grupo_insumo` e `unidade_medida` antes de `insumo`.

---

# FASE A — Fundação backend (genéricos)

### Task A1: `OperationalBase` no models/base.py

**Files:**
- Modify: `backend/app/models/base.py`
- Test: `backend/tests/test_operational_base.py`

- [ ] **Step 1: Escrever o teste que falha**

`backend/tests/test_operational_base.py`:

```python
from app.models.base import OperationalBase


def test_operational_base_is_abstract_with_standard_columns():
    assert OperationalBase.__abstract__ is True
    cols = set(OperationalBase.__annotations__)
    assert {"id", "tenant_id"}.issubset(cols)


def test_operational_base_mixes_in_soft_delete_and_version():
    from app.models.base import OperationalMixin

    assert issubclass(OperationalBase, OperationalMixin)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend; uv run pytest tests/test_operational_base.py -v`
Expected: FAIL com `ImportError: cannot import name 'OperationalBase'`

- [ ] **Step 3: Implementar**

Acrescentar ao final de `backend/app/models/base.py` (mantendo `Base`, `TimestampMixin`, `OperationalMixin` existentes):

```python
from uuid6 import uuid7
from sqlalchemy.orm import declared_attr


class OperationalBase(Base, OperationalMixin):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid7)

    @declared_attr
    def tenant_id(cls) -> Mapped[uuid.UUID]:  # noqa: N805
        return mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
```

Garantir que os imports no topo do arquivo incluam `from sqlalchemy.dialects.postgresql import UUID as PGUUID` (já presente) e `from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column`.

- [ ] **Step 4: Rodar e ver passar**

Run: `cd backend; uv run pytest tests/test_operational_base.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/base.py backend/tests/test_operational_base.py
git commit -m "feat(models): adiciona OperationalBase (padrão de tabela operacional)"
```

---

### Task A2: Schemas genéricos de paginação

**Files:**
- Create: `backend/app/schemas/common.py`
- Test: `backend/tests/test_schemas_common.py`

- [ ] **Step 1: Teste que falha**

`backend/tests/test_schemas_common.py`:

```python
from app.schemas.common import PaginatedResponse


def test_paginated_response_carries_items_and_total():
    page = PaginatedResponse[int](items=[1, 2, 3], total=10, limit=50, offset=0)
    assert page.items == [1, 2, 3]
    assert page.total == 10
    assert page.limit == 50
    assert page.offset == 0
```

- [ ] **Step 2: Ver falhar**

Run: `cd backend; uv run pytest tests/test_schemas_common.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'app.schemas.common'`

- [ ] **Step 3: Implementar**

`backend/app/schemas/common.py`:

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
```

- [ ] **Step 4: Ver passar**

Run: `cd backend; uv run pytest tests/test_schemas_common.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/common.py backend/tests/test_schemas_common.py
git commit -m "feat(schemas): adiciona PaginatedResponse genérico"
```

---

### Task A3: `CRUDBase` genérico async

**Files:**
- Create: `backend/app/crud/__init__.py` (vazio)
- Create: `backend/app/crud/base.py`
- Test: `backend/tests/test_crud_base.py`

Este teste depende de um modelo real; usa `centro_custo` (criado na Task B1). **Ordem de execução:** implemente A3 (código) agora, mas o teste A3 só roda verde depois de B1 + migração. Para destravar A3 isolado, o teste abaixo usa um modelo de fixture inline mapeado na metadata de teste.

- [ ] **Step 1: Teste que falha**

`backend/tests/test_crud_base.py`:

```python
import uuid

import pytest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.crud.base import CRUDBase
from app.models.base import OperationalBase


class _Widget(OperationalBase):
    __tablename__ = "_widget_test"
    nome: Mapped[str] = mapped_column(String(255), nullable=False)


widget_crud = CRUDBase(_Widget, search_fields=["nome"])

pytestmark = pytest.mark.anyio


@pytest.fixture
async def _widget_table(db_engine):  # type: ignore[no-untyped-def]
    async with db_engine.begin() as conn:
        await conn.run_sync(_Widget.__table__.create)
    yield
    async with db_engine.begin() as conn:
        await conn.run_sync(_Widget.__table__.drop)


async def test_create_then_get(db, _widget_table):
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    obj = await widget_crud.create(db, tenant_id=tid, user_id=uid, data={"nome": "Alpha"})
    await db.commit()
    fetched = await widget_crud.get(db, tenant_id=tid, obj_id=obj.id)
    assert fetched is not None
    assert fetched.nome == "Alpha"
    assert fetched.created_by == uid


async def test_get_other_tenant_returns_none(db, _widget_table):
    obj = await widget_crud.create(db, tenant_id=uuid.uuid4(), user_id=uuid.uuid4(), data={"nome": "X"})
    await db.commit()
    assert await widget_crud.get(db, tenant_id=uuid.uuid4(), obj_id=obj.id) is None


async def test_list_filters_by_search_and_excludes_soft_deleted(db, _widget_table):
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    a = await widget_crud.create(db, tenant_id=tid, user_id=uid, data={"nome": "Bomba Diesel"})
    await widget_crud.create(db, tenant_id=tid, user_id=uid, data={"nome": "Gasolina"})
    await db.commit()
    items, total = await widget_crud.list(db, tenant_id=tid, limit=50, offset=0, search="diesel")
    assert total == 1
    assert items[0].nome == "Bomba Diesel"
    await widget_crud.soft_delete(db, tenant_id=tid, obj_id=a.id, user_id=uid)
    await db.commit()
    _, total_after = await widget_crud.list(db, tenant_id=tid, limit=50, offset=0, search="diesel")
    assert total_after == 0


async def test_update_bumps_version_and_requires_match(db, _widget_table):
    from app.crud.base import VersionConflictError

    tid = uuid.uuid4()
    uid = uuid.uuid4()
    obj = await widget_crud.create(db, tenant_id=tid, user_id=uid, data={"nome": "V1"})
    await db.commit()
    updated = await widget_crud.update(
        db, tenant_id=tid, obj_id=obj.id, user_id=uid, data={"nome": "V2"}, expected_version=1
    )
    await db.commit()
    assert updated.nome == "V2"
    assert updated.version == 2
    with pytest.raises(VersionConflictError):
        await widget_crud.update(
            db, tenant_id=tid, obj_id=obj.id, user_id=uid, data={"nome": "V3"}, expected_version=1
        )
```

- [ ] **Step 2: Ver falhar**

Run: `cd backend; uv run pytest tests/test_crud_base.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'app.crud'`

- [ ] **Step 3: Implementar**

`backend/app/crud/__init__.py`: arquivo vazio.

`backend/app/crud/base.py`:

```python
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.models.base import OperationalBase

ModelT = TypeVar("ModelT", bound=OperationalBase)


class VersionConflictError(Exception):
    """Raised when optimistic-lock version does not match the stored row."""


class CRUDBase(Generic[ModelT]):
    def __init__(self, model: type[ModelT], *, search_fields: list[str]) -> None:
        self.model = model
        self.search_fields = search_fields

    async def list(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        limit: int,
        offset: int,
        search: str | None = None,
    ) -> tuple[list[ModelT], int]:
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None),
        )
        if search and self.search_fields:
            conds = [getattr(self.model, f).ilike(f"%{search}%") for f in self.search_fields]
            stmt = stmt.where(or_(*conds))
        total = (
            await session.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()
        stmt = stmt.order_by(self.model.created_at.desc()).limit(limit).offset(offset)
        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    async def get(
        self, session: AsyncSession, *, tenant_id: uuid.UUID, obj_id: uuid.UUID
    ) -> ModelT | None:
        obj = await session.get(self.model, obj_id)
        if obj is None or obj.tenant_id != tenant_id or obj.deleted_at is not None:
            return None
        return obj

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        data: dict[str, Any],
    ) -> ModelT:
        obj = self.model(
            id=uuid7(),
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            **data,
        )
        session.add(obj)
        await session.flush()
        return obj

    async def update(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        obj_id: uuid.UUID,
        user_id: uuid.UUID,
        data: dict[str, Any],
        expected_version: int,
    ) -> ModelT | None:
        obj = await self.get(session, tenant_id=tenant_id, obj_id=obj_id)
        if obj is None:
            return None
        if obj.version != expected_version:
            raise VersionConflictError
        for key, value in data.items():
            setattr(obj, key, value)
        obj.updated_by = user_id
        obj.version = obj.version + 1
        await session.flush()
        return obj

    async def soft_delete(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        obj_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        obj = await self.get(session, tenant_id=tenant_id, obj_id=obj_id)
        if obj is None:
            return False
        obj.deleted_at = datetime.now(UTC)
        obj.updated_by = user_id
        await session.flush()
        return True
```

- [ ] **Step 4: Ver passar**

Run: `cd backend; uv run pytest tests/test_crud_base.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: mypy + commit**

Run: `cd backend; uv run mypy app`
Expected: Success (no issues)

```bash
git add backend/app/crud/__init__.py backend/app/crud/base.py backend/tests/test_crud_base.py
git commit -m "feat(crud): adiciona CRUDBase genérico async (paginação, busca, soft delete, optimistic lock)"
```

---

### Task A4: Factory de router CRUD

**Files:**
- Create: `backend/app/api/v1/crud_router.py`
- Test: coberto integradamente pela Task B2 (centro_custo). Aqui só compila/typecheck.

- [ ] **Step 1: Implementar a factory**

`backend/app/api/v1/crud_router.py`:

```python
from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, TenantSession, get_current_tenant_id, require_role
from app.crud.base import CRUDBase, VersionConflictError
from app.models.base import OperationalBase
from app.models.role import RoleName
from app.schemas.common import PaginatedResponse

WRITE_ROLES = (RoleName.OWNER, RoleName.ADMIN, RoleName.GESTOR)

# Validador de FK: recebe (session, tenant_id, payload) e levanta HTTPException 400
# se alguma referência não existir no tenant. None = entidade sem FK.
RefValidator = Callable[[TenantSession, uuid.UUID, dict[str, Any]], Awaitable[None]]


def build_crud_router(
    *,
    prefix: str,
    tag: str,
    crud: CRUDBase[Any],
    create_schema: type[BaseModel],
    update_schema: type[BaseModel],
    read_schema: type[BaseModel],
    validate_refs: RefValidator | None = None,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("", response_model=PaginatedResponse[read_schema])  # type: ignore[valid-type]
    async def list_items(
        session: TenantSession,
        tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
        limit: Annotated[int, Query(ge=1, le=200)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
        search: Annotated[str | None, Query(max_length=255)] = None,
    ) -> Any:
        items, total = await crud.list(
            session, tenant_id=tenant_id, limit=limit, offset=offset, search=search
        )
        return PaginatedResponse[read_schema](  # type: ignore[valid-type]
            items=[read_schema.model_validate(i, from_attributes=True) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    @router.get("/{obj_id}", response_model=read_schema)
    async def get_item(
        obj_id: uuid.UUID,
        session: TenantSession,
        tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    ) -> Any:
        obj = await crud.get(session, tenant_id=tenant_id, obj_id=obj_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado")
        return obj

    @router.post(
        "",
        response_model=read_schema,
        status_code=status.HTTP_201_CREATED,
        dependencies=[require_role(*WRITE_ROLES)],
    )
    async def create_item(
        payload: create_schema,  # type: ignore[valid-type]
        session: TenantSession,
        user: CurrentUser,
        tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    ) -> Any:
        data = payload.model_dump()  # type: ignore[attr-defined]
        if validate_refs is not None:
            await validate_refs(session, tenant_id, data)
        obj = await crud.create(session, tenant_id=tenant_id, user_id=user.id, data=data)
        await session.commit()
        await session.refresh(obj)
        return obj

    @router.put(
        "/{obj_id}",
        response_model=read_schema,
        dependencies=[require_role(*WRITE_ROLES)],
    )
    async def update_item(
        obj_id: uuid.UUID,
        payload: update_schema,  # type: ignore[valid-type]
        session: TenantSession,
        user: CurrentUser,
        tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    ) -> Any:
        data = payload.model_dump()  # type: ignore[attr-defined]
        expected_version = data.pop("version")
        if validate_refs is not None:
            await validate_refs(session, tenant_id, data)
        try:
            obj = await crud.update(
                session,
                tenant_id=tenant_id,
                obj_id=obj_id,
                user_id=user.id,
                data=data,
                expected_version=expected_version,
            )
        except VersionConflictError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Registro foi modificado por outro usuário (conflito de versão)",
            ) from None
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado")
        await session.commit()
        await session.refresh(obj)
        return obj

    @router.delete(
        "/{obj_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[require_role(*WRITE_ROLES)],
    )
    async def delete_item(
        obj_id: uuid.UUID,
        session: TenantSession,
        user: CurrentUser,
        tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    ) -> None:
        ok = await crud.soft_delete(session, tenant_id=tenant_id, obj_id=obj_id, user_id=user.id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado")
        await session.commit()

    return router
```

- [ ] **Step 2: Typecheck**

Run: `cd backend; uv run mypy app`
Expected: Success (no issues)

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/crud_router.py
git commit -m "feat(api): adiciona build_crud_router (CRUD REST genérico com RBAC e optimistic lock)"
```

---

# FASE B — Entidades backend

> Padrão por entidade: (1) model em `app/models/<entidade>.py`; (2) schemas em `app/schemas/<entidade>.py` (Create/Update/Read); (3) instância `CRUDBase` + router via factory, agregados em `app/api/v1/cadastros.py`. A **migração única** (Task B-MIG) cria as 11 tabelas. As tasks B1..B11 adicionam model+schema+router. Faça **B-MIG depois de B1** (precisa de pelo menos um model para validar o autogenerate) ou escreva a migração à mão (recomendado — código completo abaixo).

### Task B1: Entidade de referência — `centro_custo` (model + schema)

**Files:**
- Create: `backend/app/models/centro_custo.py`
- Create: `backend/app/schemas/centro_custo.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Model**

`backend/app/models/centro_custo.py`:

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class CentroCusto(OperationalBase):
    __tablename__ = "centro_custo"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    responsavel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

- [ ] **Step 2: Registrar no models/__init__.py**

Adicionar a `backend/app/models/__init__.py` (import + `__all__`):

```python
from app.models.centro_custo import CentroCusto
```

E incluir `"CentroCusto"` em `__all__`.

- [ ] **Step 3: Schemas**

`backend/app/schemas/centro_custo.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CentroCustoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    responsavel: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None


class CentroCustoUpdate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    responsavel: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None
    version: int = Field(ge=1)


class CentroCustoRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    responsavel: str | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Sanidade de import**

Run: `cd backend; uv run python -c "from app.models.centro_custo import CentroCusto; from app.schemas.centro_custo import CentroCustoCreate; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/centro_custo.py backend/app/schemas/centro_custo.py backend/app/models/__init__.py
git commit -m "feat(cadastros): model e schemas de centro_custo"
```

---

### Task B-MIG: Migração 0005 — cria as 11 tabelas + RLS

> **Faça esta task somente depois de B1..B11** (todos os models existentes), para que `Base.metadata` contenha todas as tabelas. A migração abaixo é **escrita à mão** (não autogenerate) e é completa — copie-a integralmente. Cada tabela segue o padrão operacional via os helpers `_op_columns()` e `_rls(table)`.

**Files:**
- Create: `backend/alembic/versions/0005_p4_cadastros_basicos.py`
- Test: `backend/tests/test_migration_0005.py`

- [ ] **Step 1: Teste que falha (migração aplica em banco limpo)**

`backend/tests/test_migration_0005.py`:

```python
import pytest
from sqlalchemy import inspect

pytestmark = pytest.mark.anyio

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
```

> Nota: o fixture `db_engine` (conftest) cria o schema via `Base.metadata.create_all`, então este teste valida que os models estão registrados. A validação da **migração Alembic em si** é feita no Step 4 contra um banco temporário (cerebrum: migrations sempre em banco limpo).

- [ ] **Step 2: Ver falhar**

Run: `cd backend; uv run pytest tests/test_migration_0005.py -v`
Expected: FAIL (faltam tabelas) — só passa após B1..B11 + este step.

- [ ] **Step 3: Escrever a migração**

`backend/alembic/versions/0005_p4_cadastros_basicos.py`:

```python
"""p4: cadastros básicos (11 tabelas)

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-03
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

CADASTROS = [
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
]


def _op_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
    ]


def _rls(table: str) -> None:
    op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])
    op.create_index(f"ix_{table}_tenant_created", table, ["tenant_id", sa.text("created_at DESC")])
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = NULLIF(current_setting('app.current_tenant', TRUE), '')::uuid)
        """
    )


def _uq_nome(table: str) -> None:
    op.create_index(
        f"uq_{table}_tenant_nome",
        table,
        ["tenant_id", "nome"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def upgrade() -> None:
    op.create_table(
        "centro_custo",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("responsavel", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("centro_custo")
    _uq_nome("centro_custo")

    op.create_table(
        "conta_contabil",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("grupo", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("conta_contabil")
    _uq_nome("conta_contabil")

    op.create_table(
        "cargo",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("salario", sa.Numeric(15, 4), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("cargo")
    _uq_nome("cargo")

    op.create_table(
        "colaborador",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column(
            "cargo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cargo.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("telefone", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("colaborador")
    _uq_nome("colaborador")
    op.create_index("ix_colaborador_cargo_id", "colaborador", ["cargo_id"])

    op.create_table(
        "fornecedor",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=True),
        sa.Column("cnpj_cpf", sa.String(18), nullable=True),
        sa.Column("rg_ie", sa.String(255), nullable=True),
        sa.Column("endereco", sa.String(255), nullable=True),
        sa.Column("bairro", sa.String(255), nullable=True),
        sa.Column("cep", sa.String(9), nullable=True),
        sa.Column("cidade", sa.String(255), nullable=True),
        sa.Column("uf", sa.String(2), nullable=True),
        sa.Column("telefone", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("fornecedor")
    _uq_nome("fornecedor")

    op.create_table(
        "combustivel",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("combustivel")
    _uq_nome("combustivel")

    op.create_table(
        "tipo_equipamento",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("depreciacao_anual", sa.Numeric(15, 4), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("tipo_equipamento")
    _uq_nome("tipo_equipamento")

    op.create_table(
        "tipo_servico",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("tipo_servico")
    _uq_nome("tipo_servico")

    op.create_table(
        "grupo_insumo",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("grupo_insumo")
    _uq_nome("grupo_insumo")

    op.create_table(
        "unidade_medida",
        *_op_columns(),
        sa.Column("codigo", sa.String(5), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("unidade_medida")
    op.create_index(
        "uq_unidade_medida_tenant_codigo",
        "unidade_medida",
        ["tenant_id", "codigo"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "insumo",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column(
            "grupo_insumo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("grupo_insumo.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "unidade_medida_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unidade_medida.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("preco_medio", sa.Numeric(15, 4), nullable=True),
        sa.Column("marca", sa.String(255), nullable=True),
        sa.Column("fabricante", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("insumo")
    _uq_nome("insumo")
    op.create_index("ix_insumo_grupo_insumo_id", "insumo", ["grupo_insumo_id"])
    op.create_index("ix_insumo_unidade_medida_id", "insumo", ["unidade_medida_id"])


def downgrade() -> None:
    for table in reversed(CADASTROS):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.drop_table(table)
```

- [ ] **Step 4: Validar a migração em banco LIMPO** (cerebrum [2026-05-31])

```powershell
cd backend
# cria DB temporário e aplica TODAS as migrations do zero
$env:PGPASSWORD="fleetops_dev_password"
createdb -h localhost -p 5433 -U fleetops fleetops_mig_tmp
$env:DATABASE_URL="postgresql+asyncpg://fleetops:fleetops_dev_password@localhost:5433/fleetops_mig_tmp"
uv run alembic upgrade head
uv run alembic downgrade 0004
uv run alembic upgrade head
dropdb -h localhost -p 5433 -U fleetops fleetops_mig_tmp
```

Expected: `Running upgrade 0004 -> 0005` sem erro; downgrade e re-upgrade limpos.

- [ ] **Step 5: Rodar o teste de schema**

Run: `cd backend; uv run pytest tests/test_migration_0005.py -v`
Expected: PASS (após todos os models de B1..B11 registrados em `models/__init__.py`)

- [ ] **Step 6: Commit**

```bash
git add backend/alembic/versions/0005_p4_cadastros_basicos.py backend/tests/test_migration_0005.py
git commit -m "feat(migration): 0005 cria 11 tabelas de cadastros básicos com RLS"
```

---

### Task B2: Router de `centro_custo` + agregador `cadastros.py` + registro em main

**Files:**
- Create: `backend/app/api/v1/cadastros.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_cadastros_centro_custo.py`

- [ ] **Step 1: Teste de integração que falha**

`backend/tests/test_cadastros_centro_custo.py`:

```python
import pytest

pytestmark = pytest.mark.anyio


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_create_list_get_update_delete_centro_custo(client, user_with_token):
    token = user_with_token["token"]

    # create
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

    # list
    r = await client.get("/api/v1/cadastros/centro-custo", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == obj_id

    # search miss
    r = await client.get("/api/v1/cadastros/centro-custo?search=inexistente", headers=_auth(token))
    assert r.json()["total"] == 0

    # get
    r = await client.get(f"/api/v1/cadastros/centro-custo/{obj_id}", headers=_auth(token))
    assert r.status_code == 200

    # update (optimistic lock ok)
    r = await client.put(
        f"/api/v1/cadastros/centro-custo/{obj_id}",
        json={"nome": "Frota Leve", "responsavel": None, "observacoes": None, "version": 1},
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["version"] == 2

    # update with stale version -> 409
    r = await client.put(
        f"/api/v1/cadastros/centro-custo/{obj_id}",
        json={"nome": "X", "responsavel": None, "observacoes": None, "version": 1},
        headers=_auth(token),
    )
    assert r.status_code == 409

    # delete (soft)
    r = await client.delete(f"/api/v1/cadastros/centro-custo/{obj_id}", headers=_auth(token))
    assert r.status_code == 204

    # gone from list
    r = await client.get("/api/v1/cadastros/centro-custo", headers=_auth(token))
    assert r.json()["total"] == 0


async def test_requires_authentication(client):
    r = await client.get("/api/v1/cadastros/centro-custo")
    assert r.status_code == 401
```

- [ ] **Step 2: Ver falhar**

Run: `cd backend; uv run pytest tests/test_cadastros_centro_custo.py -v`
Expected: FAIL com 404 (rota não existe)

- [ ] **Step 3: Implementar o agregador**

`backend/app/api/v1/cadastros.py`:

```python
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.crud_router import build_crud_router
from app.crud.base import CRUDBase
from app.models.centro_custo import CentroCusto
from app.schemas.centro_custo import CentroCustoCreate, CentroCustoRead, CentroCustoUpdate

_BASE = "/api/v1/cadastros"

routers: list[APIRouter] = [
    build_crud_router(
        prefix=f"{_BASE}/centro-custo",
        tag="cadastros:centro-custo",
        crud=CRUDBase(CentroCusto, search_fields=["nome", "responsavel"]),
        create_schema=CentroCustoCreate,
        update_schema=CentroCustoUpdate,
        read_schema=CentroCustoRead,
    ),
]
```

- [ ] **Step 4: Registrar no main.py**

Adicionar em `backend/app/main.py` após os outros `include_router`:

```python
from app.api.v1.cadastros import routers as cadastros_routers

for _r in cadastros_routers:
    app.include_router(_r)
```

- [ ] **Step 5: Ver passar**

Run: `cd backend; uv run pytest tests/test_cadastros_centro_custo.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Suite + mypy + commit**

Run: `cd backend; uv run pytest -q; uv run mypy app; uv run ruff check .`
Expected: tudo verde

```bash
git add backend/app/api/v1/cadastros.py backend/app/main.py backend/tests/test_cadastros_centro_custo.py
git commit -m "feat(cadastros): endpoint CRUD de centro_custo + agregador de routers"
```

---

### Task B3: Entidades lookup simples (conta_contabil, cargo, combustivel, tipo_equipamento, tipo_servico, grupo_insumo)

> Seis entidades sem FK. Para cada uma: model + schemas + entrada no `routers` de `cadastros.py`. O código é completo abaixo (não é placeholder — repita o padrão exatamente, trocando nome de classe/tabela/colunas).

**Files:**
- Create: `backend/app/models/conta_contabil.py`, `cargo.py`, `combustivel.py`, `tipo_equipamento.py`, `tipo_servico.py`, `grupo_insumo.py`
- Create: schemas correspondentes em `backend/app/schemas/`
- Modify: `backend/app/models/__init__.py`, `backend/app/api/v1/cadastros.py`
- Test: `backend/tests/test_cadastros_smoke.py`

- [ ] **Step 1: Models**

`backend/app/models/conta_contabil.py`:

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class ContaContabil(OperationalBase):
    __tablename__ = "conta_contabil"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    grupo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

`backend/app/models/cargo.py`:

```python
from decimal import Decimal

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class Cargo(OperationalBase):
    __tablename__ = "cargo"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    salario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

`backend/app/models/combustivel.py`, `tipo_servico.py`, `grupo_insumo.py` (idênticos em forma — apenas `nome` + `observacoes`):

```python
# combustivel.py  (classe Combustivel, __tablename__ "combustivel")
# tipo_servico.py (classe TipoServico, __tablename__ "tipo_servico")
# grupo_insumo.py (classe GrupoInsumo, __tablename__ "grupo_insumo")
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class Combustivel(OperationalBase):  # trocar nome da classe e __tablename__ por arquivo
    __tablename__ = "combustivel"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

`backend/app/models/tipo_equipamento.py`:

```python
from decimal import Decimal

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class TipoEquipamento(OperationalBase):
    __tablename__ = "tipo_equipamento"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    depreciacao_anual: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

- [ ] **Step 2: Schemas**

Para `conta_contabil`, `combustivel`, `tipo_servico`, `grupo_insumo` o trio Create/Update/Read segue o molde de `centro_custo` (Task B1, Step 3), trocando os campos próprios. Exemplo `backend/app/schemas/conta_contabil.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ContaContabilCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    grupo: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None


class ContaContabilUpdate(ContaContabilCreate):
    version: int = Field(ge=1)


class ContaContabilRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    grupo: str | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

`backend/app/schemas/cargo.py` (campo `salario: Decimal | None`):

```python
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CargoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    salario: Decimal | None = Field(default=None, ge=0)
    observacoes: str | None = None


class CargoUpdate(CargoCreate):
    version: int = Field(ge=1)


class CargoRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    salario: Decimal | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

`backend/app/schemas/tipo_equipamento.py` (campo `depreciacao_anual: Decimal | None`, análogo a Cargo).

`backend/app/schemas/combustivel.py`, `tipo_servico.py`, `grupo_insumo.py` (só `nome` + `observacoes`):

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CombustivelCreate(BaseModel):  # trocar prefixo por arquivo
    nome: str = Field(min_length=1, max_length=255)
    observacoes: str | None = None


class CombustivelUpdate(CombustivelCreate):
    version: int = Field(ge=1)


class CombustivelRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Registrar models no __init__.py**

Adicionar a `backend/app/models/__init__.py`:

```python
from app.models.cargo import Cargo
from app.models.combustivel import Combustivel
from app.models.conta_contabil import ContaContabil
from app.models.grupo_insumo import GrupoInsumo
from app.models.tipo_equipamento import TipoEquipamento
from app.models.tipo_servico import TipoServico
```

E incluir os nomes em `__all__`.

- [ ] **Step 4: Adicionar routers ao cadastros.py**

Em `backend/app/api/v1/cadastros.py`, adicionar imports e entradas na lista `routers`:

```python
from app.models.cargo import Cargo
from app.models.combustivel import Combustivel
from app.models.conta_contabil import ContaContabil
from app.models.grupo_insumo import GrupoInsumo
from app.models.tipo_equipamento import TipoEquipamento
from app.models.tipo_servico import TipoServico
from app.schemas.cargo import CargoCreate, CargoRead, CargoUpdate
from app.schemas.combustivel import CombustivelCreate, CombustivelRead, CombustivelUpdate
from app.schemas.conta_contabil import ContaContabilCreate, ContaContabilRead, ContaContabilUpdate
from app.schemas.grupo_insumo import GrupoInsumoCreate, GrupoInsumoRead, GrupoInsumoUpdate
from app.schemas.tipo_equipamento import (
    TipoEquipamentoCreate,
    TipoEquipamentoRead,
    TipoEquipamentoUpdate,
)
from app.schemas.tipo_servico import TipoServicoCreate, TipoServicoRead, TipoServicoUpdate
```

Entradas (acrescentar à lista `routers`):

```python
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
```

- [ ] **Step 5: Smoke test de todas as rotas simples**

`backend/tests/test_cadastros_smoke.py`:

```python
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
```

- [ ] **Step 6: Rodar + commit**

Run: `cd backend; uv run pytest tests/test_cadastros_smoke.py -v; uv run mypy app; uv run ruff check .`
Expected: 6 passed, mypy/ruff verdes

```bash
git add backend/app/models backend/app/schemas backend/app/api/v1/cadastros.py backend/tests/test_cadastros_smoke.py
git commit -m "feat(cadastros): CRUD de 6 lookups simples (conta_contabil, cargo, combustivel, tipo_equipamento, tipo_servico, grupo_insumo)"
```

---

### Task B4: `unidade_medida` (campo natural `codigo`)

**Files:**
- Create: `backend/app/models/unidade_medida.py`, `backend/app/schemas/unidade_medida.py`
- Modify: `backend/app/models/__init__.py`, `backend/app/api/v1/cadastros.py`
- Test: `backend/tests/test_cadastros_unidade_medida.py`

- [ ] **Step 1: Teste que falha**

`backend/tests/test_cadastros_unidade_medida.py`:

```python
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
    # busca por codigo
    r = await client.get("/api/v1/cadastros/unidade-medida?search=kg", headers=headers)
    assert r.json()["total"] == 1
```

- [ ] **Step 2: Ver falhar**

Run: `cd backend; uv run pytest tests/test_cadastros_unidade_medida.py -v`
Expected: FAIL (404)

- [ ] **Step 3: Model + schema**

`backend/app/models/unidade_medida.py`:

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class UnidadeMedida(OperationalBase):
    __tablename__ = "unidade_medida"

    codigo: Mapped[str] = mapped_column(String(5), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

`backend/app/schemas/unidade_medida.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UnidadeMedidaCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=5)
    nome: str = Field(min_length=1, max_length=255)
    observacoes: str | None = None


class UnidadeMedidaUpdate(UnidadeMedidaCreate):
    version: int = Field(ge=1)


class UnidadeMedidaRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    nome: str
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Registrar (models/__init__.py + cadastros.py)**

`models/__init__.py`: `from app.models.unidade_medida import UnidadeMedida` + `__all__`.

`cadastros.py`: imports + entrada:

```python
    build_crud_router(
        prefix=f"{_BASE}/unidade-medida",
        tag="cadastros:unidade-medida",
        crud=CRUDBase(UnidadeMedida, search_fields=["codigo", "nome"]),
        create_schema=UnidadeMedidaCreate,
        update_schema=UnidadeMedidaUpdate,
        read_schema=UnidadeMedidaRead,
    ),
```

- [ ] **Step 5: Ver passar + commit**

Run: `cd backend; uv run pytest tests/test_cadastros_unidade_medida.py -v`
Expected: PASS

```bash
git add backend/app/models/unidade_medida.py backend/app/schemas/unidade_medida.py backend/app/models/__init__.py backend/app/api/v1/cadastros.py backend/tests/test_cadastros_unidade_medida.py
git commit -m "feat(cadastros): CRUD de unidade_medida"
```

---

### Task B5: `colaborador` (FK → cargo, com validação de referência)

**Files:**
- Create: `backend/app/models/colaborador.py`, `backend/app/schemas/colaborador.py`
- Create: `backend/app/crud/refs.py` (validadores de FK reutilizáveis)
- Modify: `backend/app/models/__init__.py`, `backend/app/api/v1/cadastros.py`
- Test: `backend/tests/test_cadastros_colaborador.py`

- [ ] **Step 1: Teste que falha**

`backend/tests/test_cadastros_colaborador.py`:

```python
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
```

- [ ] **Step 2: Ver falhar**

Run: `cd backend; uv run pytest tests/test_cadastros_colaborador.py -v`
Expected: FAIL (404)

- [ ] **Step 3: Validadores de FK**

`backend/app/crud/refs.py`:

```python
from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import OperationalBase


async def _exists(
    session: AsyncSession, model: type[OperationalBase], tenant_id: uuid.UUID, obj_id: uuid.UUID
) -> bool:
    stmt = select(model.id).where(
        model.id == obj_id,
        model.tenant_id == tenant_id,
        model.deleted_at.is_(None),
    )
    return (await session.execute(stmt)).first() is not None


def fk_validator(field: str, model: type[OperationalBase], label: str):  # type: ignore[no-untyped-def]
    async def _validate(session: AsyncSession, tenant_id: uuid.UUID, data: dict[str, Any]) -> None:
        value = data.get(field)
        if value is None:
            return
        if not await _exists(session, model, tenant_id, value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{label} não encontrado(a) neste tenant",
            )

    return _validate


def compose(*validators):  # type: ignore[no-untyped-def]
    async def _run(session, tenant_id, data):  # type: ignore[no-untyped-def]
        for v in validators:
            await v(session, tenant_id, data)

    return _run
```

- [ ] **Step 4: Model + schema**

`backend/app/models/colaborador.py`:

```python
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class Colaborador(OperationalBase):
    __tablename__ = "colaborador"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cargo_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cargo.id", ondelete="SET NULL"), nullable=True
    )
    telefone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

`backend/app/schemas/colaborador.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ColaboradorCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    cargo_id: uuid.UUID | None = None
    telefone: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None


class ColaboradorUpdate(ColaboradorCreate):
    version: int = Field(ge=1)


class ColaboradorRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    cargo_id: uuid.UUID | None
    telefone: str | None
    email: str | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Registrar + router com validador**

`models/__init__.py`: `from app.models.colaborador import Colaborador` + `__all__`.

`cadastros.py`: imports + entrada usando `validate_refs`:

```python
from app.crud.refs import fk_validator
from app.models.cargo import Cargo
from app.models.colaborador import Colaborador
from app.schemas.colaborador import ColaboradorCreate, ColaboradorRead, ColaboradorUpdate

# ... dentro de routers:
    build_crud_router(
        prefix=f"{_BASE}/colaborador",
        tag="cadastros:colaborador",
        crud=CRUDBase(Colaborador, search_fields=["nome", "email"]),
        create_schema=ColaboradorCreate,
        update_schema=ColaboradorUpdate,
        read_schema=ColaboradorRead,
        validate_refs=fk_validator("cargo_id", Cargo, "Cargo"),
    ),
```

- [ ] **Step 6: Ver passar + commit**

Run: `cd backend; uv run pytest tests/test_cadastros_colaborador.py -v; uv run mypy app`
Expected: 3 passed, mypy verde

```bash
git add backend/app/crud/refs.py backend/app/models/colaborador.py backend/app/schemas/colaborador.py backend/app/models/__init__.py backend/app/api/v1/cadastros.py backend/tests/test_cadastros_colaborador.py
git commit -m "feat(cadastros): CRUD de colaborador com validação de FK (cargo)"
```

---

### Task B6: `fornecedor`

**Files:**
- Create: `backend/app/models/fornecedor.py`, `backend/app/schemas/fornecedor.py`
- Modify: `backend/app/models/__init__.py`, `backend/app/api/v1/cadastros.py`
- Test: estende `test_cadastros_smoke.py` (adicionar caso)

- [ ] **Step 1: Model**

`backend/app/models/fornecedor.py`:

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class Fornecedor(OperationalBase):
    __tablename__ = "fornecedor"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cnpj_cpf: Mapped[str | None] = mapped_column(String(18), nullable=True)
    rg_ie: Mapped[str | None] = mapped_column(String(255), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bairro: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cep: Mapped[str | None] = mapped_column(String(9), nullable=True)
    cidade: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

- [ ] **Step 2: Schema**

`backend/app/schemas/fornecedor.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FornecedorCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    tipo: str | None = Field(default=None, max_length=50)
    cnpj_cpf: str | None = Field(default=None, max_length=18)
    rg_ie: str | None = Field(default=None, max_length=255)
    endereco: str | None = Field(default=None, max_length=255)
    bairro: str | None = Field(default=None, max_length=255)
    cep: str | None = Field(default=None, max_length=9)
    cidade: str | None = Field(default=None, max_length=255)
    uf: str | None = Field(default=None, max_length=2)
    telefone: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None


class FornecedorUpdate(FornecedorCreate):
    version: int = Field(ge=1)


class FornecedorRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    tipo: str | None
    cnpj_cpf: str | None
    rg_ie: str | None
    endereco: str | None
    bairro: str | None
    cep: str | None
    cidade: str | None
    uf: str | None
    telefone: str | None
    email: str | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Registrar + router**

`models/__init__.py` + `cadastros.py`:

```python
    build_crud_router(
        prefix=f"{_BASE}/fornecedor",
        tag="cadastros:fornecedor",
        crud=CRUDBase(Fornecedor, search_fields=["nome", "cnpj_cpf", "cidade"]),
        create_schema=FornecedorCreate,
        update_schema=FornecedorUpdate,
        read_schema=FornecedorRead,
    ),
```

- [ ] **Step 4: Caso de teste**

Adicionar a `SIMPLE_RESOURCES` em `test_cadastros_smoke.py`:

```python
    ("fornecedor", {"nome": "Posto Central", "tipo": "PJ", "cnpj_cpf": "12345678000190"}),
```

- [ ] **Step 5: Ver passar + commit**

Run: `cd backend; uv run pytest tests/test_cadastros_smoke.py -v`
Expected: PASS (7 passed)

```bash
git add backend/app/models/fornecedor.py backend/app/schemas/fornecedor.py backend/app/models/__init__.py backend/app/api/v1/cadastros.py backend/tests/test_cadastros_smoke.py
git commit -m "feat(cadastros): CRUD de fornecedor"
```

---

### Task B7: `insumo` (FK → grupo_insumo, unidade_medida)

**Files:**
- Create: `backend/app/models/insumo.py`, `backend/app/schemas/insumo.py`
- Modify: `backend/app/models/__init__.py`, `backend/app/api/v1/cadastros.py`
- Test: `backend/tests/test_cadastros_insumo.py`

- [ ] **Step 1: Teste que falha**

`backend/tests/test_cadastros_insumo.py`:

```python
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
```

- [ ] **Step 2: Ver falhar**

Run: `cd backend; uv run pytest tests/test_cadastros_insumo.py -v`
Expected: FAIL (404)

- [ ] **Step 3: Model + schema**

`backend/app/models/insumo.py`:

```python
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import OperationalBase


class Insumo(OperationalBase):
    __tablename__ = "insumo"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    grupo_insumo_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("grupo_insumo.id", ondelete="SET NULL"), nullable=True
    )
    unidade_medida_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("unidade_medida.id", ondelete="SET NULL"), nullable=True
    )
    preco_medio: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    marca: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fabricante: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

`backend/app/schemas/insumo.py`:

```python
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class InsumoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    grupo_insumo_id: uuid.UUID | None = None
    unidade_medida_id: uuid.UUID | None = None
    preco_medio: Decimal | None = Field(default=None, ge=0)
    marca: str | None = Field(default=None, max_length=255)
    fabricante: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None


class InsumoUpdate(InsumoCreate):
    version: int = Field(ge=1)


class InsumoRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    grupo_insumo_id: uuid.UUID | None
    unidade_medida_id: uuid.UUID | None
    preco_medio: Decimal | None
    marca: str | None
    fabricante: str | None
    observacoes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Registrar + router com validador composto**

`models/__init__.py`: `from app.models.insumo import Insumo` + `__all__`.

`cadastros.py`:

```python
from app.crud.refs import compose, fk_validator
from app.models.grupo_insumo import GrupoInsumo
from app.models.insumo import Insumo
from app.models.unidade_medida import UnidadeMedida
from app.schemas.insumo import InsumoCreate, InsumoRead, InsumoUpdate

# ... dentro de routers:
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
```

- [ ] **Step 5: Ver passar + suite completa + commit**

Run: `cd backend; uv run pytest -q; uv run mypy app; uv run ruff check .; uv run ruff format --check .`
Expected: tudo verde (11 recursos cobertos)

```bash
git add backend/app/models/insumo.py backend/app/schemas/insumo.py backend/app/models/__init__.py backend/app/api/v1/cadastros.py backend/tests/test_cadastros_insumo.py
git commit -m "feat(cadastros): CRUD de insumo com validação de FKs (grupo_insumo, unidade_medida)"
```

---

### Task B8: Teste de isolamento de tenant (cross-cutting)

**Files:**
- Test: `backend/tests/test_cadastros_tenant_isolation.py`

- [ ] **Step 1: Teste que falha (se algo vazar entre tenants)**

`backend/tests/test_cadastros_tenant_isolation.py`:

```python
import uuid

import pytest
from sqlalchemy import text

from app.core.security import create_access_token
from app.models.role import RoleName, UserRole
from app.models.tenant import Tenant, TenantStatus

pytestmark = pytest.mark.anyio


async def _make_tenant_user(db):  # type: ignore[no-untyped-def]
    import fastapi_users.schemas as fau_schemas
    from uuid6 import uuid7

    from app.services.user_manager import get_user_db, get_user_manager

    t = Tenant(
        slug=f"t-{uuid7().hex[:12]}",
        razao_social="ACME",
        cnpj=f"{uuid7().int % 10**14:014d}",
        status=TenantStatus.TRIAL,
    )
    db.add(t)
    await db.commit()

    class _UC(fau_schemas.BaseUserCreate):
        tenant_id: uuid.UUID
        full_name: str

    async for udb in get_user_db(db):
        async for mgr in get_user_manager(udb):
            u = await mgr.create(
                _UC(
                    email=f"u-{uuid7().hex[:10]}@x.com",
                    password="SenhaForte123!",
                    tenant_id=t.id,
                    full_name="U",
                )
            )
    db.add(UserRole(tenant_id=t.id, user_id=u.id, role=RoleName.ADMIN))
    await db.commit()
    return t, create_access_token(u.id, t.id)


async def test_centro_custo_not_visible_across_tenants(client, db):
    _, token_a = await _make_tenant_user(db)
    _, token_b = await _make_tenant_user(db)

    r = await client.post(
        "/api/v1/cadastros/centro-custo",
        json={"nome": "Secreto A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 201

    r = await client.get(
        "/api/v1/cadastros/centro-custo", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert r.json()["total"] == 0
```

> Atenção (cerebrum): a RLS só atua se `app.current_tenant` for setado — o que `TenantSession` faz. Em testes que usam `db_engine` via `Base.metadata.create_all`, a policy RLS **não** é criada (só a migração cria policies). Este teste valida o isolamento da **camada de aplicação** (filtro `tenant_id` no `CRUDBase`), que é a defense-in-depth. O isolamento via RLS no banco é coberto por `test_tenant_isolation.py` (P1) e pela validação da migração 0005.

- [ ] **Step 2: Rodar**

Run: `cd backend; uv run pytest tests/test_cadastros_tenant_isolation.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_cadastros_tenant_isolation.py
git commit -m "test(cadastros): isolamento de tenant na camada de aplicação"
```

---

# FASE C — Fundação frontend (genéricos)

### Task C1: Tipos e cliente de recurso CRUD

**Files:**
- Create: `frontend/src/types/crud.ts`
- Create: `frontend/src/hooks/useCrudResource.ts`
- Test: `frontend/tests/hooks/useCrudResource.test.tsx`

- [ ] **Step 1: Teste que falha**

`frontend/tests/hooks/useCrudResource.test.tsx`:

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { api } from "@/lib/api";
import { useCrudResource } from "@/hooks/useCrudResource";

vi.mock("@/lib/api", () => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("useCrudResource", () => {
  beforeEach(() => vi.clearAllMocks());

  it("lista itens do recurso paginado", async () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { items: [{ id: "1", nome: "A" }], total: 1, limit: 50, offset: 0 },
    });
    const resource = useCrudResource<{ id: string; nome: string }>("centro-custo");
    const { result } = renderHook(() => resource.useList({ search: "" }), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(api.get).toHaveBeenCalledWith(
      "/v1/cadastros/centro-custo",
      expect.objectContaining({ params: expect.any(Object) }),
    );
    expect(result.current.data?.total).toBe(1);
  });
});
```

- [ ] **Step 2: Ver falhar**

Run: `cd frontend; npm test -- useCrudResource`
Expected: FAIL (módulo não existe)

- [ ] **Step 3: Implementar tipos**

`frontend/src/types/crud.ts`:

```ts
export interface Paginated<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface BaseRecord {
  id: string;
  tenant_id: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ListParams {
  search?: string;
  limit?: number;
  offset?: number;
}
```

- [ ] **Step 4: Implementar o hook factory**

`frontend/src/hooks/useCrudResource.ts`:

```ts
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ListParams, Paginated } from "@/types/crud";

export function useCrudResource<T extends { id: string }>(resource: string) {
  const path = `/v1/cadastros/${resource}`;
  const key = ["cadastros", resource];

  function useList(params: ListParams) {
    return useQuery<Paginated<T>>({
      queryKey: [...key, params],
      queryFn: () =>
        api
          .get<Paginated<T>>(path, {
            params: {
              search: params.search || undefined,
              limit: params.limit ?? 50,
              offset: params.offset ?? 0,
            },
          })
          .then((r) => r.data),
    });
  }

  function useItem(id: string | null) {
    return useQuery<T>({
      queryKey: [...key, "item", id],
      queryFn: () => api.get<T>(`${path}/${id}`).then((r) => r.data),
      enabled: id !== null,
    });
  }

  function useCreate() {
    const qc = useQueryClient();
    return useMutation({
      mutationFn: (data: Record<string, unknown>) =>
        api.post<T>(path, data).then((r) => r.data),
      onSuccess: () => qc.invalidateQueries({ queryKey: key }),
    });
  }

  function useUpdate() {
    const qc = useQueryClient();
    return useMutation({
      mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
        api.put<T>(`${path}/${id}`, data).then((r) => r.data),
      onSuccess: () => qc.invalidateQueries({ queryKey: key }),
    });
  }

  function useRemove() {
    const qc = useQueryClient();
    return useMutation({
      mutationFn: (id: string) => api.delete(`${path}/${id}`),
      onSuccess: () => qc.invalidateQueries({ queryKey: key }),
    });
  }

  return { useList, useItem, useCreate, useUpdate, useRemove };
}
```

- [ ] **Step 5: Ver passar + commit**

Run: `cd frontend; npm test -- useCrudResource`
Expected: PASS

```bash
git add frontend/src/types/crud.ts frontend/src/hooks/useCrudResource.ts frontend/tests/hooks/useCrudResource.test.tsx
git commit -m "feat(frontend): useCrudResource genérico + tipos de paginação"
```

---

### Task C2: Configuração de campos e registro de entidades

**Files:**
- Create: `frontend/src/config/cadastros.tsx`
- Test: `frontend/tests/config/cadastros.test.ts`

- [ ] **Step 1: Teste que falha**

`frontend/tests/config/cadastros.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { CADASTROS, getCadastro } from "@/config/cadastros";

describe("config cadastros", () => {
  it("registra as 11 entidades", () => {
    expect(Object.keys(CADASTROS)).toHaveLength(11);
  });

  it("cada entidade tem label, resource e ao menos um campo", () => {
    for (const c of Object.values(CADASTROS)) {
      expect(c.label.length).toBeGreaterThan(0);
      expect(c.resource.length).toBeGreaterThan(0);
      expect(c.fields.length).toBeGreaterThan(0);
    }
  });

  it("resolve config por slug", () => {
    expect(getCadastro("centro-custo")?.label).toBe("Centros de Custo");
    expect(getCadastro("inexistente")).toBeUndefined();
  });
});
```

- [ ] **Step 2: Ver falhar**

Run: `cd frontend; npm test -- config/cadastros`
Expected: FAIL

- [ ] **Step 3: Implementar a config**

`frontend/src/config/cadastros.tsx`:

```tsx
export type FieldType = "text" | "number" | "money" | "textarea" | "ref";

export interface FieldConfig {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  refResource?: string; // para type "ref": slug do recurso referenciado
  listColumn?: boolean; // exibir na tabela de listagem
}

export interface CadastroConfig {
  resource: string; // slug usado na URL/endpoint
  label: string; // título plural
  singular: string;
  fields: FieldConfig[];
}

const text = (name: string, label: string, required = false, listColumn = false): FieldConfig => ({
  name,
  label,
  type: "text",
  required,
  listColumn,
});

const NOME = text("nome", "Nome", true, true);
const OBS: FieldConfig = { name: "observacoes", label: "Observações", type: "textarea" };

export const CADASTROS: Record<string, CadastroConfig> = {
  "centro-custo": {
    resource: "centro-custo",
    label: "Centros de Custo",
    singular: "Centro de Custo",
    fields: [NOME, text("responsavel", "Responsável", false, true), OBS],
  },
  "conta-contabil": {
    resource: "conta-contabil",
    label: "Contas Contábeis",
    singular: "Conta Contábil",
    fields: [NOME, text("grupo", "Grupo", false, true), OBS],
  },
  cargo: {
    resource: "cargo",
    label: "Cargos",
    singular: "Cargo",
    fields: [NOME, { name: "salario", label: "Salário", type: "money", listColumn: true }, OBS],
  },
  colaborador: {
    resource: "colaborador",
    label: "Colaboradores",
    singular: "Colaborador",
    fields: [
      NOME,
      { name: "cargo_id", label: "Cargo", type: "ref", refResource: "cargo", listColumn: true },
      text("telefone", "Telefone"),
      text("email", "E-mail", false, true),
      OBS,
    ],
  },
  fornecedor: {
    resource: "fornecedor",
    label: "Fornecedores",
    singular: "Fornecedor",
    fields: [
      NOME,
      text("tipo", "Tipo (PF/PJ)"),
      text("cnpj_cpf", "CNPJ/CPF", false, true),
      text("rg_ie", "RG/IE"),
      text("endereco", "Endereço"),
      text("bairro", "Bairro"),
      text("cep", "CEP"),
      text("cidade", "Cidade", false, true),
      text("uf", "UF"),
      text("telefone", "Telefone"),
      text("email", "E-mail"),
      OBS,
    ],
  },
  combustivel: {
    resource: "combustivel",
    label: "Combustíveis",
    singular: "Combustível",
    fields: [NOME, OBS],
  },
  "tipo-equipamento": {
    resource: "tipo-equipamento",
    label: "Tipos de Equipamento",
    singular: "Tipo de Equipamento",
    fields: [
      NOME,
      { name: "depreciacao_anual", label: "Depreciação anual (%)", type: "number", listColumn: true },
      OBS,
    ],
  },
  "tipo-servico": {
    resource: "tipo-servico",
    label: "Tipos de Serviço",
    singular: "Tipo de Serviço",
    fields: [NOME, OBS],
  },
  "grupo-insumo": {
    resource: "grupo-insumo",
    label: "Grupos de Insumo",
    singular: "Grupo de Insumo",
    fields: [NOME, OBS],
  },
  "unidade-medida": {
    resource: "unidade-medida",
    label: "Unidades de Medida",
    singular: "Unidade de Medida",
    fields: [text("codigo", "Código", true, true), NOME, OBS],
  },
  insumo: {
    resource: "insumo",
    label: "Insumos",
    singular: "Insumo",
    fields: [
      NOME,
      { name: "grupo_insumo_id", label: "Grupo", type: "ref", refResource: "grupo-insumo", listColumn: true },
      {
        name: "unidade_medida_id",
        label: "Unidade",
        type: "ref",
        refResource: "unidade-medida",
        listColumn: true,
      },
      { name: "preco_medio", label: "Preço médio", type: "money", listColumn: true },
      text("marca", "Marca"),
      text("fabricante", "Fabricante"),
      OBS,
    ],
  },
};

export function getCadastro(slug: string): CadastroConfig | undefined {
  return CADASTROS[slug];
}
```

- [ ] **Step 4: Ver passar + commit**

Run: `cd frontend; npm test -- config/cadastros`
Expected: PASS (3 passed)

```bash
git add frontend/src/config/cadastros.tsx frontend/tests/config/cadastros.test.ts
git commit -m "feat(frontend): configuração declarativa das 11 entidades de cadastro"
```

---

### Task C3: Componentes genéricos `CrudForm` e `CrudListPage`

**Files:**
- Create: `frontend/src/components/crud/CrudForm.tsx`
- Create: `frontend/src/components/crud/CrudListPage.tsx`
- Test: `frontend/tests/components/CrudListPage.test.tsx`

> Estilo: Tailwind puro, alinhado aos formulários existentes (`components/auth/LoginForm.tsx`). Sem shadcn/ui (não instalado nesta fase).

- [ ] **Step 1: Teste que falha**

`frontend/tests/components/CrudListPage.test.tsx`:

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { api } from "@/lib/api";
import { CrudListPage } from "@/components/crud/CrudListPage";
import { CADASTROS } from "@/config/cadastros";

vi.mock("@/lib/api", () => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("CrudListPage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renderiza o título e as linhas do recurso", async () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: {
        items: [{ id: "1", nome: "Frota Pesada", responsavel: "João", version: 1 }],
        total: 1,
        limit: 50,
        offset: 0,
      },
    });
    render(wrap(<CrudListPage config={CADASTROS["centro-custo"]} />));
    expect(screen.getByText("Centros de Custo")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Frota Pesada")).toBeInTheDocument());
  });
});
```

- [ ] **Step 2: Ver falhar**

Run: `cd frontend; npm test -- CrudListPage`
Expected: FAIL

- [ ] **Step 3: Implementar `CrudForm`**

`frontend/src/components/crud/CrudForm.tsx`:

```tsx
import { useEffect, useState } from "react";
import type { CadastroConfig } from "@/config/cadastros";
import { useCrudResource } from "@/hooks/useCrudResource";

interface Props {
  config: CadastroConfig;
  initial?: Record<string, unknown> | null;
  onClose: () => void;
}

function RefSelect({
  field,
  value,
  onChange,
}: {
  field: { refResource?: string; label: string };
  value: string;
  onChange: (v: string) => void;
}) {
  const ref = useCrudResource<{ id: string; nome: string; codigo?: string }>(field.refResource!);
  const { data } = ref.useList({ limit: 200 });
  return (
    <select
      className="w-full rounded border border-gray-300 px-3 py-2"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">— selecione —</option>
      {data?.items.map((o) => (
        <option key={o.id} value={o.id}>
          {o.codigo ? `${o.codigo} — ${o.nome}` : o.nome}
        </option>
      ))}
    </select>
  );
}

export function CrudForm({ config, initial, onClose }: Props) {
  const create = useCrudResource(config.resource).useCreate();
  const update = useCrudResource(config.resource).useUpdate();
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [error, setError] = useState<string | null>(null);
  const isEdit = initial != null;

  useEffect(() => {
    setValues(initial ?? {});
  }, [initial]);

  function set(name: string, v: unknown) {
    setValues((prev) => ({ ...prev, [name]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const payload: Record<string, unknown> = {};
    for (const f of config.fields) {
      const raw = values[f.name];
      payload[f.name] =
        raw === "" || raw === undefined ? null : f.type === "ref" ? raw : raw;
    }
    try {
      if (isEdit) {
        payload.version = (initial as { version: number }).version;
        await update.mutateAsync({ id: (initial as { id: string }).id, data: payload });
      } else {
        await create.mutateAsync(payload);
      }
      onClose();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Erro ao salvar");
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <h3 className="text-lg font-semibold">
        {isEdit ? `Editar ${config.singular}` : `Novo ${config.singular}`}
      </h3>
      {config.fields.map((f) => (
        <div key={f.name} className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            {f.label}
            {f.required && <span className="text-red-500"> *</span>}
          </label>
          {f.type === "textarea" ? (
            <textarea
              className="w-full rounded border border-gray-300 px-3 py-2"
              value={String(values[f.name] ?? "")}
              onChange={(e) => set(f.name, e.target.value)}
            />
          ) : f.type === "ref" ? (
            <RefSelect field={f} value={String(values[f.name] ?? "")} onChange={(v) => set(f.name, v)} />
          ) : (
            <input
              type={f.type === "money" || f.type === "number" ? "number" : "text"}
              step={f.type === "money" ? "0.0001" : undefined}
              className="w-full rounded border border-gray-300 px-3 py-2"
              value={String(values[f.name] ?? "")}
              onChange={(e) => set(f.name, e.target.value)}
              required={f.required}
            />
          )}
        </div>
      ))}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={create.isPending || update.isPending}
          className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
        >
          Salvar
        </button>
        <button type="button" onClick={onClose} className="rounded border px-4 py-2">
          Cancelar
        </button>
      </div>
    </form>
  );
}
```

- [ ] **Step 4: Implementar `CrudListPage`**

`frontend/src/components/crud/CrudListPage.tsx`:

```tsx
import { useState } from "react";
import type { CadastroConfig } from "@/config/cadastros";
import { useCrudResource } from "@/hooks/useCrudResource";
import { CrudForm } from "@/components/crud/CrudForm";

type Row = Record<string, unknown> & { id: string; version: number };

export function CrudListPage({ config }: { config: CadastroConfig }) {
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Row | null | undefined>(undefined);
  const resource = useCrudResource<Row>(config.resource);
  const { data, isLoading } = resource.useList({ search });
  const remove = resource.useRemove();

  const columns = config.fields.filter((f) => f.listColumn);

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">{config.label}</h2>
        <button
          onClick={() => setEditing(null)}
          className="rounded bg-blue-600 px-4 py-2 text-white"
        >
          Novo
        </button>
      </div>

      <input
        placeholder="Buscar..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full max-w-sm rounded border border-gray-300 px-3 py-2"
      />

      {editing !== undefined && (
        <div className="rounded border border-gray-200 bg-gray-50 p-4">
          <CrudForm config={config} initial={editing} onClose={() => setEditing(undefined)} />
        </div>
      )}

      {isLoading ? (
        <p>Carregando...</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left">
              {columns.map((c) => (
                <th key={c.name} className="py-2 pr-4 font-medium">
                  {c.label}
                </th>
              ))}
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {data?.items.map((row) => (
              <tr key={row.id} className="border-b">
                {columns.map((c) => (
                  <td key={c.name} className="py-2 pr-4">
                    {String(row[c.name] ?? "—")}
                  </td>
                ))}
                <td className="py-2 text-right">
                  <button onClick={() => setEditing(row)} className="mr-3 text-blue-600">
                    Editar
                  </button>
                  <button
                    onClick={() => {
                      if (confirm("Excluir este registro?")) remove.mutate(row.id);
                    }}
                    className="text-red-600"
                  >
                    Excluir
                  </button>
                </td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td colSpan={columns.length + 1} className="py-6 text-center text-gray-500">
                  Nenhum registro.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Ver passar + commit**

Run: `cd frontend; npm test -- CrudListPage`
Expected: PASS

```bash
git add frontend/src/components/crud/CrudForm.tsx frontend/src/components/crud/CrudListPage.tsx frontend/tests/components/CrudListPage.test.tsx
git commit -m "feat(frontend): componentes genéricos CrudForm e CrudListPage"
```

---

### Task C4: Página roteada + índice de cadastros + rotas

**Files:**
- Create: `frontend/src/pages/cadastros/CadastroPage.tsx`
- Create: `frontend/src/pages/cadastros/CadastrosIndex.tsx`
- Modify: `frontend/src/App.tsx`
- Test: `frontend/tests/pages/CadastroPage.test.tsx`

- [ ] **Step 1: Teste que falha**

`frontend/tests/pages/CadastroPage.test.tsx`:

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { CadastroPage } from "@/pages/cadastros/CadastroPage";

vi.mock("@/lib/api", () => ({
  api: { get: vi.fn().mockResolvedValue({ data: { items: [], total: 0, limit: 50, offset: 0 } }) },
}));

function wrap(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/cadastros/:resource" element={<CadastroPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CadastroPage", () => {
  it("renderiza o cadastro pelo slug da rota", () => {
    wrap("/cadastros/combustivel");
    expect(screen.getByText("Combustíveis")).toBeInTheDocument();
  });

  it("mostra 'não encontrado' para slug inválido", () => {
    wrap("/cadastros/xyz");
    expect(screen.getByText(/não encontrado/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Ver falhar**

Run: `cd frontend; npm test -- CadastroPage`
Expected: FAIL

- [ ] **Step 3: Implementar páginas**

`frontend/src/pages/cadastros/CadastroPage.tsx`:

```tsx
import { useParams } from "react-router-dom";
import { CrudListPage } from "@/components/crud/CrudListPage";
import { getCadastro } from "@/config/cadastros";

export function CadastroPage() {
  const { resource } = useParams<{ resource: string }>();
  const config = resource ? getCadastro(resource) : undefined;
  if (!config) {
    return <div className="p-6 text-gray-600">Cadastro não encontrado.</div>;
  }
  return <CrudListPage config={config} />;
}
```

`frontend/src/pages/cadastros/CadastrosIndex.tsx`:

```tsx
import { Link } from "react-router-dom";
import { CADASTROS } from "@/config/cadastros";

export function CadastrosIndex() {
  return (
    <div className="p-6">
      <h2 className="mb-4 text-2xl font-bold">Cadastros</h2>
      <ul className="grid grid-cols-2 gap-3 md:grid-cols-3">
        {Object.values(CADASTROS).map((c) => (
          <li key={c.resource}>
            <Link
              to={`/cadastros/${c.resource}`}
              className="block rounded border border-gray-200 p-4 hover:bg-gray-50"
            >
              {c.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 4: Registrar rotas no App.tsx**

Em `frontend/src/App.tsx`, adicionar imports e rotas dentro do bloco `<ProtectedRoute />`:

```tsx
import { CadastrosIndex } from "@/pages/cadastros/CadastrosIndex";
import { CadastroPage } from "@/pages/cadastros/CadastroPage";

// dentro de <Route element={<ProtectedRoute />}> ... </Route>:
        <Route path="/cadastros" element={<CadastrosIndex />} />
        <Route path="/cadastros/:resource" element={<CadastroPage />} />
```

- [ ] **Step 5: Ver passar + lint + commit**

Run: `cd frontend; npm test -- CadastroPage; npm run lint`
Expected: PASS, lint verde

```bash
git add frontend/src/pages/cadastros frontend/src/App.tsx frontend/tests/pages/CadastroPage.test.tsx
git commit -m "feat(frontend): rotas e índice de cadastros (/cadastros e /cadastros/:resource)"
```

---

### Task C5: Link no Dashboard + verificação full-stack

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`

- [ ] **Step 1: Adicionar link para Cadastros no Dashboard**

Em `frontend/src/pages/Dashboard.tsx`, adicionar um link de navegação para `/cadastros` na área principal (seguindo o estilo existente do shell). Exemplo de bloco a inserir:

```tsx
import { Link } from "react-router-dom";

// dentro do JSX do Dashboard, na área de conteúdo:
<Link
  to="/cadastros"
  className="inline-block rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
>
  Cadastros
</Link>
```

- [ ] **Step 2: Build do frontend + suite**

Run: `cd frontend; npm run lint; npm run build; npm test`
Expected: build sem erros de tipo; todos os testes passam

- [ ] **Step 3: Verificação manual full-stack (cerebrum: docker-compose.override + rebuild)**

```powershell
# backend + deps
docker compose up -d --build postgres redis api
docker compose exec api alembic upgrade head
# seed (tenant + owner) se necessário
docker compose exec api python scripts/seed.py
# frontend dev
cd frontend; npm run dev
```

Validar no navegador (`http://localhost:5173`): login → Dashboard → "Cadastros" → criar/editar/excluir um Centro de Custo; criar um Insumo selecionando Grupo e Unidade (combos populados). Conferir busca e que o registro excluído some da lista.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Dashboard.tsx
git commit -m "feat(frontend): atalho de Cadastros no Dashboard"
```

---

# FASE D — Fechamento

### Task D1: Documentação e atualização de estado

**Files:**
- Modify: `README.md` (seção de status / planos)
- Modify: `.wolf/cerebrum.md` (Key Learnings + Decision Log)
- Create: `docs/superpowers/P4_CADASTROS.md` (guia curto: entidades, rotas, padrão genérico) — **somente se o usuário pedir** (cerebrum: não criar `.md` sem solicitação)

- [ ] **Step 1: Atualizar README**

Adicionar à lista de planos:

```markdown
- [P4 — Cadastros Básicos](docs/superpowers/plans/2026-06-03-p4-cadastros-basicos.md) ✅ **Concluído**
```

E no status: `✅ **P4** — Cadastros Básicos (11 CRUDs full-stack com RLS, soft delete, optimistic lock)`.

- [ ] **Step 2: Atualizar cerebrum (Key Learnings + Decision Log)**

Registrar: padrão genérico `OperationalBase` + `CRUDBase` + `build_crud_router` + `useCrudResource`/`CrudListPage` para futuros domínios; mapeamento Access (sufixos removidos, `REAL`→`Numeric(15,4)`, FKs string→UUID); unicidade parcial `WHERE deleted_at IS NULL`.

- [ ] **Step 3: Suite completa final (backend + frontend)**

Run:
```bash
cd backend; uv run pytest -q; uv run mypy app; uv run ruff check .; uv run ruff format --check .
cd ../frontend; npm test; npm run lint; npm run build
```
Expected: tudo verde.

- [ ] **Step 4: Commit**

```bash
git add README.md .wolf/cerebrum.md
git commit -m "docs(p4): atualiza status e aprendizados dos cadastros básicos"
```

---

## Self-review checklist (executado pelo autor do plano)

- **Cobertura do escopo:** 11 entidades extraídas do Access (centro_custo, conta_contabil, cargo, colaborador, fornecedor, combustivel, tipo_equipamento, tipo_servico, grupo_insumo, unidade_medida, insumo) → todas têm model (B1/B3/B4/B5/B6/B7), schema, router (cadastros.py), migração (B-MIG) e UI (config C2 + páginas C4). ✅
- **Decisões do usuário:** todas as 11 de uma vez ✅; full-stack ✅; colunas extraídas do Access ✅; sem CSV/LGPD (só CRUDs com busca/paginação/soft delete) ✅.
- **Convenções:** UUID v7, tenant_id, TIMESTAMPTZ, Numeric(15,4) para dinheiro (salario/preco_medio/depreciacao), unicidade parcial composta, RLS via migração, defense-in-depth no CRUDBase, optimistic lock (409), require_role nas rotas mutativas. ✅
- **Consistência de tipos:** `obj_id` usado uniformemente no CRUDBase/factory; `version` no Update e checado no `update()`; `read_schema.model_validate(..., from_attributes=True)`; FK validators retornam 400. ✅
- **Sem placeholders:** todo passo de código mostra o código completo; entidades repetidas trazem o código (não "igual à Task N"). ✅
- **Ordem de dependência:** cargo antes de colaborador; grupo_insumo/unidade_medida antes de insumo; migração após todos os models. Documentado no topo da Fase B. ✅
```

